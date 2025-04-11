import streamlit as st
import pandas as pd

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("matches.csv")
    return df

df = load_data()

st.title("Team Head-to-Head Stats Viewer")

teams = sorted(set(df['team1'].dropna().unique()) | set(df['team2'].dropna().unique()))

# Team selection
team1 = st.selectbox("Select Team 1", teams)
team2 = st.selectbox("Select Team 2", [team for team in teams if team != team1])

if team1 and team2:
    h2h_matches = df[((df['team1'] == team1) & (df['team2'] == team2)) |
                     ((df['team1'] == team2) & (df['team2'] == team1))]

    total_matches = h2h_matches.shape[0]
    wins_team1 = h2h_matches[h2h_matches['winner'] == team1].shape[0]
    wins_team2 = h2h_matches[h2h_matches['winner'] == team2].shape[0]
    
    st.subheader(f"Head-to-Head: {team1} vs {team2}")
    st.write(f"**Total Matches:** {total_matches}")
    st.write(f"**{team1} Wins:** {wins_team1}")
    st.write(f"**{team2} Wins:** {wins_team2}")
