import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import pandas as pd
import requests
import plotly.graph_objects as go

# Function to fetch data from the World Bank API
def fetch_data(country_codes, indicator, start_year, end_year):
    url = f"http://api.worldbank.org/v2/country/{';'.join(country_codes)}/indicator/{indicator}"
    params = {
        'format': 'json',
        'date': f"{start_year}:{end_year}",
        'per_page': 5000
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if len(data) > 1:
            return data[1]
        else:
            print(f"No data found for indicator {indicator}!")
            return []
    else:
        print(f"Failed to fetch data for indicator {indicator}. HTTP Status code: {response.status_code}")
        return []

# Function to process and clean the data
def process_data(raw_data):
    if raw_data:
        df = pd.DataFrame(raw_data)
        df = df[['countryiso3code', 'date', 'value']]
        df.columns = ['Country Code', 'Year', 'Value']
        df.dropna(inplace=True)
        df['Year'] = df['Year'].astype(int)
        df['Value'] = df['Value'].astype(float)
        return df
    else:
        return pd.DataFrame()

# Define parameters
country_codes = ['AFG', 'IND', 'PAK', 'BGD', 'LKA']
indicators = {
    'Population': 'SP.POP.TOTL',
    'Net Migration': 'SM.POP.NETM'
}
start_year = 1960
end_year = 2023

all_data = {}
for name, indicator in indicators.items():
    raw_data = fetch_data(country_codes, indicator, start_year, end_year)
    processed_data = process_data(raw_data)
    all_data[name] = processed_data

if all_data:
    population_df = all_data.get('Population', pd.DataFrame())
    migration_df = all_data.get('Net Migration', pd.DataFrame())
    merged_df = pd.merge(
        population_df, migration_df, 
        on=['Country Code', 'Year'], 
        how='outer', 
        suffixes=('_Population', '_Net Migration')
    )

df = merged_df.copy()

app = dash.Dash(__name__)

# Layout of the dashboard
app.layout = html.Div(
    style={
        "background": "linear-gradient(45deg, #6a11cb, #2575fc)",  # Beautiful gradient
        "fontFamily": "Arial, sans-serif",
        "color": "#fff",
        "padding": "30px",
        "borderRadius": "15px"
    },
    children=[
        html.H1(
            "South Asia Population and Migration Dashboard",
            style={
                "textAlign": "center", 
                "marginBottom": "30px", 
                "color": "#fff", 
                "fontSize": "36px",
                "textShadow": "2px 2px 5px rgba(0, 0, 0, 0.3)"
            }
        ),
        
        # Dropdown to select countries and year range
        html.Div(
            style={"marginBottom": "20px", "textAlign": "center"},
            children=[
                html.Label("Select Countries:", style={"fontWeight": "bold", "marginRight": "10px", "fontSize": "18px"}),
                dcc.Dropdown(
                    id="country-dropdown",
                    options=[
                        {"label": "Afghanistan", "value": "AFG"},
                        {"label": "India", "value": "IND"},
                        {"label": "Pakistan", "value": "PAK"},
                        {"label": "Bangladesh", "value": "BGD"},
                        {"label": "Sri Lanka", "value": "LKA"}
                    ],
                    value=["AFG"],
                    multi=True,
                    clearable=False,
                    style={
                        "width": "50%",
                        "display": "inline-block",
                        "marginTop": "10px",
                        "backgroundColor": "#000000",
                        "color": "#000000",
                        "borderRadius": "10px"
                    }
                ),
                html.Label("Select Year Range:", style={"fontWeight": "bold", "marginTop": "20px", "fontSize": "18px"}),
                dcc.RangeSlider(
                    id="year-range-slider",
                    min=1960,
                    max=2023,
                    step=1,
                    marks={year: str(year) for year in range(1960, 2024, 5)},
                    value=[1960, 2023],  # Default value
                ),
            ]
        ),
        
        # Graphs and Summary section
        html.Div(
            children=[
                html.Div(id="summary-metrics", style={
                    "marginBottom": "30px", 
                    "background": "rgba(0, 0, 0, 0.6)", 
                    "padding": "20px", 
                    "borderRadius": "10px",
                    "fontSize": "18px",
                    "textAlign": "center"
                }),
                dcc.Graph(id="line-plot-population", style={"height": "400px"}),
                dcc.Graph(id="line-plot-migration", style={"height": "400px"}),
                dcc.Graph(id="scatter-plot", style={"height": "400px"}),
                
                # Data Table for displaying filtered data
                html.H3("Filtered Data", style={"textAlign": "center", "marginTop": "20px", "fontSize": "24px"}),
                dash_table.DataTable(
                    id="data-table",
                    style_table={"overflowX": "auto"},
                    style_header={"backgroundColor": "#333", "color": "#fff"},
                    style_data={"backgroundColor": "#444", "color": "#fff"},
                    style_cell={'textAlign': 'center', 'padding': '10px'},
                    page_size=10,
                    export_format="csv",
                    export_headers="display"
                ),
                
                # Export Button
                html.Div(
                    style={"textAlign": "center", "marginTop": "20px"},
                    children=[
                        html.Button(
                            "Export Data as CSV", 
                            id="export-btn", 
                            style={
                                "backgroundColor": "#2575fc", 
                                "color": "#fff", 
                                "padding": "10px 20px", 
                                "border": "none", 
                                "borderRadius": "5px", 
                                "cursor": "pointer"
                            }
                        )
                    ]
                )
            ]
        )
    ]
)

@app.callback(
    [
        Output("line-plot-population", "figure"), 
        Output("line-plot-migration", "figure"), 
        Output("scatter-plot", "figure"),
        Output("data-table", "data"),
        Output("data-table", "columns"),
        Output("summary-metrics", "children")
    ],
    [
        Input("country-dropdown", "value"),
        Input("year-range-slider", "value")
    ]
)
def update_dashboard(selected_countries, selected_year_range):
    filtered_df = df[
        (df["Country Code"].isin(selected_countries)) & 
        (df["Year"] >= selected_year_range[0]) & 
        (df["Year"] <= selected_year_range[1])
    ]
    
    # Line graph for Population
    line_fig_population = px.line(
        filtered_df,
        x="Year",
        y="Value_Population",
        color="Country Code",
        title="Population Over the Years",
        markers=True
    ).update_layout(
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0.1)",
        font={"color": "#fff"},
        hovermode="x unified"
    )
    
    # Line graph for Net Migration
    line_fig_migration = px.line(
        filtered_df,
        x="Year",
        y="Value_Net Migration",
        color="Country Code",
        title="Net Migration Over the Years",
        markers=True
    ).update_layout(
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0.1)",
        font={"color": "#fff"},
        hovermode="x unified"
    )
    
    # Scatter plot for Net Migration vs Population
    scatter_fig = px.scatter(
        filtered_df,
        x="Value_Population",
        y="Value_Net Migration",
        color="Year",
        size="Value_Population",
        title="Net Migration vs. Total Population"
    ).update_layout(
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0.1)",
        font={"color": "#fff"},
        hovermode="closest"
    )
    
    # Data Table
    data = filtered_df.to_dict("records")
    columns = [{"name": col, "id": col} for col in filtered_df.columns]
    
    # Summary Metrics
    summary = html.Div([
        html.P(f"Total Population: {filtered_df['Value_Population'].sum():,.0f}"),
        html.P(f"Average Net Migration: {filtered_df['Value_Net Migration'].mean():,.2f}")
    ])
    
    return line_fig_population, line_fig_migration, scatter_fig, data, columns, summary

if __name__ == "__main__":
    app.run_server(debug=True)






