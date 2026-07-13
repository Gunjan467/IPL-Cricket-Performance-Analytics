import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pickle
import numpy as np

# --- 1. Setup the Web Page ---
st.set_page_config(page_title="IPL Analytics Dashboard", layout="wide")
st.title("🏏 IPL Cricket Performance Analytics")
st.write("Welcome to the interactive IPL match analysis dashboard.")

# --- High-Visibility Dashboard Theme Colors ---
THEME_COLORS = ['#38BDF8', '#818CF8', '#34D399', '#FBBF24'] 

# --- 2. Load and Clean Data ---
@st.cache_data
def load_and_clean_data():
    df = pd.read_csv('data/data.csv')
    
    # NEW: Load the ball-by-ball ML data for the progression chart
    try:
        ml_df = pd.read_csv('data/ml_data.csv')
    except FileNotFoundError:
        ml_df = pd.DataFrame() # Fallback if file isn't found
    
    match_df = df.drop_duplicates(subset=['match_id']).copy()
    
    # Standardize Team Names (Historically Accurate)
    team_mapping = {
        'Delhi Daredevils': 'Delhi Capitals',
        'Kings XI Punjab': 'Punjab Kings',
        'Deccan Chargers': 'Sunrisers Hyderabad',
        'Royal Challengers Bangalore': 'Royal Challengers Bengaluru',
        'Rising Pune Supergiant': 'Rising Pune Supergiants'
    }
    match_df['team1'] = match_df['team1'].replace(team_mapping)
    match_df['team2'] = match_df['team2'].replace(team_mapping)
    match_df['winner'] = match_df['winner'].replace(team_mapping)
    
    # Standardize ML data team names if it loaded successfully
    if not ml_df.empty:
        if 'batting_team' in ml_df.columns:
            ml_df['batting_team'] = ml_df['batting_team'].replace(team_mapping)
        if 'bowling_team' in ml_df.columns:
            ml_df['bowling_team'] = ml_df['bowling_team'].replace(team_mapping)
            
    return match_df, ml_df

match_df, ml_df = load_and_clean_data()
teams = sorted(match_df['team1'].dropna().unique())
stadiums = sorted(match_df['venue'].dropna().unique())

# --- 3. Build the Dashboard UI - Venue Analysis ---
st.header("🏟️ Venue Analysis")

selected_venue = st.selectbox("Select a Stadium to Analyze", stadiums, index=stadiums.index('Wankhede Stadium') if 'Wankhede Stadium' in stadiums else 0)

venue_df = match_df[match_df['venue'] == selected_venue]
st.write(f"**Total Matches Played at {selected_venue}:** {len(venue_df)}")

if len(venue_df) > 0:
    batting_first_wins = len(venue_df[venue_df['result'] == 'runs'])
    chasing_wins = len(venue_df[venue_df['result'] == 'wickets'])
    
    chart_data = pd.DataFrame({
        'Outcome': ['Batting First', 'Chasing'],
        'Wins': [batting_first_wins, chasing_wins]
    })
    
    fig = px.pie(chart_data, values='Wins', names='Outcome', 
                 color='Outcome',
                 color_discrete_map={'Batting First':'#38BDF8', 'Chasing':'#818CF8'},
                 hole=0.4) 
    
    fig.update_traces(textposition='inside', textinfo='percent+label', 
                      textfont_size=16, textfont_color='white',
                      marker=dict(line=dict(color='#111827', width=2)))
                      
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "#E2E8F0", 'size': 15}, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Not enough data to calculate win ratios for this venue.")

# --- 4. Head-to-Head Matchup ---
st.markdown("---") 
st.header("⚔️ Head-to-Head Matchup")

col1, col2 = st.columns(2)
with col1:
    default_idx1 = teams.index('Chennai Super Kings') if 'Chennai Super Kings' in teams else 0
    team1 = st.selectbox("Select Team 1", teams, index=default_idx1)
    
with col2:
    default_idx2 = teams.index('Mumbai Indians') if 'Mumbai Indians' in teams else 1
    team2 = st.selectbox("Select Team 2", teams, index=default_idx2)

if team1 == team2:
    st.warning("⚠️ Please select two different teams!")
else:
    mask = ((match_df['team1'] == team1) & (match_df['team2'] == team2)) | ((match_df['team1'] == team2) & (match_df['team2'] == team1))
    h2h_df = match_df[mask]
    
    st.write(f"**Total Matches Played between {team1} and {team2}:** {len(h2h_df)}")
    
    if len(h2h_df) > 0:
        wins = h2h_df['winner'].value_counts().reset_index()
        wins.columns = ['Team', 'Wins']
        
        fig2 = px.bar(wins, x='Team', y='Wins', 
                      color='Team', 
                      title=f"Historic Win Record: {team1} vs {team2}",
                      text='Wins',
                      color_discrete_sequence=['#8B5CF6', '#D97706']) 
        
        fig2.update_traces(textfont_size=22, textfont_color='white')              
        fig2.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': "#E2E8F0", 'size': 15})
        fig2.update_xaxes(showgrid=False, tickfont=dict(size=18))
        fig2.update_yaxes(showgrid=True, gridcolor='#334155')
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("These two teams have never played against each other in the dataset.")

# --- 5. Team Dominance Matrix ---
st.markdown("---")
st.header("🎯 Team Dominance by Stadium")
st.write("Analyze a specific team's win percentage across all venues where they've played at least 3 matches.")

focus_team = st.selectbox("Select a Team to Analyze", teams, index=teams.index('Chennai Super Kings') if 'Chennai Super Kings' in teams else 0)

# Filter matches where the selected team played
team_matches = match_df[(match_df['team1'] == focus_team) | (match_df['team2'] == focus_team)]

if len(team_matches) > 0:
    # Calculate matches played at each venue by this team
    venue_counts = team_matches['venue'].value_counts().reset_index()
    venue_counts.columns = ['Venue', 'Matches Played']
    
    # Calculate matches won at each venue by this team
    team_wins = team_matches[team_matches['winner'] == focus_team]['venue'].value_counts().reset_index()
    team_wins.columns = ['Venue', 'Wins']
    
    # Merge and calculate win percentage
    dominance_df = pd.merge(venue_counts, team_wins, on='Venue', how='left').fillna(0)
    dominance_df['Win Percentage'] = (dominance_df['Wins'] / dominance_df['Matches Played']) * 100
    dominance_df['Win Percentage'] = dominance_df['Win Percentage'].round(1)
    
    # Filter out stadiums with too little data
    dominance_df = dominance_df[dominance_df['Matches Played'] >= 3].sort_values(by='Win Percentage', ascending=True)
    
    if len(dominance_df) > 0:
        fig_dom = px.bar(dominance_df, 
                         x='Win Percentage', 
                         y='Venue', 
                         orientation='h',
                         title=f"{focus_team} - Strongest to Weakest Stadiums",
                         text='Win Percentage',
                         hover_data=['Matches Played', 'Wins'],
                         color='Win Percentage',
                         color_continuous_scale=['#EF4444', '#FBBF24', '#10B981'])
        
        fig_dom.update_traces(texttemplate='%{text}%', textposition='inside', textfont_size=14, textfont_color='white')
        fig_dom.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
                              font={'color': "#E2E8F0", 'size': 14},
                              coloraxis_showscale=False,
                              height=max(400, len(dominance_df) * 40)) 
        
        fig_dom.update_xaxes(showgrid=True, gridcolor='#334155', range=[0, 100], title="Win %")
        fig_dom.update_yaxes(title="")
        
        st.plotly_chart(fig_dom, use_container_width=True)
    else:
        st.info("Not enough data to map dominance. The team needs to have played at least 3 matches at a venue.")
else:
    st.info("No match data available for this team.")


# --- NEW: 6. Historical Match Progression ---
st.markdown("---")
st.header("📈 Historical Match Progression")
st.write("Select a specific match to see how the run chase progressed ball-by-ball.")

if not ml_df.empty and 'match_id' in ml_df.columns:
    # Get a list of unique match IDs
    match_ids = sorted(ml_df['match_id'].unique())
    
    # Default to the first match if available
    selected_match_id = st.selectbox("Select Match ID", match_ids)
    
# --- NEW: 6. Team Chase Pacing ---
st.markdown("---")
st.header("📈 Average Team Chase Pacing")
st.write("Analyze how a specific team paces their run chase over 120 balls on average.")

if not ml_df.empty:
    # Get a list of teams available in the ML data
    chasing_teams = sorted(ml_df['batting_team'].unique())
    
    # Let the user select a team to analyze
    selected_chasing_team = st.selectbox("Select Chasing Team", chasing_teams)
    
    # Filter for the selected team
    team_chase_data = ml_df[ml_df['batting_team'] == selected_chasing_team].copy()
    
    if not team_chase_data.empty:
        # Reconstruct balls played
        team_chase_data['balls_played'] = 120 - team_chase_data['balls_left']
        # Reconstruct current score
        team_chase_data['current_runs'] = team_chase_data['target'] - team_chase_data['runs_left']
        
        # Group by balls played and calculate the average runs scored at each ball
        avg_progression = team_chase_data.groupby('balls_played')['current_runs'].mean().reset_index()
        
        # Create the line chart
        fig_prog = px.line(avg_progression, x='balls_played', y='current_runs', 
                           title=f"Average Run Progression: {selected_chasing_team}",
                           labels={'balls_played': 'Balls Played', 'current_runs': 'Average Cumulative Runs'},
                           line_shape='spline')
                           
        # Styling
        fig_prog.update_traces(line=dict(color='#38BDF8', width=4))
        fig_prog.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': "#E2E8F0"})
        fig_prog.update_xaxes(showgrid=True, gridcolor='#334155', range=[0, 120])
        fig_prog.update_yaxes(showgrid=True, gridcolor='#334155')
        
        st.plotly_chart(fig_prog, use_container_width=True)
else:
    st.info("Ball-by-ball progression data (`ml_data.csv`) is unavailable.")

# --- 7. Live Match Win Predictor ---
st.markdown("---")
st.header("🔮 Live Match Win Predictor")

try:
    pipe = pickle.load(open('model.pkl', 'rb'))
except FileNotFoundError:
    st.error("Model file not found! Please ensure 'model.pkl' is in the same folder.")
    st.stop()

# Layout for Team and Venue Selection
col3, col4, col5 = st.columns(3)
with col3:
    batting_team = st.selectbox("Batting Team (Chasing)", teams, index=teams.index('Chennai Super Kings') if 'Chennai Super Kings' in teams else 0)
with col4:
    bowling_team = st.selectbox("Bowling Team (Defending)", teams, index=teams.index('Mumbai Indians') if 'Mumbai Indians' in teams else 1)
with col5:
    selected_stadium = st.selectbox("Predict at Venue", stadiums)

# Layout for Live Match Situation Inputs
col6, col7, col8, col9 = st.columns(4)
with col6:
    target = st.number_input("Target Score", min_value=0, max_value=300, value=180)
with col7:
    score = st.number_input("Current Score", min_value=0, max_value=target, value=120)
with col8:
    overs = st.number_input("Overs Completed", min_value=0.0, max_value=20.0, value=15.0, step=0.1)
with col9:
    wickets = st.number_input("Wickets Fallen", min_value=0, max_value=10, value=4)

if st.button("Predict Win Probability"):
    if batting_team == bowling_team:
        st.error("Batting and Bowling teams must be different!")
    else:
        # Math calculations
        runs_left = target - score
        balls_left = 120 - int(overs * 6)
        wickets_left = 10 - wickets
        crr = (score * 6) / (int(overs * 6)) if overs > 0 else 0
        rrr = (runs_left * 6) / balls_left if balls_left > 0 else 0
        
        input_df = pd.DataFrame({
            'batting_team': [batting_team], 'bowling_team': [bowling_team], 'venue': [selected_stadium], 
            'runs_left': [runs_left], 'balls_left': [balls_left], 'wickets_left': [wickets_left], 
            'target': [target], 'crr': [crr], 'rrr': [rrr]
        })
        
        result = pipe.predict_proba(input_df)
        win_prob = result[0][1] * 100
        
        st.subheader("Match Win Probability")
        
        fig3 = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = win_prob,
            title = {'text': f"{batting_team} Win %", 'font': {'size': 26, 'color': '#E2E8F0'}}, 
            number = {'font': {'color': '#E2E8F0'}}, 
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#334155"},
                'bar': {'color': "rgba(0,0,0,0)"}, 
                'bgcolor': "rgba(0,0,0,0)", 
                'borderwidth': 0, 
                'steps': [
                    {'range': [0, 40], 'color': "#EF4444"},     
                    {'range': [40, 60], 'color': "#F59E0B"},    
                    {'range': [60, 100], 'color': "#10B981"}    
                ],
                'threshold': {
                    'line': {'color': "#FFFFFF", 'width': 4}, 
                    'thickness': 0.75,
                    'value': win_prob
                }
            }
        ))
        
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "#E2E8F0"})
        st.plotly_chart(fig3, use_container_width=True)
        
        st.markdown(
            f"""
            <div style="background-color: #1E293B; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #334155;">
                <h4 style="margin: 0; color: #94A3B8; font-weight: normal; font-size: 20px;">
                    <strong style="color: #E2E8F0;">{bowling_team}</strong> Win Probability: 
                    <span style="color: #38BDF8; font-weight: bold;">{round(100 - win_prob, 1)}%</span>
                </h4>
            </div>
            """, 
            unsafe_allow_html=True
        )