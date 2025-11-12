# dashboard_simple_three_charts.py
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# Load and normalize
df = pd.read_csv("cleaned_space_missions.csv")
df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('-', '_')
df = df.dropna(subset=['Year'])
df['Year'] = df['Year'].astype(int)

# Prepare options
countries = sorted(df['Country'].dropna().unique())
companies = sorted(df['Company_Name'].dropna().unique())
min_year, max_year = int(df['Year'].min()), int(df['Year'].max())

app = Dash(__name__)
app.title = "Space Missions Dashboard (3 Charts)"

def make_kpi_card(title, value):
    return html.Div([
        html.Div(title, style={'fontSize':12, 'color':'#666'}),
        html.Div(value, style={'fontSize':20, 'fontWeight':'bold'})
    ], style={'padding':'10px','border':'1px solid #eee','borderRadius':6,'width':'160px','background':'#fff','textAlign':'center'})

app.layout = html.Div([
    html.H1("Space Missions Dashboard", style={'textAlign':'center', 'marginTop':10}),

    html.Div(id='kpi-row', style={'display':'flex','gap':'12px','justifyContent':'center','padding':'8px 12px'}),

    # Filters
    html.Div([
        html.Div([
            html.Label("Country"),
            dcc.Dropdown(id='country_filter', options=[{'label':c,'value':c} for c in countries],
                         value=None, placeholder="All countries", multi=True)
        ], style={'width':'32%','display':'inline-block','paddingRight':12}),
        html.Div([
            html.Label("Company"),
            dcc.Dropdown(id='company_filter', options=[{'label':c,'value':c} for c in companies],
                         value=None, placeholder="All companies", multi=True)
        ], style={'width':'32%','display':'inline-block','paddingRight':12}),
        html.Div([
            html.Label("Year range"),
            dcc.RangeSlider(id='year_slider', min=min_year, max=max_year, value=[min_year,max_year],
                            marks={y:str(y) for y in range(min_year, max_year+1, 5)}, step=1)
        ], style={'width':'100%','paddingTop':8})
    ], style={'maxWidth':1200,'margin':'0 auto'}),

    html.Hr(),

    # Only these three charts
    dcc.Graph(id='launches_time', style={'height':'480px'}),
    dcc.Graph(id='top_countries', style={'height':'420px'}),
    dcc.Graph(id='missions_outcomes', style={'height':'480px'}),

    html.Div(id='debug', style={'fontSize':12, 'color':'gray', 'textAlign':'center', 'marginTop':'10px'})
], style={'fontFamily':'Arial, sans-serif'})

def filter_df(selected_countries, selected_companies, year_range):
    dff = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
    if selected_countries:
        dff = dff[dff['Country'].isin(selected_countries)]
    if selected_companies:
        dff = dff[dff['Company_Name'].isin(selected_companies)]
    return dff

@app.callback(
    Output('kpi-row','children'),
    Output('launches_time','figure'),
    Output('top_countries','figure'),
    Output('missions_outcomes','figure'),
    Output('debug','children'),
    Input('country_filter','value'),
    Input('company_filter','value'),
    Input('year_slider','value')
)
def update(selected_countries, selected_companies, year_range):
    dff = filter_df(selected_countries, selected_companies, year_range)

    # KPIs
    total_launches = int(dff.shape[0])
    succ = int((dff['Status_Mission']=='Success').sum()) if 'Status_Mission' in dff.columns else 0
    success_rate = f"{round((succ/total_launches*100),2)}%" if total_launches else "N/A"
    active = int((dff['Status_Rocket'].astype(str).str.lower()=='active').sum()) if 'Status_Rocket' in dff.columns else 0

    kpis = [
        make_kpi_card("Total launches", total_launches),
        make_kpi_card("Total successes", succ),
        make_kpi_card("Success rate", success_rate),
        make_kpi_card("Active rockets", active)
    ]

    # Chart 1: Launches over time
    if dff.empty:
        empty_fig = px.scatter(title='No data for selected filters')
        empty_fig.update_layout(xaxis={'visible':False}, yaxis={'visible':False})
        return kpis, empty_fig, empty_fig, empty_fig, f"Filtered rows: 0"

    launches_per_year = dff.groupby('Year').size().reset_index(name='Launches').sort_values('Year')
    fig1 = px.line(launches_per_year, x='Year', y='Launches', markers=True, title='Number of Space Launches Per Year')
    fig1.update_layout(xaxis=dict(rangeslider=dict(visible=True)))

    # Chart 2: Top countries
    country_counts = dff['Country'].value_counts().reset_index(name='Total').rename(columns={'index':'Country'})
    fig2 = px.bar(country_counts.head(15), x='Country', y='Total', title='Top Countries by Launches')
    fig2.update_layout(xaxis_tickangle=-45)

    # Chart 3: Mission outcomes
    if 'Status_Mission' in dff.columns and dff['Status_Mission'].notna().any():
        outcomes = dff.groupby(['Year','Status_Mission']).size().reset_index(name='Count')
        fig3 = px.bar(outcomes, x='Year', y='Count', color='Status_Mission', barmode='stack', title='Mission Outcomes Over Time')
    else:
        fig3 = px.scatter(title='Mission outcome data unavailable')

    return kpis, fig1, fig2, fig3, f"Filtered rows: {dff.shape[0]}"

if __name__ == "__main__":
    app.run_server(debug=True)