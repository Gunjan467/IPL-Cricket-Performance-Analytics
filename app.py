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
st.markdown("---") 
st.header("⚔️ Head-to-Head Matchup")

# Create two columns for the team selection dropdowns
col1, col2 = st.columns(2)
teams = sorted(match_df['team1'].dropna().unique())

with col1:
    # Safely handle default index just in case the team isn't in the list
    default_idx1 = teams.index('Chennai Super Kings') if 'Chennai Super Kings' in teams else 0
    team1 = st.selectbox("Select Team 1", teams, index=default_idx1)
    
with col2:
    default_idx2 = teams.index('Mumbai Indians') if 'Mumbai Indians' in teams else 1
    team2 = st.selectbox("Select Team 2", teams, index=default_idx2)

if team1 == team2:
    st.warning("⚠️ Please select two different teams!")
else:
    # Filter the data for only matches between these two teams
    mask = ((match_df['team1'] == team1) & (match_df['team2'] == team2)) | ((match_df['team1'] == team2) & (match_df['team2'] == team1))
    h2h_df = match_df[mask]
    
    st.write(f"**Total Matches Played between {team1} and {team2}:** {len(h2h_df)}")
    
    # Only draw the chart if they have played against each other
    if len(h2h_df) > 0:
        # Count the wins for each team
        wins = h2h_df['winner'].value_counts().reset_index()
        wins.columns = ['Team', 'Wins']
        
        # Create a Plotly Bar Chart
        fig2 = px.bar(wins, x='Team', y='Wins', color='Team', 
                      title=f"Historic Win Record: {team1} vs {team2}",
                      text='Wins')
        
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("These two teams have never played against each other in the dataset.")