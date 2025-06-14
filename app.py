import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

# Load datasets for Curry, Harden, and LeBron
steph = pd.read_csv('3_stephen_curry_shot_chart_2023.csv')
harden = pd.read_csv('2_james_harden_shot_chart_2023.csv')
lebron = pd.read_csv('1_lebron_james_shot_chart_1_2023.csv')

# Add player column
steph['player'] = 'Stephen Curry'
harden['player'] = 'James Harden'
lebron['player'] = 'LeBron James'

# Combine datasets
all_players = pd.concat([steph, harden, lebron], ignore_index=True)

# Add game index to group by games
all_players['game_index'] = all_players.groupby('player').cumcount() + 1

# Filter for the first few games (e.g., first 5 games per player)
first_games = all_players[all_players['game_index'] <= 5]

# Add game result determination
def determine_game_result(row):
    if 'lebron_team_score' in row.index and 'opponent_team_score' in row.index:
        return 'Win' if row['lebron_team_score'] > row['opponent_team_score'] else 'Loss'
    elif 'team_score' in row.index and 'opponent_team_score' in row.index:
        return 'Win' if row['team_score'] > row['opponent_team_score'] else 'Loss'
    else:
        return 'Unknown'

if 'lebron_team_score' in first_games.columns or 'team_score' in first_games.columns:
    first_games['game_result'] = first_games.apply(determine_game_result, axis=1)

# Group by player and game to summarize results
game_results = first_games.groupby(['player', 'game_index'])['game_result'].first().reset_index()

# Prepare shot frequency by quarter data
all_players['qtr'] = all_players['qtr'].str.strip()
quarter_data = all_players.groupby(['player', 'qtr'])['result'].count().reset_index()
quarter_data = quarter_data.rename(columns={'result': 'total_shots'})

quarter_order = ['1st Qtr', '2nd Qtr', '3rd Qtr', '4th Qtr', 'OT']
quarter_data['qtr'] = pd.Categorical(quarter_data['qtr'], categories=quarter_order, ordered=True)
quarter_data = quarter_data.sort_values(['player', 'qtr'])

# Prepare data for player activity by quarter
activity_data = all_players.groupby(['player', 'qtr'])['result'].count().reset_index()
activity_data = activity_data.rename(columns={'result': 'plays_count'})
activity_data['qtr'] = pd.Categorical(activity_data['qtr'], categories=quarter_order, ordered=True)
activity_data = activity_data.sort_values(['player', 'qtr'])

# Initialize Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1('Basketball Analysis Dashboard', style={'textAlign': 'center'}),

    dcc.Dropdown(
        id='player-dropdown',
        options=[
            {'label': 'Stephen Curry', 'value': 'Stephen Curry'},
            {'label': 'James Harden', 'value': 'James Harden'},
            {'label': 'LeBron James', 'value': 'LeBron James'},
            {'label': 'All Players', 'value': 'All'}
        ],
        value='All',
        clearable=False,
        style={'width': '50%', 'margin': 'auto'}
    ),

    # Graph 1: Game Results
    html.Div([
        html.H2('Game Results for First 5 Games'),
        dcc.Graph(id='game-results-chart'),
    ]),

    # Graph 2: Shot Frequency by Quarter
    html.Div([
        html.H2('Shot Frequency by Quarter'),
        dcc.Graph(id='quarter-chart'),
    ]),

    # Graph 3: Player Activity by Quarter
    html.Div([
        html.H2('Player Activity by Quarter'),
        dcc.Graph(id='activity-chart'),
    ]),
])

@app.callback(
    [Output('game-results-chart', 'figure'),
     Output('quarter-chart', 'figure'),
     Output('activity-chart', 'figure')],
    [Input('player-dropdown', 'value')]
)
def update_charts(selected_player):
    # Update Game Results Chart
    if selected_player == 'All':
        filtered_game_results = game_results
        filtered_quarter_data = quarter_data
        filtered_activity_data = activity_data
    else:
        filtered_game_results = game_results[game_results['player'] == selected_player]
        filtered_quarter_data = quarter_data[quarter_data['player'] == selected_player]
        filtered_activity_data = activity_data[activity_data['player'] == selected_player]

    game_results_fig = px.bar(
        filtered_game_results,
        x='game_index',
        y='game_result',
        color='game_result',
        barmode='group',
        labels={'game_index': 'Game Number', 'game_result': 'Result'},
        title=f'Game Results for {selected_player if selected_player != "All" else "All Players"}'
    )
    game_results_fig.update_layout(transition_duration=500)

    # Update Quarter Chart
    quarter_chart_fig = px.bar(
        filtered_quarter_data,
        x='qtr',
        y='total_shots',
        color='player',
        barmode='group',
        labels={'qtr': 'Quarter', 'total_shots': 'Total Shots'},
        title=f'Shot Frequency by Quarter for {selected_player if selected_player != "All" else "All Players"}'
    )
    quarter_chart_fig.update_layout(transition_duration=500)

    # Update Activity Chart
    activity_chart_fig = px.bar(
        filtered_activity_data,
        x='qtr',
        y='plays_count',
        color='player',
        barmode='group',
        labels={'qtr': 'Quarter', 'plays_count': 'Total Plays'},
        title=f'Player Activity by Quarter for {selected_player if selected_player != "All" else "All Players"}'
    )
    activity_chart_fig.update_layout(transition_duration=500)

    return game_results_fig, quarter_chart_fig, activity_chart_fig

# Run the Dash app
if __name__ == '__main__':
    app.run(debug=True)
