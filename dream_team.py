import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🏏 Dream11 Points Calculator – Matchwise Top 11")

uploaded_file = st.file_uploader("Upload Deliveries CSV", type="csv")

# ----------------------------- #
# 🔁 Dream11 Point Calculation
# ----------------------------- #
def calculate_dream11_points(df):
    batting = df.groupby(['match_id', 'batter']).agg(
        runs=('batsman_runs', 'sum'),
        fours=('batsman_runs', lambda x: (x == 4).sum()),
        sixes=('batsman_runs', lambda x: (x == 6).sum()),
        ducks=('batsman_runs', lambda x: (x.sum() == 0 and len(x) >= 1))
    ).reset_index()
    batting['batting_points'] = (
        batting['runs'] + batting['fours']*4 + batting['sixes'] * 6 +
        batting['ducks'].astype(int) * -2 +
        batting['runs'].apply(lambda x: 4 if x > 25 else 0) +
        batting['runs'].apply(lambda x: 4 if x > 50 else 0) +
        batting['runs'].apply(lambda x: 4 if x > 75 else 0) +
        batting['runs'].apply(lambda x: 4 if x > 100 else 0)
    )

    bowling_dots = df[df['total_runs'] == 0].groupby(['match_id', 'bowler']).size().reset_index(name='dot_balls')

    bowling = df.groupby(['match_id', 'bowler']).agg(
        wickets=('is_wicket', 'sum'),
        bowled_or_lbw=('dismissal_kind', lambda x: ((x == 'bowled') | (x == 'lbw')).sum())
    ).reset_index()

    bowling = pd.merge(bowling, bowling_dots, on=['match_id', 'bowler'], how='left')
    bowling['dot_balls'] = bowling['dot_balls'].fillna(0)

    bowling['bowling_points'] = (
        bowling['wickets'] * 25 +
        bowling['bowled_or_lbw'] * 8 +
        bowling['dot_balls'] * 1 +
        bowling['wickets'].apply(lambda x: 4 if x == 3 else 0) +
        bowling['wickets'].apply(lambda x: 8 if x == 4 else 0) +
        bowling['wickets'].apply(lambda x: 16 if x >= 5 else 0)
    )

    fielding = df[df['is_wicket'] == 1].dropna(subset=['fielder'])
    fielding_points = fielding.groupby(['match_id', 'fielder']).agg(
        catches=('dismissal_kind', lambda x: (x == 'caught').sum()),
        stumpings=('dismissal_kind', lambda x: (x == 'stumped').sum()),
        runouts=('dismissal_kind', lambda x: (x == 'run out').sum())
    ).reset_index()
    fielding_points['fielding_points'] = (
        fielding_points['catches'] * 8 +
        fielding_points['stumpings'] * 12 +
        fielding_points['runouts'] * 12 +
        fielding_points['catches'].apply(lambda x: 4 if x >= 3 else 0)
    )

    batting.rename(columns={'batter': 'player'}, inplace=True)
    bowling.rename(columns={'bowler': 'player'}, inplace=True)
    fielding_points.rename(columns={'fielder': 'player'}, inplace=True)

    points = pd.merge(batting[['match_id', 'player', 'batting_points']],
                      bowling[['match_id', 'player', 'bowling_points']],
                      on=['match_id', 'player'], how='outer')
    points = pd.merge(points,
                      fielding_points[['match_id', 'player', 'fielding_points']],
                      on=['match_id', 'player'], how='outer')
    points.fillna(0, inplace=True)
    points['total_points'] = points['batting_points'] + points['bowling_points'] + points['fielding_points'] + 4

    return points

# ---------------------- #
# 🧠 Helper: Get Team Map
# ---------------------- #
def get_team_mapping(df):
    batter_teams = df[['match_id', 'batter', 'batting_team']].rename(columns={'batter': 'player', 'batting_team': 'team'})
    bowler_teams = df[['match_id', 'bowler', 'bowling_team']].rename(columns={'bowler': 'player', 'bowling_team': 'team'})
    fielder_teams = df[['match_id', 'fielder', 'bowling_team']].rename(columns={'fielder': 'player', 'bowling_team': 'team'})
    return pd.concat([batter_teams, bowler_teams, fielder_teams]).dropna().drop_duplicates(subset=['match_id', 'player'])

# ---------------------- #
# 🚀 MAIN APP LOGIC
# ---------------------- #
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Use fixed file for team mapping
    team_df = pd.read_csv("ipl_data/deliveries_2025.csv")
    team_map = get_team_mapping(team_df)

    # Calculate points
    points = calculate_dream11_points(df)
    points = pd.merge(points, team_map, on=['match_id', 'player'], how='left')

    # Merge season info from matches.csv
    matches = pd.read_csv("ipl_data/matches.csv")
    season_map = matches[['id', 'season']].rename(columns={'id': 'match_id'})
    points = pd.merge(points, season_map, on='match_id', how='left')

    # Season filter
    available_seasons = sorted(points['season'].dropna().unique())
    selected_seasons = st.multiselect(
        "Filter by Season:",
        options=available_seasons,
        default=available_seasons
    )

    filtered_points = points[points['season'].isin(selected_seasons)]

    # ✅ Filter by selected team combinations
    match_teams = matches[['id', 'team1', 'team2']].rename(columns={'id': 'match_id'})
    filtered_points = filtered_points.merge(match_teams, on='match_id', how='left')

    all_teams = sorted(pd.unique(matches[['team1', 'team2']].values.ravel('K')))

    # Get all unique teams from matches
    all_teams = sorted(pd.unique(matches[['team1', 'team2']].values.ravel('K')))

    st.markdown("### Filter by Teams (Both team1 and team2 must be selected):")
    cols = st.columns(4)
    selected_teams = []

    for i, team in enumerate(all_teams):
        if cols[i % 4].checkbox(team, value=True):
            selected_teams.append(team)

    # Apply filter: match included only if both team1 and team2 are in selected_teams
    filtered_points = filtered_points[
        filtered_points['team1'].isin(selected_teams) & filtered_points['team2'].isin(selected_teams)
    ]

    # Top 11 players per match
    top_11 = (
        filtered_points.sort_values(['match_id', 'total_points'], ascending=[True, False])
        .groupby('match_id', group_keys=False)
        .head(11)
    )

    match_ids = top_11['match_id'].unique()
    col1, col2, col3 = st.columns(3)

    for i, match_id in enumerate(match_ids):
        match_df = top_11[top_11['match_id'] == match_id][
            ['player', 'team', 'batting_points', 'bowling_points', 'fielding_points', 'total_points']
        ].sort_values(by='total_points', ascending=False).reset_index(drop=True)

        summary = match_df[['batting_points', 'bowling_points', 'fielding_points', 'total_points']].sum()
        summary_str = (
            f"**Batting:** {summary['batting_points']:.0f} | "
            f"**Bowling:** {summary['bowling_points']:.0f} | "
            f"**Fielding:** {summary['fielding_points']:.0f} | "
            f"**Total:** {summary['total_points']:.0f}"
        )

        title = f"Match ID: {match_id}"
        if i % 3 == 0:
            with col1:
                with st.expander(title, expanded=True):
                    st.markdown(summary_str)
                    st.dataframe(match_df, use_container_width=True)
        elif i % 3 == 1:
            with col2:
                with st.expander(title, expanded=True):
                    st.markdown(summary_str)
                    st.dataframe(match_df, use_container_width=True)
        else:
            with col3:
                with st.expander(title, expanded=True):
                    st.markdown(summary_str)
                    st.dataframe(match_df, use_container_width=True)
