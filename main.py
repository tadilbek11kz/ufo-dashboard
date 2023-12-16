import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from dash import Dash, html, dcc, callback, Output, Input, callback_context
from dash_daq import BooleanSwitch
import os

HOST = os.getenv('HOST', '10.16.121.111')
DEBUG = os.getenv('DEBUG', False)

pd.options.plotting.backend = "plotly"

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)

engine = create_engine(f'postgresql://postgres:postgres@{HOST}:5432/ufo')

cities = pd.read_sql_query('SELECT DISTINCT city FROM ufo_sightings', con=engine).sort_values(by='city').apply(lambda x: x.str.capitalize())['city'].tolist()
states = pd.read_sql_query('SELECT DISTINCT state FROM ufo_sightings', con=engine).sort_values(by='state')['state'].tolist()
shapes = pd.read_sql_query('SELECT DISTINCT shape FROM ufo_sightings', con=engine).sort_values(by='shape')['shape'].tolist()
weather_condition = pd.read_sql_query('SELECT DISTINCT label FROM weather', con=engine).sort_values(by='label')['label'].tolist()
max_year = pd.read_sql_query('SELECT MAX(EXTRACT(YEAR FROM sigthed_date)) AS max_year FROM ufo_sightings', con=engine)['max_year'].tolist()[0]
min_year = pd.read_sql_query('SELECT MIN(EXTRACT(YEAR FROM sigthed_date)) AS min_year FROM ufo_sightings', con=engine)['min_year'].tolist()[0]
daytime = pd.read_sql_query('SELECT DISTINCT daytime FROM ufo_sightings', con=engine)['daytime'].tolist()


def density_graph():
    query = f"""
        SELECT lat, lng, COUNT(*) AS total_sightings
        FROM ufo_sightings
        GROUP BY lat, lng
        ORDER BY total_sightings DESC
    """
    ufo_sightings = pd.read_sql_query(query, con=engine)

    fig = px.density_mapbox(ufo_sightings, lat='lat', lon='lng', z='total_sightings', labels={'total_sightings': 'UFO count'}, radius=10, center=dict(lat=39.8283, lon=-98.5795), zoom=3, mapbox_style="open-street-map")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': 'white'})

    return fig


def heatmap_graph(type, normilize=False):
    if type == 'population':
        query = f"""
            SELECT state, population, code
            FROM population
        """
        data = pd.read_sql_query(query, con=engine)

        fig = px.choropleth(data, locations="code", locationmode="USA-states", color="population", scope='usa', color_continuous_scale=px.colors.sequential.Oranges)
    elif type == 'sightings' and not normilize:
        query = f"""
            SELECT state, COUNT(*) AS total_sightings
            FROM ufo_sightings
            GROUP BY state
            ORDER BY total_sightings DESC
        """
        data = pd.read_sql_query(query, con=engine)

        fig = px.choropleth(data, labels={'total_sightings': 'UFO count'}, locations="state", locationmode="USA-states", color="total_sightings", scope='usa', color_continuous_scale=px.colors.sequential.Oranges)

    elif type == 'sightings' and normilize:
        query = f"""
            SELECT 
                ufo_sightings.state,
                COUNT(DISTINCT ufo_sightings.id) / population.population::numeric as total_sightings
            FROM ufo_sightings
            LEFT JOIN population ON ufo_sightings.state = population.code
            GROUP BY ufo_sightings.state, population.population
        """
        data = pd.read_sql_query(query, con=engine)

        fig = px.choropleth(data, labels={'total_sightings': 'UFO/Person count'}, locations="state", locationmode="USA-states", color="total_sightings", scope='usa', color_continuous_scale=px.colors.sequential.Oranges)

    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': 'white'})

    return fig


app.layout = html.Div(children=[
    html.Header(className='row', children=[
        html.Img(className='two columns', src='./assets/logo.png', style={'width': '64px', 'height': '64px'}),
        html.H3(children='UFO Sightings (GROUP F)'),
    ], style={'display': 'flex', 'align-items': 'center', 'gap': '10px', 'padding': '10px'}),

    dcc.Tabs([
        dcc.Tab(label='UFO Sightings', children=[
            html.Div(className='ufo-tab', children=[
                html.Div(className='four columns', children=[
                    html.Div(children='Year', style={'padding': '5px'}),
                    html.Div(className='row', children=[
                        dcc.Input(className='input three columns', id="ufo-tab--start", type="number", min=min_year, max=max_year, value=2000),
                        dcc.Input(className='input three columns', id="ufo-tab--end", type="number", min=min_year, max=max_year, value=2010),
                    ], style={'padding-bottom': '20px'}),
                    dcc.RangeSlider(min_year, max_year, 1, id='ufo-tab--slider', value=[2000, 2010], marks=None, tooltip={"placement": "bottom", "always_visible": False}),

                    html.Div(className='row', children=[
                        BooleanSwitch(id='ufo-tab--log', label='LogFN', labelPosition='top', on=False, color='black'),
                    ], style={'display': 'flex', 'justify-content': 'flex-start', 'margin-bottom': '10px'}),

                    html.Div(children='Time of Day', style={'padding': '5px'}),
                    dcc.Dropdown(daytime, None, id='ufo-tab--daytime-selection', style={'margin-bottom': '10px'}),

                    html.Div(children='State', style={'padding': '5px'}),
                    dcc.Dropdown(states, None, id='ufo-tab--state-selection', style={'margin-bottom': '10px'}),

                    html.Div(children='City / Town', style={'padding': '5px'}),
                    dcc.Dropdown(cities, None, id='ufo-tab--city-selection', style={'margin-bottom': '10px'}),

                ], style={'display': 'flex', 'flex-direction': 'column'}),

                html.Div(className='eight columns', children=[
                    dcc.Graph(id='ufo-tab--graph'),
                ]),
            ]),
        ], style={'background-color': 'black', 'color': 'white', 'border': '0', 'border-top-left-radius': '10px'}, selected_style={'background-color': '#222222', 'color': 'white', 'border': '0', 'border-top-left-radius': '10px'}),

        dcc.Tab(label='UFO Shapes', children=[
            html.Div(className='shape-tab', children=[
                html.Div(className='four columns', children=[
                    html.Div(children='Year', style={'padding': '5px'}),
                    html.Div(className='row', children=[
                        dcc.Input(className='input three columns', id="shape-tab--start", type="number", min=min_year, max=max_year, value=2000),
                        dcc.Input(className='input three columns', id="shape-tab--end", type="number", min=min_year, max=max_year, value=2010),
                    ], style={'padding-bottom': '20px'}),
                    dcc.RangeSlider(min_year, max_year, 1, id='shape-tab--slider', value=[2000, 2010], marks=None, tooltip={"placement": "bottom", "always_visible": False}),

                    html.Div(children='Time of Day', style={'padding': '5px'}),
                    dcc.Dropdown(daytime, None, id='shape-tab--daytime-selection', style={'margin-bottom': '10px'}),

                    html.Div(children='State', style={'padding': '5px'}),
                    dcc.Dropdown(states, None, id='shape-tab--state-selection', style={'margin-bottom': '10px'}),

                    html.Div(children='City / Town', style={'padding': '5px'}),
                    dcc.Dropdown(cities, None, id='shape-tab--city-selection', style={'margin-bottom': '10px'}),

                ], style={'display': 'flex', 'flex-direction': 'column'}),

                html.Div(className='eight columns', children=[
                    dcc.Graph(id='shape-tab--graph'),
                ]),
            ]),
        ], style={'background-color': 'black', 'color': 'white', 'border': '0'}, selected_style={'background-color': '#222222', 'color': 'white', 'border': '0'}),

        dcc.Tab(label='Weather', children=[
            html.Div(className='weather-tab', children=[
                html.Div(className='twelve columns', children=[
                    dcc.Dropdown(['Count', 'Duration'], 'Count', id='weather-tab--graph-selection'),
                ]),

                html.Div(children=[
                    html.Div(className='four columns', children=[
                        html.Div(children='Year', style={'padding': '5px'}),
                        html.Div(className='row', children=[
                            dcc.Input(className='input three columns', id="weather-tab--start", type="number", min=min_year, max=max_year, value=2000),
                            dcc.Input(className='input three columns', id="weather-tab--end", type="number", min=min_year, max=max_year, value=2010),
                        ], style={'padding-bottom': '20px'}),
                        dcc.RangeSlider(min_year, max_year, 1, id='weather-tab--slider-year', value=[2000, 2010], marks=None, tooltip={"placement": "bottom", "always_visible": False}),

                        html.Div(children='Shape Count', style={'padding': '5px'}),
                        dcc.Slider(1, len(shapes), 1, id='weather-tab--slider-shape', value=6, marks={i: f'{i}' for i in range(1, len(shapes), 5)}, tooltip={"placement": "bottom", "always_visible": True}),


                        html.Div(className='row', children=[
                            BooleanSwitch(id='weather-tab--log', label='LogFN', labelPosition='top', on=False, color='black'),
                        ], style={'display': 'flex', 'justify-content': 'flex-start', 'margin-bottom': '10px'}),

                        html.Div(children='Time of Day', style={'padding': '5px'}),
                        dcc.Dropdown(daytime, None, id='weather-tab--daytime-selection', style={'margin-bottom': '10px'}),

                        html.Div(children='State', style={'padding': '5px'}),
                        dcc.Dropdown(states, None, id='weather-tab--state-selection', style={'margin-bottom': '10px'}),

                        html.Div(children='City / Town', style={'padding': '5px'}),
                        dcc.Dropdown(cities, None, id='weather-tab--city-selection', style={'margin-bottom': '10px'}),

                    ], style={'display': 'flex', 'flex-direction': 'column'}),

                    html.Div(className='eight columns', children=[
                        dcc.Graph(id='weather-tab--graph'),
                    ]),
                ], style={'display': 'flex', 'width': '100%', 'align-items': 'center', 'justify-content': 'center'}),
            ]),
        ], style={'background-color': 'black', 'color': 'white', 'border': '0'}, selected_style={'background-color': '#222222', 'color': 'white', 'border': '0'}),

        dcc.Tab(label='Heatmaps', children=[
            html.Div(className='heatmap-tab', children=[
                html.Div(className='twelve columns', children=[
                    html.H4(children='UFO Sightings Heatmaps', style={'text-align': 'center'}),
                    dcc.Graph(figure=density_graph()),
                ]),
                html.Div(children=[
                    html.Div(className='six columns', children=[
                        dcc.Graph(figure=heatmap_graph('population')),
                    ]),
                    html.Div(className='six columns', children=[
                        dcc.Graph(figure=heatmap_graph('sightings')),
                    ]),
                ], style={'display': 'flex', 'width': '100%', 'align-items': 'center', 'justify-content': 'center'}),
                html.Div(className='twelve columns', children=[
                    dcc.Graph(figure=heatmap_graph('sightings', True)),
                ]),
            ]),
        ], style={'background-color': 'black', 'color': 'white', 'border': '0', 'border-top-right-radius': '10px'}, selected_style={'background-color': '#222222', 'color': 'white', 'border': '0', 'border-top-right-radius': '10px'}),
    ], style={'margin': '10px 10px 0px'}),
])


@callback(
    Output("ufo-tab--start", "value"),
    Output("ufo-tab--end", "value"),
    Output("ufo-tab--slider", "value"),
    Input("ufo-tab--start", "value"),
    Input("ufo-tab--end", "value"),
    Input("ufo-tab--slider", "value"),
)
def update_slider(start, end, slider):
    ctx = callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    start_value = start if trigger_id == "ufo-tab--start" else slider[0]
    end_value = end if trigger_id == "ufo-tab--end" else slider[1]
    slider_value = slider if trigger_id == "ufo-tab--slider" else [start_value, end_value]

    return start_value, end_value, slider_value


@callback(
    Output("weather-tab--start", "value"),
    Output("weather-tab--end", "value"),
    Output("weather-tab--slider-year", "value"),
    Input("weather-tab--start", "value"),
    Input("weather-tab--end", "value"),
    Input("weather-tab--slider-year", "value"),
)
def update_slider(start, end, slider):
    ctx = callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    start_value = start if trigger_id == "ufo-tab--start" else slider[0]
    end_value = end if trigger_id == "ufo-tab--end" else slider[1]
    slider_value = slider if trigger_id == "ufo-tab--slider-year" else [start_value, end_value]

    return start_value, end_value, slider_value


@callback(
    Output("shape-tab--start", "value"),
    Output("shape-tab--end", "value"),
    Output("shape-tab--slider", "value"),
    Input("shape-tab--start", "value"),
    Input("shape-tab--end", "value"),
    Input("shape-tab--slider", "value"),
)
def update_slider(start, end, slider):
    ctx = callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    start_value = start if trigger_id == "shape-tab--start" else slider[0]
    end_value = end if trigger_id == "shape-tab--end" else slider[1]
    slider_value = slider if trigger_id == "shape-tab--slider" else [start_value, end_value]

    return start_value, end_value, slider_value


@callback(
    Output('ufo-tab--graph', 'figure'),
    Input('ufo-tab--slider', 'value'),
    Input('ufo-tab--daytime-selection', 'value'),
    Input('ufo-tab--state-selection', 'value'),
    Input('ufo-tab--city-selection', 'value'),
    Input('ufo-tab--log', 'on')
)
def update_graph(year, daytime, state, city, log):
    year_filter = f"EXTRACT(YEAR FROM sigthed_date) BETWEEN {year[0]} AND {year[1]}"
    filters = {
        'daytime': daytime if daytime else '',
        'state': state if state else '',
        'city': city.lower() if city else '',
    }

    filter_query = ' AND '.join([year_filter] + [f'{key} = \'{value}\'' for key, value in filters.items() if value != ''])

    if len(filter_query) > 0:
        filter_query = 'WHERE ' + filter_query

    query = f"""
        SELECT EXTRACT(YEAR FROM sigthed_date) AS year, COUNT(*) AS total_sightings, shape
        FROM ufo_sightings
        {filter_query}
        GROUP BY year, shape
        ORDER BY year
    """

    ufo_sightings = pd.read_sql_query(query, con=engine)

    fig = px.bar(
        ufo_sightings,
        x='year',
        y='total_sightings',
        log_y=log,
        category_orders={'shape': shapes},
        color='shape',
        labels={'total_sightings': 'count'},
        title='Total UFO Sightings Over the Years',
        barmode='stack'
    )
    fig.update_layout(xaxis_title='Year', yaxis_title="Number of UFO")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': 'white'})

    return fig


@callback(
    Output('weather-tab--graph', 'figure'),
    Input('weather-tab--graph-selection', 'value'),
    Input('weather-tab--slider-year', 'value'),
    Input('weather-tab--slider-shape', 'value'),
    Input('weather-tab--daytime-selection', 'value'),
    Input('weather-tab--state-selection', 'value'),
    Input('weather-tab--city-selection', 'value'),
    Input('weather-tab--log', 'on')
)
def update_graph(type, year, shape_count, daytime, state, city, log):
    year_filter = f"EXTRACT(YEAR FROM sigthed_date) BETWEEN {year[0]} AND {year[1]}"
    filters = {
        'daytime': daytime if daytime else '',
        'state': state if state else '',
        'city': city.lower() if city else '',
    }

    filter_query = ' AND '.join([year_filter] + [f'{key} = \'{value}\'' for key, value in filters.items() if value != ''])

    if len(filter_query) > 0:
        filter_query = 'WHERE ' + filter_query

    aggregation = 'COUNT(DISTINCT ufo_sightings.id) AS total' if type == 'Count' else 'SUM(ufo_sightings.duration) / COUNT(DISTINCT ufo_sightings.id) AS total'

    query = f"""
        SELECT DISTINCT
            CASE WHEN ufo_sightings.shape IN (
                SELECT shape
                FROM (
                    SELECT shape, COUNT(*) AS count
                    FROM ufo_sightings
                    {filter_query}
                    GROUP BY shape
                    ORDER BY count DESC
                    LIMIT {int(shape_count)}
                ) AS top_shapes
            ) THEN ufo_sightings.shape
            END AS shape,
            weather.label,
            {aggregation}
        FROM ufo_sightings
        LEFT JOIN weather ON ufo_sightings.sigthed_date = weather.date
            AND ufo_sightings.lat = weather.latitude
            AND ufo_sightings.lng = weather.longitude
        {filter_query}
        GROUP BY shape, weather.label
        ORDER BY shape, weather.label
    """
    ufo_sightings = pd.read_sql_query(query, con=engine)
    ufo_sightings = ufo_sightings.groupby(['shape', 'label']).sum().reset_index()

    fig = px.bar(
        ufo_sightings,
        x='label',
        y='total',
        log_y=log,
        color='shape',
        category_orders={'shape': shapes, 'label': weather_condition},
        labels={'total': type.lower(), 'label': 'weather'},
        title=f'Total {type} UFO Sightings by Shape and Weather',
        barmode='group'
    )
    fig.update_layout(xaxis_title='Weather condition', yaxis_title=f'{type} of UFO')
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': 'white'})
    return fig


@callback(
    Output('shape-tab--graph', 'figure'),
    Input('shape-tab--slider', 'value'),
    Input('shape-tab--daytime-selection', 'value'),
    Input('shape-tab--state-selection', 'value'),
    Input('shape-tab--city-selection', 'value'),
)
def update_graph(year, daytime, state, city):
    year_filter = f"EXTRACT(YEAR FROM sigthed_date) BETWEEN {year[0]} AND {year[1]}"
    filters = {
        'daytime': daytime if daytime else '',
        'state': state if state else '',
        'city': city.lower() if city else '',
    }

    filter_query = ' AND '.join([year_filter] + [f'{key} = \'{value}\'' for key, value in filters.items() if value != ''])

    if len(filter_query) > 0:
        filter_query = 'WHERE ' + filter_query

    query = f"""
        SELECT shape, COUNT(*) AS total_sightings
        FROM ufo_sightings
        {filter_query}
        GROUP BY shape
        ORDER BY total_sightings DESC
    """

    ufo_sightings = pd.read_sql_query(query, con=engine)

    fig = px.pie(
        ufo_sightings,
        values='total_sightings',
        names='shape',
        title='Distribution of UFO Shapes',
        labels={'total_sightings': 'count'},
    )

    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': 'white'})

    return fig


if __name__ == '__main__':
    app.run(host=HOST, debug=DEBUG)
