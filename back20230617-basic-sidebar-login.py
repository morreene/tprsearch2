from flask import Flask, session
from flask_session import Session
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import pandas as pd
import openai
from openai.embeddings_utils import get_embedding #, cosine_similarity
import pinecone

##### openai
API_KEY = "3842bbdef12e406dbaf407d7a133ee7e"
RESOURCE_ENDPOINT = "https://openai-mais.openai.azure.com/"
openai.api_type = "azure"
openai.api_key = API_KEY
openai.api_base = RESOURCE_ENDPOINT
openai.api_version = "2022-12-01"

###### pinecone
index_name = 'semantic-search-openai'

# initialize connection to pinecone (get API key at app.pinecone.io)
pinecone.init(
    api_key="b5d40c2b-abda-4590-8cb5-06251507c483",
    environment="asia-southeast1-gcp-free"  # find next to api key in console
)

# # check if 'openai' index already exists (only create index if not)
# if index_name not in pinecone.list_indexes():
#     pinecone.create_index(index_name, dimension=1536)
    
# connect to index
index = pinecone.Index(index_name)

##### function search document data with openai embedding
def search_docs(user_query, threshold=0.8):
    xq = get_embedding(
        user_query,
        engine="text-embedding-ada-002" # engine should be set to the deployment name you chose when you deployed the text-embedding-ada-002 (Version 2) model
    )

    res = index.query([xq], top_k=500, include_metadata=True)

    # df["similarities"] = df.ada_v2.apply(lambda x: cosine_similarity(x, embedding))

    # res = df[df['similarities']>threshold].sort_values("similarities", ascending=False)

    data = res.to_dict()
    # Create an empty list to store the transformed data
    transformed_data = []

    # Iterate over the matches and extract relevant information
    for match in data['matches']:
        metadata = match.get('metadata', {})
        row = {
            'id': match['id'],
            'score': match['score'],
            **metadata
        }
        transformed_data.append(row)

    # Create a DataFrame from the transformed data
    df = pd.DataFrame(transformed_data)
    df = df[df['score']>threshold].sort_values("score", ascending=False)
    return df


















# Hardcoded users (for demo purposes)
USERS = {"admin": "admin", "w": "w", "wto": "wto"}

server = Flask(__name__)
server.config['SECRET_KEY'] = 'supersecretkey'
server.config['SESSION_TYPE'] = 'filesystem'

Session(server)

# dash app
external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css']
app = Dash(__name__, server=server, 
        #    external_stylesheets=[dbc.themes.BOOTSTRAP], 
           external_stylesheets = external_stylesheets,
           suppress_callback_exceptions=True
           )

app.title = 'WTO TPR Report Database'
app.index_string = """<!DOCTYPE html>
<html>
    <head>
        <!-- Global site tag (gtag.js) - Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=UA-62289743-10"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'UA-62289743-10');
        </script>

        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""


sidebar_header = dbc.Row([
    # dbc.Col(html.H3("Analytical Database", className="display-logo")),
    html.A([
            dbc.Col(html.Img(src=app.get_asset_url("logo.png"),  width="180px", style={'margin-left':'15px', 'margin-bottom':'50px'})),
            ], href="/page-1",
        ),
    dbc.Col(
        html.Button(
            # use the Bootstrap navbar-toggler classes to style the toggle
            html.Span(className="navbar-toggler-icon"),
            className="navbar-toggler",
            # the navbar-toggler classes don't set color, so we do it here
            style={
                "color": "rgba(0,0,0,.5)",
                "bordercolor": "rgba(0,0,0,.1)",
            },
            id="toggle",
        ),
        # the column containing the toggle will be only as wide as the
        # toggle, resulting in the toggle being right aligned
        width="auto",
        # vertically align the toggle in the center
        align="center",
    ),
])

sidebar = html.Div([
        sidebar_header,
        # we wrap the horizontal rule and short blurb in a div that can be
        # hidden on a small screen
        html.Div(
            [
                # html.Hr(),
                # html.P(
                #     "Download integrated tariff and trade data for research and analysis",
                #     # className="lead",
                # ),
            ],
            id="blurb",
        ),
        # use the Collapse component to animate hiding / revealing links
        dbc.Collapse(
            dbc.Nav(
                [
                    dbc.NavLink("Search", href="/page-1", id="page-1-link"),
                    dbc.NavLink("Q&A", href="/page-2", id="page-2-link"),
                    dbc.NavLink("Reference Tables", href="/page-3", id="page-3-link"),
                    dbc.NavLink("Methodology", href="/page-4", id="page-4-link"),
                    dbc.NavLink("Help", href="/page-5", id="page-5-link"),
                    dbc.NavLink("Logout", href="/logout", active="exact"),  # Add a logout link
                ],
                vertical=True,
                pills=False,
            ),
            id="collapse",
        ),
        html.Div([
                html.P(
                    "V0.5 (20230619)",
                    # className="lead",
                ),
                ],
                id="blurb-bottom",
        ),
    ],
    id="sidebar",
)

content = html.Div(id="page-content")







# this callback uses the current pathname to set the active state of the
# corresponding nav link to true, allowing users to tell see page they are on
@app.callback(
    [Output(f"page-{i}-link", "active") for i in range(1, 6)],
    [Input("url", "pathname")],
)
def toggle_active_links(pathname):
    if pathname == "/":
        # Treat page 1 as the homepage / index
        return True, False, False, False, False
    return [pathname == f"/page-{i}" for i in range(1, 6)]








# # the style arguments for the sidebar. We use position:fixed and a fixed width
# SIDEBAR_STYLE = {
#     "position": "fixed",
#     "top": 0,
#     "left": 0,
#     "bottom": 0,
#     "width": "16rem",
#     "padding": "2rem 1rem",
#     "background-color": "#f8f9fa",
# }

# # the styles for the main content position it to the right of the sidebar and
# # add some padding.
# CONTENT_STYLE = {
#     "margin-left": "18rem",
#     "margin-right": "2rem",
#     "padding": "2rem 1rem",
# }

# sidebar = html.Div(
#     [
#         html.H2("Sidebar", className="display-4"),
#         html.Hr(),
#         html.P(
#             "A simple sidebar layout with navigation links", className="lead"
#         ),
#         dbc.Nav(
#             [
#                 dbc.NavLink("Home", href="/", active="exact"),
#                 dbc.NavLink("Page 1", href="/page-1", active="exact"),
#                 dbc.NavLink("Page 2", href="/page-2", active="exact"),
#                 dbc.NavLink("Logout", href="/logout", active="exact"),  # Add a logout link
#             ],
#             vertical=True,
#             pills=True,
#         ),
#     ],
#     style=SIDEBAR_STYLE,
# )

# content = html.Div(id="page-content", style=CONTENT_STYLE)












app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Location(id='logout-url', refresh=False),  # Added logout URL component

    # login facet
    dbc.Container(
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H3("Login", className="card-title"),
                            dbc.Form(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label("Username", html_for="username"),
                                                    dbc.Input(
                                                        type="text",
                                                        id="username",
                                                        placeholder="Enter your username",
                                                    ),
                                                ],
                                                className="mb-3",
                                            )
                                        ]
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label("Password", html_for="password"),
                                                    dbc.Input(
                                                        type="password",
                                                        id="password",
                                                        placeholder="Enter your password",
                                                    ),
                                                ],
                                                className="mb-3",
                                            )
                                        ]
                                    ),
                                    dbc.Button(id='login-button', children='Login', n_clicks=0, color="primary", className="mt-3"),
                                ]
                            ),
                        ]
                    ),
                    className="text-center",
                    style={"width": "400px", "margin": "auto"},
                ),
                width=6,
                className="mt-5",
            )
        ), id='login-facet',
    ),

    # dbc.Input(id='username', placeholder='username', type='text'),
    # dbc.Input(id='password', placeholder='password', type='password'),
    # dbc.Button(id='login-button', children='Login', n_clicks=0),

    html.Div([sidebar, content], id='page-layout', style={'display': 'none'}),
])

@app.callback(
    # Output('username', 'style'),
    # Output('password', 'style'),
    # Output('login-button', 'style'),
    Output('login-facet', 'style'),
    Output('page-layout', 'style'),
    [Input('login-button', 'n_clicks')],
    [State('username', 'value'), State('password', 'value')]
)
def update_output(n_clicks, username, password):
    if n_clicks > 0:
        if username in USERS and USERS[username] == password:
            session['authed'] = True
    if session.get('authed', False):
        # return {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'block'}
        return  {'display': 'none'}, {'display': 'block'}
    else:
        # return {}, {}, {}, {'display': 'none'}
        return {}, {'display': 'none'}

@app.callback(Output("page-content", "children"),
              Output("logout-url", "pathname"),  # Added callback output for logout URL
              [Input("url", "pathname"), Input("logout-url", "pathname")])
def render_page_content(pathname, logout_pathname):
    if logout_pathname == "/logout":  # Handle logout
        session.pop('authed', None)
        return dcc.Location(pathname="/login", id="redirect-to-login"), "/logout"
    if pathname == "/":
        # return html.P("This is the content of the home page!"), pathname
        return dcc.Location(pathname="/page-1", id="redirect-to-login"), "/page-1"    
    elif pathname == "/login":
        # return html.P("This is the content of page after login"), '/page-1'
        return dcc.Location(pathname="/page-1", id="redirect-to-login"), "/page-1"
    elif pathname == "/page-1":
        return html.P("This is the content of page 1. Yay!"), pathname
    elif pathname == "/page-2":
        return html.P("Oh cool, this is page 2!"), pathname
    else:
        return html.P("404: Not found"), pathname
        # return dbc.JumbHotron(
        #     [
        #         html.H1("404: Not found", className="text-danger"),
        #         html.Hr(),
        #         html.P(f"The pathname {pathname} was not recognised..."),
        #     ]
        # ), pathname
























# app
@app.callback(
    Output("collapse", "is_open"),
    [Input("toggle", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open






if __name__ == '__main__':
    app.run_server(port=8888)
