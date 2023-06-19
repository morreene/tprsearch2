import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
import pandas as pd
import urllib.parse

# Creating a dataframe with some dummy data
df = pd.DataFrame({
    'Name': ['Alice', 'Bob', 'Charlie', 'Dave'],
    'Age': [25, 31, 35, 19]
})

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Button('Load data', id='load-button'),
    html.Div(id='output-container-button'),
    html.A('Download CSV', id='download-link', download="rawdata.csv", href="", target="_blank", style={'display': 'none'}),
    dash_table.DataTable(id='table')
])

@app.callback(
    Output('table', 'data'),
    Output('output-container-button', 'children'),
    Output('download-link', 'href'),
    Output('download-link', 'style'),
    Input('load-button', 'n_clicks')
)
def update_output(n_clicks):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    else:
        csv_string = df.to_csv(index=False, encoding='utf-8')
        csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
        return df.to_dict('records'), f"Total number of rows: {len(df)}", csv_string, {'display': 'block'}

if __name__ == '__main__':
    app.run_server(debug=True)
