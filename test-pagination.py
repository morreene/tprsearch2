import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd

# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout
app.layout = dbc.Container([
    dbc.Input(id="input", type="text", placeholder="Search"),
    dbc.Button("Search", id="search-button", color="primary", className="mr-1"),
    html.Div(id='content', children=[]),
    dbc.Pagination(id='pagination', active_page=1, max_value=1, className='my-4')
], fluid=True)

@app.callback(
    [Output('content', 'children'),
     Output('pagination', 'max_value'),
     Output('pagination', 'active_page')],
    [Input('pagination', 'active_page'),
     Input("search-button", "n_clicks")],
    [State('input', 'value')]
)
def update_content(active_page, n_clicks, search_term):
    ctx = dash.callback_context

    # Search function to be defined here
    # I'm using a dictionary for the demonstration purpose
    results = {f'record{i}': i for i in range(500)}
    df = pd.DataFrame(list(results.items()), columns=['Key', 'Value'])

    if not ctx.triggered:
        # if nothing has triggered the callback yet, we display no results
        data_slice = pd.DataFrame(columns=['Key', 'Value'])
    elif "search-button" in ctx.triggered[0]['prop_id']:
        # if the search button triggered the callback, we reset to page 1
        active_page = 1
        data_slice = df.iloc[:50]
    else:
        start = 50 * (active_page - 1)  # Start of slice
        end = start + 50  # End of slice
        data_slice = df.iloc[start:end]  # Slice of 50 rows

    children = [html.Div(f'{row[1]["Key"]}: {row[1]["Value"]}') for row in data_slice.iterrows()]
    max_pages = len(df) // 50 if len(df) % 50 == 0 else (len(df) // 50) + 1

    return children, max_pages, active_page

if __name__ == "__main__":
    app.run_server(debug=True)