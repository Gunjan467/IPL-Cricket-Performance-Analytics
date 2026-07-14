import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pickle
import numpy as np

# --- 1. Setup the Web Page ---
st.set_page_config(page_title="IPL Analytics Dashboard", layout="wide", initial_sidebar_state="collapsed")
st.title("🏏 IPL Cricket Performance Analytics")
st.write("Welcome to the interactive IPL match analysis dashboard.")

THEME_COLORS = ['#4F46E5', '#06B6D4', '#10B981', '#3B82F6'] 

# --- 2. Load and Clean Data ---
@st.cache_data
def load_and_clean_data():
    df = pd.read_csv('data/data.csv')
    
    try:
        ml_df = pd.read_csv('data/ml_data.csv')
    except FileNotFoundError:
        ml_df = pd.DataFrame()
    
    match_df = df.drop_duplicates(subset=['match_id']).copy()
    
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
    
    if not ml_df.empty:
        if 'batting_team' in ml_df.columns:
            ml_df['batting_team'] = ml_df['batting_team'].replace(team_mapping)
        if 'bowling_team' in ml_df.columns:
            ml_df['bowling_team'] = ml_df['bowling_team'].replace(team_mapping)
            
    return match_df, ml_df

match_df, ml_df = load_and_clean_data()
teams = sorted(match_df['team1'].dropna().unique())
stadiums = sorted(match_df['venue'].dropna().unique())

# --- NEW: UI LAYOUT WITH TABS ---
tab1, tab2, tab3 = st.tabs(["🏟️ Venue Insights", "⚔️ Team Analytics", "🔮 Live Predictor"])

# ==========================================
# TAB 1: VENUE INSIGHTS
# ==========================================
with tab1:
    st.header("Venue Analysis")
    selected_venue = st.selectbox("Select a Stadium", stadiums, index=stadiums.index('Wankhede Stadium') if 'Wankhede Stadium' in stadiums else 0)

    venue_df = match_df[match_df['venue'] == selected_venue]
    
    # Use columns within the tab for better layout
    v_col1, v_col2 = st.columns([1, 2])
    
    with v_col1:
        st.write("") # Spacing
        st.write(f"**Total Matches:** {len(venue_df)}")
        if len(venue_df) > 0:
            batting_first_wins = len(venue_df[venue_df['result'] == 'runs'])
            chasing_wins = len(venue_df[venue_df['result'] == 'wickets'])
            st.metric(label="Batting First Win %", value=f"{round((batting_first_wins/len(venue_df))*100, 1)}%")
            st.metric(label="Chasing Win %", value=f"{round((chasing_wins/len(venue_df))*100, 1)}%")
        
    with v_col2:
        if len(venue_df) > 0:
            chart_data = pd.DataFrame({'Outcome': ['Batting First', 'Chasing'], 'Wins': [batting_first_wins, chasing_wins]})
            fig = px.pie(chart_data, values='Wins', names='Outcome', color='Outcome',
                         color_discrete_map={'Batting First':'#4F46E5', 'Chasing':'#06B6D4'}, hole=0.4) 
            fig.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#111827', width=2)))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "#E2E8F0"}, showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Not enough data for this venue.")

    st.markdown("---")
    st.header("🎯 Team Dominance Matrix")
    focus_team = st.selectbox("Select Team", teams, index=teams.index('Chennai Super Kings') if 'Chennai Super Kings' in teams else 0)
    team_matches = match_df[(match_df['team1'] == focus_team) | (match_df['team2'] == focus_team)]

    if len(team_matches) > 0:
        venue_counts = team_matches['venue'].value_counts().reset_index()
        venue_counts.columns = ['Venue', 'Matches Played']
        team_wins = team_matches[team_matches['winner'] == focus_team]['venue'].value_counts().reset_index()
        team_wins.columns = ['Venue', 'Wins']
        dominance_df = pd.merge(venue_counts, team_wins, on='Venue', how='left').fillna(0)
        dominance_df['Win Percentage'] = (dominance_df['Wins'] / dominance_df['Matches Played']) * 100
        dominance_df = dominance_df[dominance_df['Matches Played'] >= 3].sort_values(by='Win Percentage', ascending=True)
        
        if len(dominance_df) > 0:
            fig_dom = px.bar(dominance_df, x='Win Percentage', y='Venue', orientation='h',
                             text='Win Percentage', hover_data=['Matches Played', 'Wins'],
                             color='Win Percentage', color_continuous_scale=['#EF4444', '#FBBF24', '#10B981'])
            fig_dom.update_traces(texttemplate='%{text:.1f}%', textposition='inside', textfont_color='white')
            fig_dom.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': "#E2E8F0"},
                                  coloraxis_showscale=False, height=max(300, len(dominance_df) * 35), margin=dict(l=10, r=10, t=10, b=10)) 
            fig_dom.update_xaxes(showgrid=True, gridcolor='#334155', range=[0, 100], title="")
            fig_dom.update_yaxes(title="")
            st.plotly_chart(fig_dom, use_container_width=True)
        else:
            st.info("Requires at least 3 matches at a venue.")

# ==========================================
# TAB 2: TEAM ANALYTICS
# ==========================================
with tab2:
    st.header("Head-to-Head Matchup")
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        team1 = st.selectbox("Team 1", teams, index=teams.index('Chennai Super Kings') if 'Chennai Super Kings' in teams else 0)
    with t_col2:
        team2 = st.selectbox("Team 2", teams, index=teams.index('Mumbai Indians') if 'Mumbai Indians' in teams else 1)

    if team1 == team2:
        st.warning("⚠️ Please select two different teams!")
    else:
        mask = ((match_df['team1'] == team1) & (match_df['team2'] == team2)) | ((match_df['team1'] == team2) & (match_df['team2'] == team1))
        h2h_df = match_df[mask]
        
        if len(h2h_df) > 0:
            wins = h2h_df['winner'].value_counts().reset_index()
            wins.columns = ['Team', 'Wins']
            fig2 = px.bar(wins, x='Team', y='Wins', color='Team', text='Wins', color_discrete_sequence=['#8B5CF6', '#D97706'])
            fig2.update_traces(textfont_size=20, textfont_color='white')              
            fig2.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': "#E2E8F0"}, margin=dict(t=30))
            fig2.update_xaxes(showgrid=False, title="")
            fig2.update_yaxes(showgrid=True, gridcolor='#334155', title="Total Wins")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No historical matches found between these teams.")

    st.markdown("---")
    st.header("Average Team Chase Pacing")
    if not ml_df.empty:
        chasing_teams = sorted(ml_df['batting_team'].unique())
        selected_chasing_team = st.selectbox("Select Chasing Team", chasing_teams)
        team_chase_data = ml_df[ml_df['batting_team'] == selected_chasing_team].copy()
        
        if not team_chase_data.empty:
            team_chase_data['balls_played'] = 120 - team_chase_data['balls_left']
            team_chase_data['current_runs'] = team_chase_data['target'] - team_chase_data['runs_left']
            avg_progression = team_chase_data.groupby('balls_played')['current_runs'].mean().reset_index()
            
            fig_prog = px.line(avg_progression, x='balls_played', y='current_runs', line_shape='spline')
            fig_prog.update_traces(line=dict(color='#06B6D4', width=4))
            fig_prog.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': "#E2E8F0"}, margin=dict(t=20))
            fig_prog.update_xaxes(showgrid=True, gridcolor='#334155', range=[0, 120], title="Balls Played")
            fig_prog.update_yaxes(showgrid=True, gridcolor='#334155', title="Average Cumulative Runs")
            st.plotly_chart(fig_prog, use_container_width=True)
    else:
        st.info("Progression data unavailable.")

# ==========================================
# TAB 3: LIVE PREDICTOR
# ==========================================
with tab3:
    st.header("Live Match Win Predictor")
    try:
        pipe = pickle.load(open('model.pkl', 'rb'))
        
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            batting_team = st.selectbox("Batting (Chasing)", teams, index=teams.index('Chennai Super Kings') if 'Chennai Super Kings' in teams else 0)
        with p_col2:
            bowling_team = st.selectbox("Bowling (Defending)", teams, index=teams.index('Mumbai Indians') if 'Mumbai Indians' in teams else 1)
        with p_col3:
            selected_stadium = st.selectbox("At Venue", stadiums)

        st.markdown("<br>", unsafe_allow_html=True)
        
        i_col1, i_col2, i_col3, i_col4 = st.columns(4)
        with i_col1:
            target = st.number_input("Target Score", min_value=0, max_value=300, value=180)
        with i_col2:
            score = st.number_input("Current Score", min_value=0, max_value=target, value=120)
        with i_col3:
            overs = st.number_input("Overs Completed", min_value=0.0, max_value=20.0, value=15.0, step=0.1)
        with i_col4:
            wickets = st.number_input("Wickets Fallen", min_value=0, max_value=10, value=4)

        if st.button("Calculate Probability", type="primary", use_container_width=True):
            if batting_team == bowling_team:
                st.error("Teams must be different!")
            else:
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
                
                # Use columns to center the gauge
                g_col1, g_col2, g_col3 = st.columns([1, 2, 1])
                with g_col2:
                    fig3 = go.Figure(go.Indicator(
                        mode = "gauge+number", value = win_prob,
                        title = {'text': f"{batting_team} Win %", 'font': {'size': 22, 'color': '#E2E8F0'}},
                        number = {'font': {'color': '#E2E8F0'}}, 
                        gauge = {
                            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#334155"},
                            'bar': {'color': "rgba(0,0,0,0)"}, 'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 0, 
                            'steps': [{'range': [0, 40], 'color': "#EF4444"}, {'range': [40, 60], 'color': "#F59E0B"}, {'range': [60, 100], 'color': "#10B981"}],
                            'threshold': {'line': {'color': "#FFFFFF", 'width': 4}, 'thickness': 0.75, 'value': win_prob}
                        }
                    ))
                    fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "#E2E8F0"}, margin=dict(t=40, b=10))
                    st.plotly_chart(fig3, use_container_width=True)
                
                st.markdown(
                    f"""
                    <div style="background-color: #1E293B; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #334155;">
                        <h4 style="margin: 0; color: #94A3B8; font-weight: normal;">
                            <strong style="color: #E2E8F0;">{bowling_team}</strong> Win Probability: 
                            <span style="color: #38BDF8; font-weight: bold;">{round(100 - win_prob, 1)}%</span>
                        </h4>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
    except FileNotFoundError:
        st.error("Model file 'model.pkl' not found.")