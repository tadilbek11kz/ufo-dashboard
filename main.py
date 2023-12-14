import pandas as pd
import plotly.express as px
# import folium
from sqlalchemy import create_engine
from dash import Dash, html, dcc, callback, Output, Input
from dash_daq import BooleanSwitch

pd.options.plotting.backend = "plotly"

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)

engine = create_engine('postgresql://postgres:postgres@10.16.121.111:5432/ufo')

cities = pd.read_sql_query('SELECT DISTINCT city FROM ufo_sightings', con=engine)
cities = sorted([city.capitalize() for city in cities['city'].tolist()])
shapes = pd.read_sql_query('SELECT DISTINCT shape FROM ufo_sightings', con=engine).sort_values(by='shape')['shape'].tolist()
weather_condition = pd.read_sql_query('SELECT DISTINCT label FROM weather', con=engine).sort_values(by='label')['label'].tolist()

# ufo_sightings = pd.read_sql_query('SELECT * FROM ufo_sightings', con=engine)
# weather = pd.read_sql_query('SELECT * FROM weather', con=engine)

app.layout = html.Div(children=[
    html.Div(className='row', children=[
        html.H1(children='UFO Sightings (GROUP F)', style={'textAlign': 'center'}),
    ], style={'margin': '10px'}),

    html.Div(children=[
        html.Div(className='four columns', children=[
            dcc.Dropdown(cities, None, id='graph-0--city-selection'),
        ]),
        html.Div(children=[
            BooleanSwitch(id='graph-0--day-switch', on=False, color='black')
        ]),
        html.Div(children=[
            BooleanSwitch(id='graph-0--log', on=False, color='black')
        ]),
    ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'flex-end'}),

    html.Div(className='row', children=[
        html.Div(className='twelve columns', children=[
            dcc.Graph(id='graph-0'),
        ]),
    ]),

    html.Div(children=[
        html.Div(className='four columns', children=[
            dcc.Dropdown(cities, None, id='graph-1--city-selection'),
        ]),
        html.Div(children=[
            BooleanSwitch(id='graph-1--day-switch', on=False, color='black')
        ]),
        html.Div(children=[
            BooleanSwitch(id='graph-1--log', on=False, color='black')
        ]),
    ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'flex-end'}),

    html.Div(className='row', children=[
        html.Div(className='twelve columns', children=[
            dcc.Graph(id='graph-1'),
        ]),
    ]),

    html.Div(children=[
        html.Div(className='four columns', children=[
            dcc.Dropdown(cities, None, id='graph-2--city-selection'),
        ]),
        html.Div(children=[
            BooleanSwitch(id='graph-2--day-switch', on=False, color='black')
        ]),
        html.Div(children=[
            BooleanSwitch(id='graph-2--log', on=False, color='black')
        ]),
    ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'flex-end'}),

    html.Div(className='row', children=[
        html.Div(className='twelve columns', children=[
            dcc.Graph(id='graph-2'),
        ]),
    ]),

    html.Div(children=[
        html.Div(className='four columns', children=[
            dcc.Dropdown(cities, None, id='graph-3--city-selection'),
        ]),
        html.Div(children=[
            BooleanSwitch(id='graph-3--day-switch', on=False, color='black')
        ]),
    ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'flex-end'}),

    html.Div(className='row', children=[
        html.Div(className='twelve columns', children=[
            dcc.Graph(id='graph-3'),
        ]),
    ]),

    html.Div(children=[
        html.Div(className='four columns', children=[
            dcc.Dropdown(cities, None, id='graph-4--city-selection'),
        ]),
        html.Div(children=[
            BooleanSwitch(id='graph-4--day-switch', on=False, color='black')
        ]),
    ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'flex-end'}),

    html.Div(className='row', children=[
        html.Div(className='six columns', children=[
            dcc.Graph(id='graph-4'),
        ]),
        html.Div(className='six columns', children=[
            dcc.Graph(id='graph-5'),
        ]),
    ]),
])


@callback(
    Output('graph-0', 'figure'),
    Input('graph-0--city-selection', 'value'),
    Input('graph-0--day-switch', 'on'),
    Input('graph-0--log', 'on')
)
def update_graph(value, on, log):
    filters = {
        'city': value.lower() if value else '',
        'daytime': 'night' if on else 'day'
    }

    filter_query = [f'{key} = \'{value}\'' for key, value in filters.items() if value != '']

    if len(filter_query) > 0:
        filter_query = 'WHERE ' + ' AND '.join(filter_query)

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

    return fig


@callback(
    Output('graph-1', 'figure'),
    Input('graph-1--city-selection', 'value'),
    Input('graph-1--day-switch', 'on'),
    Input('graph-1--log', 'on')
)
def update_graph(value, on, log):
    filters = {
        'city': value.lower() if value else '',
        'daytime': 'night' if on else 'day'
    }

    filter_query = [f'{key} = \'{value}\'' for key, value in filters.items() if value != '']

    if len(filter_query) > 0:
        filter_query = 'WHERE ' + ' AND '.join(filter_query)

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
                    LIMIT 7
                ) AS top_shapes
            ) THEN ufo_sightings.shape
            END AS shape,
            weather.label,
            COUNT(DISTINCT ufo_sightings.index) AS total_sightings
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
        y='total_sightings',
        log_y=log,
        color='shape',
        category_orders={'shape': shapes, 'label': weather_condition},
        labels={'total_sightings': 'count', 'label': 'weather'},
        title='Total UFO Sightings by Shape and Weather',
        barmode='group'
    )
    fig.update_layout(xaxis_title='Weather condition', yaxis_title="Number of UFO")

    return fig


@callback(
    Output('graph-2', 'figure'),
    Input('graph-2--city-selection', 'value'),
    Input('graph-2--day-switch', 'on'),
    Input('graph-2--log', 'on')
)
def update_graph(value, on, log):
    filters = {
        'city': value.lower() if value else '',
        'daytime': 'night' if on else 'day'
    }

    filter_query = [f'{key} = \'{value}\'' for key, value in filters.items() if value != '']

    if len(filter_query) > 0:
        filter_query = 'WHERE ' + ' AND '.join(filter_query)

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
                    LIMIT 7
                ) AS top_shapes
            ) THEN ufo_sightings.shape
            END AS shape,
            weather.label,
    	    SUM(ufo_sightings.duration) / COUNT(DISTINCT ufo_sightings.index) AS total_duration
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
        y='total_duration',
        log_y=log,
        category_orders={'shape': shapes, 'label': weather_condition},
        color='shape',
        labels={'total_duration': 'duration'},
        title='Total UFO Duration by Shape and Weather',
        barmode='group'
    )
    fig.update_layout(xaxis_title='Weather condition', yaxis_title="Total Duration (seconds)")

    return fig


@callback(
    Output('graph-3', 'figure'),
    Input('graph-3--city-selection', 'value'),
    Input('graph-3--day-switch', 'on')
)
def update_graph(value, on):
    filters = {
        'city': value.lower() if value else '',
        'daytime': 'night' if on else 'day'
    }

    filter_query = [f'{key} = \'{value}\'' for key, value in filters.items() if value != '']

    if len(filter_query) > 0:
        filter_query = 'WHERE ' + ' AND '.join(filter_query)

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

    return fig


@callback(
    Output('graph-4', 'figure'),
    Input('graph-4--city-selection', 'value'),
    Input('graph-4--day-switch', 'on')
)
def update_graph(value, on):
    filters = {
        'city': value.lower() if value else '',
        'daytime': 'night' if on else 'day'
    }

    filter_query = [f'{key} = \'{value}\'' for key, value in filters.items() if value != '']

    if len(filter_query) > 0:
        filter_query = 'WHERE ' + ' AND '.join(filter_query)

    query = f"""
        SELECT lat, lng, COUNT(*) AS total_sightings
        FROM ufo_sightings
        {filter_query}
        GROUP BY lat, lng
        ORDER BY total_sightings DESC
    """

    ufo_sightings = pd.read_sql_query(query, con=engine)
    fig = px.density_mapbox(ufo_sightings, lat='lat', lon='lng', z='total_sightings', labels={'total_sightings': 'count'}, radius=10, center=dict(lat=39.8283, lon=-98.5795), zoom=3, mapbox_style="open-street-map")
    # fig = px.choropleth(ufo_sightings, locations="state", locationmode="USA-states", color="total_sightings", scope='usa', color_continuous_scale=px.colors.sequential.Oranges)

    return fig


@callback(
    Output('graph-5', 'figure'),
    Input('graph-4--city-selection', 'value'),
    Input('graph-4--day-switch', 'on')
)
def update_graph(value, on):
    df = pd.read_csv('population.csv')

    # fig = px.density_mapbox(ufo_sightings, lat='lat', lon='lng', z='total_sightings', labels={'total_sightings': 'count'}, radius=10, center=dict(lat=39.8283, lon=-98.5795), zoom=3, mapbox_style="open-street-map")
    fig = px.choropleth(df, locations="code", locationmode="USA-states", color="population", scope='usa', color_continuous_scale=px.colors.sequential.Oranges)

    return fig


if __name__ == '__main__':
    app.run(host="10.16.121.111", debug=True)
