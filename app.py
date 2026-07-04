import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="IPL Analytics Dashboard", layout="wide")
st.title("🏏 IPL Cricket Performance Analytics")
st.write("Welcome to the interactive IPL match analysis dashboard.")

@st.cache_data
def load_and_clean_data():
    df = pd.read_csv('data/data.csv')
    
    match_df = df.drop_duplicates(subset=['match_id']).copy()
    
    team_mapping = {
        'Delhi Daredevils': 'Delhi Capitals',
        'Kings XI Punjab': 'Punjab Kings',
        'Deccan Chargers': 'Sunrisers Hyderabad',
        'Royal Challengers Bangalore': 'Royal Challengers Bengaluru'
    }
    match_df['team1'] = match_df['team1'].replace(team_mapping)
    match_df['team2'] = match_df['team2'].replace(team_mapping)
    
    return match_df

match_df = load_and_clean_data()

st.header("🏟️ Venue Analysis")

stadiums = sorted(match_df['venue'].dropna().unique())
selected_venue = st.selectbox("Select a Stadium to Analyze", stadiums, index=stadiums.index('Wankhede Stadium'))

venue_df = match_df[match_df['venue'] == selected_venue]
st.write(f"**Total Matches Played at {selected_venue}:** {len(venue_df)}")

batting_first_wins = len(venue_df[venue_df['result'] == 'runs'])
chasing_wins = len(venue_df[venue_df['result'] == 'wickets'])

if len(venue_df) > 0:
    chart_data = pd.DataFrame({
        'Outcome': ['Batting First', 'Chasing'],
        'Wins': [batting_first_wins, chasing_wins]
    })
    
    fig = px.pie(chart_data, values='Wins', names='Outcome', 
                 color='Outcome',
                 color_discrete_map={'Batting First':'#1f77b4', 'Chasing':'#ff7f0e'})
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Not enough data to calculate win ratios for this venue.")