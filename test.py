import dash
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
from datetime import datetime, timedelta
import math

# Create a pandas dataframe df
df = pd.DataFrame({
    "title": [f"Title {i}" for i in range(100)],
    "contents": [f"Content {i}" for i in range(100)],
    "author": [f"Author {i%10}" for i in range(100)],
    "date": [datetime.now() - timedelta(days=i) for i in range(100)]
})

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

pagination = dbc.Pagination(
    id="pagination",
    size="lg",
    max_value=math.ceil(df.shape[0] / 20),
    active_page=1,
    style={"margin":"20px 0px"}
)

app.layout = html.Div([
    dbc.Input(id="search-box", placeholder="Type something...", type="text"),
    dbc.Button("Search", id='search-button', color="primary", className="mr-1"),
    html.Div(id='table-container'),
    pagination
])

@app.callback(
    Output('pagination', 'active_page'),
    [Input('search-button', 'n_clicks')],
    [State('search-box', 'value')])
def reset_pagination(n_clicks, search_value):
    return 1

@app.callback(
    [Output('table-container', 'children'),
    Output('pagination', 'max_value')],
    [Input('pagination', 'active_page'),
    Input('search-button', 'n_clicks')],
    [State('search-box', 'value')])
def update_table(page_number, n_clicks, search_value):
    if n_clicks is None:
        return [], 1
    else:
        df_search = df[df.apply(lambda row: row.astype(str).str.contains(search_value).any(), axis=1)]
        df_subset = df_search.iloc[(page_number-1)*20:page_number*20]
        table = []
        for _, row in df_subset.iterrows():
            table.append(html.Div([
                html.H3(row['title'], style={'fontWeight': 'bold'}),
                html.P(row['contents']),
                html.Div([
                    html.Div(row['author'], style={'display': 'inline-block'}),
                    html.Div(row['date'].strftime("%Y-%m-%d %H:%M:%S"), style={'display': 'inline-block', 'float': 'right'})
                ])
            ], style={'border': 'solid', 'padding': '10px', 'margin': '10px'}))

        max_pages = math.ceil(df_search.shape[0] / 20)
        return table, max_pages

if __name__ == '__main__':
    app.run_server(debug=True)























# import dash
# import dash_html_components as html
# import dash_bootstrap_components as dbc
# from dash.dependencies import Input, Output
# import pandas as pd
# from datetime import datetime, timedelta
# import math

# # Create a pandas dataframe df
# df = pd.DataFrame({
#     "title": [f"Title {i}" for i in range(100)],
#     "contents": [f"Content {i}" for i in range(100)],
#     "author": [f"Author {i%10}" for i in range(100)],
#     "date": [datetime.now() - timedelta(days=i) for i in range(100)]
# })

# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# pagination = dbc.Pagination(
#     id="pagination",
#     size="lg",
#     max_value=math.ceil(df.shape[0] / 20),  # Correct number of pages
#     active_page=1,
#     style={"margin":"20px 0px"}
# )

# app.layout = html.Div([
#     html.Div(id='table-container'),
#     pagination
# ])

# @app.callback(
#     Output('table-container', 'children'),
#     [Input('pagination', 'active_page')])
# def update_table(page_number):
#     df_subset = df.iloc[(page_number-1)*20:page_number*20]
#     table = []
#     for _, row in df_subset.iterrows():
#         table.append(html.Div([
#             html.H3(row['title'], style={'fontWeight': 'bold'}),
#             html.P(row['contents']),
#             html.Div([
#                 html.Div(row['author'], style={'display': 'inline-block'}),
#                 html.Div(row['date'].strftime("%Y-%m-%d %H:%M:%S"), style={'display': 'inline-block', 'float': 'right'})
#             ])
#         ], style={'border': 'solid', 'padding': '10px', 'margin': '10px'}))
#     return table

# if __name__ == '__main__':
#     app.run_server(debug=True)
















# import dash
# import dash_html_components as html
# import dash_core_components as dcc
# from dash.dependencies import Input, Output, State
# import pandas as pd
# from datetime import datetime, timedelta

# # Create a pandas dataframe df
# df = pd.DataFrame({
#     "title": [f"Title {i}" for i in range(100)],
#     "contents": [f"Content {i}" for i in range(100)],
#     "author": [f"Author {i%10}" for i in range(100)],
#     "date": [datetime.now() - timedelta(days=i) for i in range(100)]
# })

# app = dash.Dash(__name__)

# app.layout = html.Div([
#     html.Div(id='table-container'),
#     html.Div(id='button-container', children=[
#         html.Button('Prev', id='prev-button', n_clicks=0),
#         html.Button('Next', id='next-button', n_clicks=0),
#     ]),
#     html.Div(id='hidden-div', style={'display':'none'})
# ])

# @app.callback(
#     [Output('table-container', 'children'),
#     Output('hidden-div', 'children')],
#     [Input('prev-button', 'n_clicks'),
#      Input('next-button', 'n_clicks')],
#     [State('hidden-div', 'children')])
# def update_table(prev_clicks, next_clicks, page_number):
#     if page_number is None:
#         page_number = 0
#     else:
#         page_number = int(page_number)

#     changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
#     if 'prev-button' in changed_id:
#         page_number = max(0, page_number-1)
#     elif 'next-button' in changed_id:
#         page_number = min(df.shape[0]//20, page_number+1)

#     df_subset = df.iloc[page_number*20:(page_number+1)*20]
#     table = []
#     for _, row in df_subset.iterrows():
#         table.append(html.Div([
#             html.H3(row['title'], style={'fontWeight': 'bold'}),
#             html.P(row['contents']),
#             html.Div([
#                 html.Div(row['author'], style={'display': 'inline-block'}),
#                 html.Div(row['date'].strftime("%Y-%m-%d %H:%M:%S"), style={'display': 'inline-block', 'float': 'right'})
#             ])
#         ], style={'border': 'solid', 'padding': '10px', 'margin': '10px'}))
#     return table, page_number

# if __name__ == '__main__':
#     app.run_server(debug=True)
