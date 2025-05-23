import pandas as pd
from dash import Dash, State, dcc, html, Input, Output, dash_table, callback, callback_context
import plotly.express as px
from dash_auth import BasicAuth
import dash_bootstrap_components as dbc
import os
from datetime import datetime, timedelta
import numpy as np
import base64
import io
import pycountry_convert as pc
from dash.exceptions import PreventUpdate
import pdfkit
from flask import send_file
import tempfile

# Initialize the app
app = Dash(__name__, 
          external_stylesheets=[dbc.themes.FLATLY],
          suppress_callback_exceptions=True,
          meta_tags=[{'name': 'viewport', 
                     'content': 'width=device-width, initial-scale=1.0'}])
app.server.secret_key = 'AlSolutions-Secret-Key-123' 

# Simple authentication setup
VALID_USERNAME_PASSWORD_PAIRS = {
    "admin": "pass12345678",
    "analyst": "DataInsights2024"
}
auth = BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)

# Function to get continent from country
def country_to_continent(country_name):
    try:
        country_alpha2 = pc.country_name_to_country_alpha2(country_name)
        continent_code = pc.country_alpha2_to_continent_code(country_alpha2)
        continent_name = pc.convert_continent_code_to_continent_name(continent_code)
        return continent_name
    except:
        return 'Unknown'

# Load and process data
def load_data():
    # Specify the exact path to your dataset
    data_path = r'C:\Users\PC\Desktop\PD\assignmet\web_server_logs.csv'
    
    try:
        df = pd.read_csv(data_path)
        df = df.rename(columns={
            'Time': 'time_str',
            'IP Address': 'ip',
            'URL/Path': 'path',
            'Status Code': 'status_code',
            'Country': 'country',
            'Request Type': 'request_type',
            'Method': 'http_method'
        })
        
        date_range = pd.date_range(end=datetime.now(), periods=30).date
        df['date'] = np.random.choice(date_range, size=len(df))
        df['timestamp'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time_str'])
        df = df.drop(['time_str', 'date'], axis=1)
        
        if 'Continent' in df.columns:
            df = df.rename(columns={'Continent': 'continent'})
        else:
            df['continent'] = df['country'].apply(country_to_continent)
        
        df['request_category'] = df['path'].apply(lambda x: 
            'Job Request' if '/job' in x.lower() else
            'Demo Request' if '/demo' in x.lower() else
            'Event Inquiry' if '/event' in x.lower() else
            'AI Assistant' if '/ai' in x.lower() or '/virtualassistant' in x.lower() else
            'Prototype Info' if '/prototype' in x.lower() else
            'Other'
        )
        
        required_columns = ['timestamp', 'ip', 'path', 'status_code', 'country', 'request_type', 'continent', 'request_category']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
                
        return df
        
    except Exception as e:
        print(f"Error loading data: {e}")
        num_records = 1000
        start_date = datetime.now() - timedelta(days=30)
        
        df = pd.DataFrame({
            'timestamp': [start_date + timedelta(seconds=np.random.randint(0, 30*24*60*60)) 
                         for _ in range(num_records)],
            'ip': [f"192.168.{np.random.randint(1,5)}.{np.random.randint(1,255)}" 
                   for _ in range(num_records)],
            'path': np.random.choice(
                ['/demo', '/job/apply', '/events', '/virtualassistant.php', '/prototype', '/index.html'],
                size=num_records,
                p=[0.3, 0.25, 0.2, 0.15, 0.05, 0.05]
            ),
            'status_code': np.random.choice(
                [200, 302, 304, 400, 404, 500],
                size=num_records,
                p=[0.7, 0.15, 0.05, 0.04, 0.04, 0.02]
            ),
            'country': np.random.choice(
                ['United States', 'China', 'India', 'Brazil', 'Germany', 
                 'United Kingdom', 'France', 'Japan', 'Nigeria', 'South Africa'],
                size=num_records
            ),
            'request_type': np.random.choice(
                ['Demo Request', 'Job Application', 'Event Inquiry', 
                 'AI Assistant Inquiry', 'Prototype Info', None],
                size=num_records,
                p=[0.3, 0.25, 0.2, 0.15, 0.05, 0.05]
            ),
            'http_method': np.random.choice(
                ['GET', 'POST', 'PUT', 'DELETE'],
                size=num_records,
                p=[0.85, 0.12, 0.02, 0.01]
            )
        })
        
        df['continent'] = df['country'].apply(country_to_continent)
        df['request_category'] = df['path'].apply(lambda x: 
            'Job Request' if '/job' in x.lower() else
            'Demo Request' if '/demo' in x.lower() else
            'Event Inquiry' if '/event' in x.lower() else
            'AI Assistant' if '/virtualassistant' in x.lower() else
            'Prototype Info' if '/prototype' in x.lower() else
            'Other'
        )
        
        print("Using sample data as fallback")
        return df

# Load the data
df = load_data()

# Custom styles
UPLOAD_STYLE = {
    'width': '100%',
    'height': '60px',
    'lineHeight': '60px',
    'borderWidth': '1px',
    'borderStyle': 'dashed',
    'borderRadius': '5px',
    'textAlign': 'center',
    'margin': '10px'
}

CARD_STYLE = {
    'padding': '20px',
    'margin': '10px',
    'borderRadius': '5px',
    'boxShadow': '0 4px 6px 0 rgba(0, 0, 0, 0.1)'
}

# App layout
app.layout = dbc.Container([
    # Header with logo and title
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1("Al-Solutions", className="display-4"),
                html.P("Web Analytics Dashboard", className="lead")
            ], style={'textAlign': 'center', 'margin': '30px 0'})
        ])
    ]),
    
    # Upload and filters card
    dbc.Card([
        dbc.CardBody([
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    html.I(className="fas fa-cloud-upload-alt mr-2"),
                    'Drag and Drop or ',
                    html.A('Select CSV Log File', className="font-weight-bold")
                ]),
                style=UPLOAD_STYLE,
                multiple=False,
                accept='.csv'
            ),
            
            dbc.Row([
                dbc.Col(
                    dcc.Dropdown(
                        id='continent-filter',
                        options=[{'label': 'All Continents', 'value': 'All'}] + 
                               [{'label': c, 'value': c} for c in sorted(df['continent'].unique())],
                        value='All',
                        placeholder="Filter by Continent",
                        className="mb-3"
                    ),
                    md=3
                ),
                
                dbc.Col(
                    dcc.Dropdown(
                        id='country-filter',
                        options=[{'label': 'All Countries', 'value': 'All'}],
                        value='All',
                        placeholder="Filter by Country",
                        className="mb-3"
                    ),
                    md=3
                ),
                
                dbc.Col(
                    dcc.Dropdown(
                        id='request-category-filter',
                        options=[{'label': 'All Categories', 'value': 'All'}] + 
                               [{'label': r, 'value': r} for r in sorted(df['request_category'].unique())],
                        value='All',
                        placeholder="Filter by Request Category",
                        className="mb-3"
                    ),
                    md=3
                ),
                
                dbc.Col(
                    dcc.DatePickerRange(
                        id='date-range',
                        min_date_allowed=df['timestamp'].min(),
                        max_date_allowed=df['timestamp'].max(),
                        start_date=df['timestamp'].min(),
                        end_date=df['timestamp'].max(),
                        display_format='YYYY-MM-DD',
                        className="mb-3"
                    ),
                    md=3
                )
            ])
        ])
    ], style=CARD_STYLE),
    
    # Visualization tabs
    dbc.Tabs([
        dbc.Tab(label="🌍 Geographic Analysis", tabClassName="font-weight-bold", children=[
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(dcc.Graph(id='continent-chart')), 
                        dbc.Col(dcc.Graph(id='country-map'))
                    ]),
                    dbc.Row(
                        dbc.Col(
                            dbc.ButtonGroup([
                                dbc.Button("Export as CSV", id="export-geo-csv-btn", color="primary"),
                                dbc.Button("Export as PDF", id="export-geo-pdf-btn", color="secondary")
                            ], className="mt-3"),
                            width={"size": 6, "offset": 3},
                            className="text-center"
                        )
                    )
                ])
            ], style=CARD_STYLE)
        ]),
        
        dbc.Tab(label="📈 Temporal Analysis", tabClassName="font-weight-bold", children=[
            dbc.Card([
                dbc.CardBody([
                    dbc.Row(dbc.Col(dcc.Graph(id='requests-over-time'))),
                    dbc.Row([
                        dbc.Col(dcc.Graph(id='status-codes')), 
                        dbc.Col(dcc.Graph(id='request-breakdown'))
                    ]),
                    dbc.Row(
                        dbc.Col(
                            dbc.ButtonGroup([
                                dbc.Button("Export as CSV", id="export-temporal-csv-btn", color="primary"),
                                dbc.Button("Export as PDF", id="export-temporal-pdf-btn", color="secondary")
                            ], className="mt-3"),
                            width={"size": 6, "offset": 3},
                            className="text-center"
                        )
                    )
                ])
            ], style=CARD_STYLE)
        ])
    ], className="mt-4"),
    
    # Hidden components
    dcc.Download(id="download-csv"),
    dcc.Store(id='filtered-data-store'),
    dcc.Store(id='geo-figures-store'),
    dcc.Store(id='temp-figures-store')
], fluid=True)

# Update country options based on continent selection
@app.callback(
    Output('country-filter', 'options'),
    Input('continent-filter', 'value')
)
def update_country_options(selected_continent):
    if selected_continent == 'All':
        countries = sorted(df['country'].unique())
    else:
        countries = sorted(df[df['continent'] == selected_continent]['country'].unique())
    
    return [{'label': 'All Countries', 'value': 'All'}] + [{'label': c, 'value': c} for c in countries]

# Main dashboard update callback
@app.callback(
    [Output('continent-chart', 'figure'),
     Output('country-map', 'figure'),
     Output('requests-over-time', 'figure'),
     Output('status-codes', 'figure'),
     Output('request-breakdown', 'figure'),
     Output('filtered-data-store', 'data'),
     Output('geo-figures-store', 'data'),
     Output('temp-figures-store', 'data')],
    [Input('continent-filter', 'value'),
     Input('country-filter', 'value'),
     Input('request-category-filter', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_dashboard(continent, country, request_category, start_date, end_date, upload_contents, filename):
    global df
    
    ctx = callback_context
    triggered_prop_id = ctx.triggered[0]['prop_id'] if ctx.triggered else None
    
    if upload_contents and triggered_prop_id == 'upload-data.contents':
        content_type, content_string = upload_contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            new_df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            new_df = new_df.rename(columns={
                'Time': 'time_str',
                'IP Address': 'ip',
                'URL/Path': 'path',
                'Status Code': 'status_code',
                'Country': 'country',
                'Request Type': 'request_type',
                'Method': 'http_method'
            })
            
            date_range = pd.date_range(end=datetime.now(), periods=30).date
            new_df['date'] = np.random.choice(date_range, size=len(new_df))
            new_df['timestamp'] = pd.to_datetime(new_df['date'].astype(str) + ' ' + new_df['time_str'])
            new_df = new_df.drop(['time_str', 'date'], axis=1)
            
            if 'Continent' in new_df.columns:
                new_df = new_df.rename(columns={'Continent': 'continent'})
            else:
                new_df['continent'] = new_df['country'].apply(country_to_continent)
            
            new_df['request_category'] = new_df['path'].apply(lambda x: 
                'Job Request' if '/job' in x.lower() else
                'Demo Request' if '/demo' in x.lower() else
                'Event Inquiry' if '/event' in x.lower() else
                'AI Assistant' if '/ai' in x.lower() or '/virtualassistant' in x.lower() else
                'Prototype Info' if '/prototype' in x.lower() else
                'Other'
            )
            
            df = new_df
            
        except Exception as e:
            print(f"Error processing uploaded file: {e}")
    
    filtered_df = df.copy()
    if continent != 'All':
        filtered_df = filtered_df[filtered_df['continent'] == continent]
    if country != 'All':
        filtered_df = filtered_df[filtered_df['country'] == country]
    if request_category != 'All':
        filtered_df = filtered_df[filtered_df['request_category'] == request_category]
    
    filtered_df = filtered_df[
        (filtered_df['timestamp'] >= start_date) & 
        (filtered_df['timestamp'] <= end_date)
    ]
    
    # Continent bar chart
    continent_df = filtered_df.groupby('continent').size().reset_index(name='count')
    continent_fig = px.bar(
        continent_df,
        x='continent',
        y='count',
        title='Requests by Continent',
        color='count',
        color_continuous_scale='Viridis',
        text='count'
    )
    continent_fig.update_traces(texttemplate='%{text:,d}', textposition='outside')
    continent_fig.update_layout(
        xaxis_title='Continent', 
        yaxis_title='Number of Requests',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Country map
    country_df = filtered_df.groupby('country').size().reset_index(name='count')
    country_fig = px.choropleth(
        country_df,
        locations='country',
        locationmode='country names',
        color='count',
        title='Requests by Country',
        color_continuous_scale='Viridis',
        hover_data={'country': True, 'count': ':,d'}
    )
    country_fig.update_layout(
        geo=dict(showframe=False, showcoastlines=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Time series
    sales_df = filtered_df[filtered_df['request_category'].isin(['Job Request', 'Demo Request'])]
    time_df = sales_df.groupby([pd.Grouper(key='timestamp', freq='D'), 'request_category']).size().reset_index(name='count')
    time_fig = px.line(
        time_df,
        x='timestamp',
        y='count',
        color='request_category',
        title='Daily Sales Performance Metrics',
        labels={'count': 'Number of Requests', 'timestamp': 'Date', 'request_category': 'Request Type'}
    )
    time_fig.update_xaxes(rangeslider_visible=True)
    time_fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Status codes
    status_fig = px.pie(
        filtered_df,
        names='status_code',
        title='Status Code Distribution',
        hole=0.3
    )
    status_fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Request categories
    request_fig = px.bar(
        filtered_df.groupby('request_category').size().reset_index(name='count'),
        x='request_category',
        y='count',
        title='Request Category Distribution',
        text='count',
        color='request_category'
    )
    request_fig.update_traces(texttemplate='%{text:,d}', textposition='outside')
    request_fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Store figures for PDF export
    geo_figures = {
        'continent': continent_fig.to_dict(),
        'country': country_fig.to_dict()
    }
    
    temp_figures = {
        'timeline': time_fig.to_dict(),
        'status': status_fig.to_dict(),
        'requests': request_fig.to_dict()
    }
    
    return (
        continent_fig, 
        country_fig, 
        time_fig, 
        status_fig, 
        request_fig,
        filtered_df.to_dict('records'),
        geo_figures,
        temp_figures
    )

# CSV Export Callbacks
@app.callback(
    Output("download-csv", "data"),
    [Input("export-geo-csv-btn", "n_clicks"),
     Input("export-temporal-csv-btn", "n_clicks")],
    [State('filtered-data-store', 'data')],
    prevent_initial_call=True
)
def export_csv(geo_clicks, temp_clicks, data):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    df = pd.DataFrame(data)
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'export-geo-csv-btn':
        geo_data = df.groupby(['continent', 'country', 'request_category']).size().reset_index(name='count')
        return dcc.send_data_frame(
            geo_data.to_csv,
            "geographic_analysis.csv",
            index=False
        )
    elif button_id == 'export-temporal-csv-btn':
        time_data = df.groupby([
            pd.Grouper(key='timestamp', freq='D'),
            'request_category'
        ]).size().reset_index(name='count')
        return dcc.send_data_frame(
            time_data.to_csv,
            "temporal_analysis.csv",
            index=False
        )

# PDF Export Callbacks
@app.callback(
    Output("download-csv", "data", allow_duplicate=True),
    [Input("export-geo-pdf-btn", "n_clicks"),
     Input("export-temporal-pdf-btn", "n_clicks")],
    [State('geo-figures-store', 'data'),
     State('temp-figures-store', 'data')],
    prevent_initial_call=True
)
def export_pdf(geo_clicks, temp_clicks, geo_figures, temp_figures):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Create a temporary HTML file
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp_html:
        if button_id == 'export-geo-pdf-btn':
            html_content = f"""
            <html>
                <head>
                    <title>Geographic Analysis Report</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; }}
                        .page {{ page-break-after: always; }}
                        h1 {{ color: #2c3e50; }}
                        .chart {{ width: 100%; height: 600px; }}
                    </style>
                </head>
                <body>
                    <h1>Geographic Analysis Report</h1>
                    <div class="page">
                        <h2>Requests by Continent</h2>
                        <div id="continent-chart" class="chart"></div>
                    </div>
                    <div class="page">
                        <h2>Requests by Country</h2>
                        <div id="country-map" class="chart"></div>
                    </div>
                    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                    <script>
                        Plotly.newPlot('continent-chart', {geo_figures['continent']});
                        Plotly.newPlot('country-map', {geo_figures['country']});
                    </script>
                </body>
            </html>
            """
        elif button_id == 'export-temporal-pdf-btn':
            html_content = f"""
            <html>
                <head>
                    <title>Temporal Analysis Report</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; }}
                        .page {{ page-break-after: always; }}
                        h1 {{ color: #2c3e50; }}
                        .chart {{ width: 100%; height: 600px; }}
                    </style>
                </head>
                <body>
                    <h1>Temporal Analysis Report</h1>
                    <div class="page">
                        <h2>Daily Sales Performance</h2>
                        <div id="timeline-chart" class="chart"></div>
                    </div>
                    <div class="page">
                        <h2>Status Code Distribution</h2>
                        <div id="status-chart" class="chart"></div>
                    </div>
                    <div class="page">
                        <h2>Request Category Distribution</h2>
                        <div id="requests-chart" class="chart"></div>
                    </div>
                    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                    <script>
                        Plotly.newPlot('timeline-chart', {temp_figures['timeline']});
                        Plotly.newPlot('status-chart', {temp_figures['status']});
                        Plotly.newPlot('requests-chart', {temp_figures['requests']});
                    </script>
                </body>
            </html>
            """
        
        tmp_html.write(html_content.encode('utf-8'))
        tmp_html_path = tmp_html.name
    
    # Convert HTML to PDF
    pdf_path = tmp_html_path.replace('.html', '.pdf')
    try:
        pdfkit.from_file(tmp_html_path, pdf_path)
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        print(f"Error generating PDF: {e}")
        raise PreventUpdate

if __name__ == '__main__':
    app.run(debug=True)
