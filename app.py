import streamlit as st
import pandas as pd

# Load data

def load_data():
    matches_df = pd.read_csv("ipl_data/matches.csv")
    players_df = pd.read_csv("ipl_data/team_players_matches.csv")
    deliveries_df = pd.read_csv("ipl_data/deliveries_2025.csv")
    matchup_df = pd.read_csv("ipl_data/deliveries.csv")
    return matches_df, players_df, deliveries_df, matchup_df

matches_df, players_df, deliveries_df, matchup_df = load_data()

st.set_page_config(layout="wide")
st.title("Team Head-to-Head Stats Viewer")

teams = sorted(players_df['team'].dropna().unique())

# Layout for team selection using radio buttons
col1, col2 = st.columns(2)

with col1:
    team1 = st.radio("Select Team 1", teams, key="team1")
with col2:
    team2 = st.radio("Select Team 2", [team for team in teams if team != team1], key="team2")

if team1 and team2:
    h2h_matches = matches_df[((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) |
                              ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))]

    wins_team1 = h2h_matches[h2h_matches['winner'] == team1].shape[0]
    wins_team2 = h2h_matches[h2h_matches['winner'] == team2].shape[0]

    st.markdown("---")
    col1, col2 = st.columns(2)

    def get_player_stats(team_name):
        team_players = players_df[players_df['team'] == team_name]['player'].unique()
        stats = []
        for player in team_players:
            batting_df = deliveries_df[deliveries_df['batter'] == player]
            bowling_df = deliveries_df[deliveries_df['bowler'] == player]
            
            matches_played = pd.concat([batting_df['match_id'], bowling_df['match_id']]).nunique()
            runs_scored = batting_df['batsman_runs'].sum()
            balls_faced = batting_df.shape[0]

            overs_bowled = round(bowling_df[['match_id', 'over', 'ball']].drop_duplicates().shape[0] / 6, 1)
            wickets = bowling_df['is_wicket'].sum()
            runs_given = bowling_df['total_runs'].sum()

            stats.append({
                "Player": player,
                "Matches": matches_played,
                "Runs Scored": runs_scored,
                "Balls Faced": balls_faced,
                "Overs Bowled": overs_bowled,
                "Wickets Taken": wickets,
                "Runs Given": runs_given
            })

        return pd.DataFrame(stats).sort_values(by="Player")

    with col1:
        st.subheader(team1)
        st.markdown(
            f"""
            <div style='background-color:#f0f2f6;padding:20px;border-radius:15px;text-align:center;'>
                <h3>Wins</h3>
                <h1 style='color:#2E86C1;'>{wins_team1}</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("### Current Players Stats")
        team1_stats = get_player_stats(team1)
        st.dataframe(team1_stats, use_container_width=True)

    with col2:
        st.subheader(team2)
        st.markdown(
            f"""
            <div style='background-color:#f0f2f6;padding:20px;border-radius:15px;text-align:center;'>
                <h3>Wins</h3>
                <h1 style='color:#28B463;'>{wins_team2}</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("### Current Players Stats")
        team2_stats = get_player_stats(team2)
        st.dataframe(team2_stats, use_container_width=True)

    st.markdown("---")
    st.subheader("Match History Between Teams")
    match_details = h2h_matches[["season", "date", "city", "team1", "team2", "toss_winner", "toss_decision", "winner", "result", "result_margin", "target_runs"]]
    match_details = match_details.sort_values(by="date", ascending=False).reset_index(drop=True)
    st.dataframe(match_details, use_container_width=True)

    # Matchup Analysis from matchup_df
    st.markdown("---")
    st.subheader("Key Player Matchups Between Teams")

    team1_players = players_df[players_df['team'] == team1]['player'].unique()
    team2_players = players_df[players_df['team'] == team2]['player'].unique()

    matchup_df['matchup_flag'] = ((matchup_df['bowler'].isin(team1_players)) & (matchup_df['batter'].isin(team2_players))) | \
                                 ((matchup_df['bowler'].isin(team2_players)) & (matchup_df['batter'].isin(team1_players)))

    df_matchup = matchup_df[matchup_df['matchup_flag']]

    matchup_stats = df_matchup.groupby(['bowler', 'batter']).agg(
        matches=('match_id', 'nunique'),
        balls=('ball', 'count'),
        runs=('total_runs', 'sum'),
        wickets=('is_wicket', 'sum')
    ).reset_index()

    matchup_stats['Strike Rate'] = (100 * matchup_stats['runs'] / matchup_stats['balls']).round(2)

    st.dataframe(matchup_stats.sort_values(by='balls', ascending=False), use_container_width=True)
