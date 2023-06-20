from flask import Flask, session
from flask_session import Session
from dash import Dash, dcc, html
# import dash
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
# to delete dash_table
from dash import html, dcc, dash_table
import urllib.parse

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
def search_docs(user_query, top=200):
    xq = get_embedding(
        user_query,
        engine="text-embedding-ada-002" # engine should be set to the deployment name you chose when you deployed the text-embedding-ada-002 (Version 2) model
    )

    res = index.query([xq], top_k=top, include_metadata=True)

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
    # print(df.dtypes)
    
    df['date'] = df['date'].astype(str)
    
    return df


##### functions for retrieval augmented generative question answering
def complete(prompt, engine = 'text-davinci-003'):
    prompt = 'Please answer the question with no more than 200 words: ' + prompt
    # engine = 'text-ada-001'
    # engine = 'text-curie-001'
    # engine = 'text-davinci-003'
    # engine = 'gpt-35-turbo'
    
    # query text-davinci-003
    res = openai.Completion.create(
        engine=engine,        
        prompt=prompt,
        temperature=0,
        max_tokens=400,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    # res = openai.Completion.create(engine=engine, prompt=prompt, max_tokens=200)
    return res['choices'][0]['text'].strip()








limit = 10000
def retrieve(query):
    res = openai.Embedding.create(
        input=[query],
        engine='text-embedding-ada-002'
    )

    # retrieve from Pinecone
    xq = res['data'][0]['embedding']

    # get relevant contexts
    res = index.query(xq, top_k=10, include_metadata=True)
    contexts = [
        x['metadata']['text'] for x in res['matches']
    ]

    # build our prompt with the retrieved contexts included
    prompt_start = (
        "Answer the question based on the context below. \n\n"+
        "Context:\n"
    )
    prompt_end = (
        f"\n\nQuestion: {query}\nAnswer:"
    )
    # append contexts until hitting limit
    for i in range(1, len(contexts)):
        if len("\n\n---\n\n".join(contexts[:i])) >= limit:
            prompt = (
                prompt_start +
                "\n\n---\n\n".join(contexts[:i-1]) +
                prompt_end
            )
            break
        elif i == len(contexts)-1:
            prompt = (
                prompt_start +
                "\n\n---\n\n".join(contexts) +
                prompt_end
            )
    return prompt



#################################################
#####      Load data 
#################################################

with open('data/about.md', 'r') as markdown_file:
    markdown_about = markdown_file.read()

matrix = pd.read_pickle("data/tpr_matrix.pickle")
# matrix.columns = matrix.columns.droplevel()
matrix.index.name = None

# print([{"name": str(i), "id": str(i)} for i in matrix.columns])

# member_list = pd.read_sql_query("SELECT * FROM all_mem", cnx)
member_list = pd.read_pickle("data/all_mem.pickle")
member_list = member_list['Member'].tolist()
member_list = ['All Members'] + member_list

cat_list = pd.read_pickle("data/all_cat.pickle")
cat_list = cat_list['Topic'].tolist()
cat_list = ['All topics (slow loading)'] + cat_list
















##### Dash App
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
    html.A([dbc.Col(html.Img(src=app.get_asset_url("logo.png"),  width="180px", style={'margin-left':'15px', 'margin-bottom':'50px'}))], href="/page-1"),
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
                    # html.Div([
                    #         html.Hr(),
                    #         html.P(
                    #             "Download integrated tariff and trade data for research and analysis",
                    #             # className="lead",
                    #         ),
                    #     ],id="blurb",
                    # ),

                    # use the Collapse component to animate hiding / revealing links
                    dbc.Collapse(
                        dbc.Nav([
                                dbc.NavLink("Search", href="/page-1", id="page-1-link"),
                                dbc.NavLink("Question & Answer", href="/page-2", id="page-2-link"),
                                # dbc.NavLink("Reports - SrReference Tables", href="/page-3", id="page-3-link"),
                                # dbc.NavLink("Methodology", href="/page-4", id="page-4-link"),
                                # dbc.NavLink("Help", href="/page-5", id="page-5-link"),
                                # dbc.NavLink("Browse Sec Reports", href="/page-3", id="page-3-link"),
                                # dbc.NavLink("Browse Gov Reports", href="/page-4", id="page-4-link"),
                                dbc.NavLink("Inventory", href="/page-3", id="page-3-link"),
                                dbc.NavLink("About", href="/page-4", id="page-4-link"),
                                dbc.NavLink("Logout", href="/logout", active="exact"),  # Add a logout link
                            ], vertical=True, pills=False,
                        ), id="collapse",
                    ),
                    html.Div([html.P("V0.5 (20230619)",
                                # className="lead",
                            ),],id="blurb-bottom",
                    ),
                ], id="sidebar",
            )

content = html.Div(id="page-content")


# this callback uses the current pathname to set the active state of the
# corresponding nav link to true, allowing users to tell see page they are on
@app.callback(
    [Output(f"page-{i}-link", "active") for i in range(1, 5)],
    [Input("url", "pathname")],
)
def toggle_active_links(pathname):
    if pathname == "/":
        # Treat page 1 as the homepage / index
        return True, False, False, False, False
    return [pathname == f"/page-{i}" for i in range(1, 5)]



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
                            html.H4("Sign in to TPR Reports DB", className="card-title"),
                            html.Br(),
                            dbc.Form(
                                [
                                    dbc.Row([
                                            dbc.Col([
                                                    dbc.Input(type="text", id="username", placeholder="Username", style={"width": 300}),
                                                ], className="mb-3",
                                            )
                                        ]
                                    ),
                                    dbc.Row([
                                            dbc.Col([
                                                    dbc.Input(type="password",  id="password", placeholder="Password",style={"width": 300}),
                                                ], className="mb-3",
                                            )
                                        ]
                                    ),
                                    dbc.Button(id='login-button', children='Sign in', n_clicks=0, color="primary", className="my-custom-button", style={"width": 300}),
                                ], 
                            ),
                        ], className="d-grid gap-2 col-8 mx-auto",
                    ),
                    className="text-center",
                    style={"width": "500px", "margin": "auto", "background-color": "#e4f5f2"},
                ), width=6, className="mt-5",
            )
        ), id='login-facet',className="login-page",
    ),

    html.Div([sidebar, content], id='page-layout', style={'display': 'none'}),
])

@app.callback(
    [Output('login-facet', 'style'),
    Output('page-layout', 'style')],
    [Input('login-button', 'n_clicks')],
    [State('username', 'value'), State('password', 'value')]
)
def update_output(n_clicks, username, password):
    if n_clicks > 0:
        if username in USERS and USERS[username] == password:
            session['authed'] = True
    if session.get('authed', False):
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
    # elif pathname == "/":
    #     # return html.P("This is the content of the home page!"), pathname
    #     # return dcc.Location(pathname="/page-1", id="redirect-to-login"), "/page-1"  
    #     return dcc.Location(pathname="/page-1", id="redirect-to-login"), "/page-1"      
    # elif pathname == "/login":
    #     # return html.P("This is the content of page after login"), pathname
    #     return dcc.Location(pathname="/page-1", id="redirect-to-login"), "/page-1"
    # elif pathname == "/page-1":
    elif pathname in ["/","/login", "/page-1"]:
        return dbc.Container([
            html.H6("Search reports with OpenAI embeddings", className="display-about"),
            html.Br(),
            html.Br(),            
            dbc.Row([
                dbc.Col(
                        dbc.InputGroup([
                                dbc.Input(id="search-box", type="text", placeholder="Enter search query, e.g. subsidies and government support to fossil feul and energy", ),
                                dbc.Button(" Search ", id="search-button", n_clicks=0,
                                                #    className="btn btn-primary mt-3", 
                                            ),
                            ]
                        ), width=12,
                    ),
                ], justify="center", 
                # className="header", 
                id='search-container'
            ),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(html.Label("Display paragraphs with the highest score:"), width="auto",  style={'margin-top':5,'margin-left':10}),
                    dbc.Col(
                        dbc.RadioItems(
                            id="radio-select-top",
                            options=[
                                {"label": "Top 100", "value": 100},
                                {"label": "Top 200", "value": 200},
                                {"label": "Top 500", "value": 500},
                            ],
                            value=200,
                            inline=True,
                        ),
                        width=True,
                    ),
                ],
                align="center",
                style={"margin-bottom": "10px"},
            ),
            html.Br(),
            html.Br(),
            dbc.Row([
                dbc.Col([
                    dcc.Markdown(
                        '''
                        Be clear and specific when crafting your query. There's no need to worry about whether the words or phrases will exactly match the text you want to find. 
                        You can use English, French, Spanish, Arabic, German and other languages. Search query examples:
                        * subsidies and government supports on fossil fuel and energy
                        * find policies related to MSME, SME or small businesses in Africa
                        * any competition policy related to high-tech sector
                        * quantatitive restrictions (with typo)
                        * policies supporting ecommerce
                        * الإعانات والدعم الحكومي للوقود الأحفوري والطاقة
                        * interdictions d'importer ou d'exporter
                        * Πολιτικές που ευνοούν τις μικρές επιχειρήσεις

                        The search is based on 204 Trade Policy Review Secretariat reports issued since 2015, including a total 100,390 paragraphs.
                        '''
                        ),
                ], width=12),
            ], justify="center", 
            # className="header", 
            id='sample-queries'),

            html.Br(),
            html.Br(),

            dbc.Row([ 
                # html.Div(id="search-results", className="results"),
                dbc.Col([
                        # html.Div(id="search-results", className="results"),
                        dcc.Loading(id="loading", type="default", children=html.Div(id="search-results"), fullscreen=False),
                    ], width=12),
            ], justify="center"),
        ]), pathname






    elif pathname == "/page-2":
        return dbc.Container([
            html.H6("Q&A with ChatGTP (OpenAI) and report data", className="display-about"),
            html.Br(),
            html.Br(),
            dbc.Row([
                dbc.Col(
                        dbc.InputGroup([
                                dbc.Input(id="search-box2", type="text", placeholder="Enter search query, e.g. subsidies and government support to fossil feul and energy", ),
                                dbc.Button(" Query ChatGPT and TPR data ", id="search-button2", n_clicks=0,
                                                #    className="btn btn-primary mt-3", 
                                            ),


                            ]
                        ), width=12,
                    ),
                ], justify="center", className="header", id='search-container2'
            ),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(html.Label("Select OpenAI model:"), width="auto", style={'margin-top':5,'margin-left':10}),
                    dbc.Col(
                        dbc.RadioItems(
                            id="radio-select-top2",
                            options=[
                                {"label": "text-ada", "value": 'text-ada-001'},
                                {"label": 'text-curie', "value": 'text-curie-001'},
                                {"label": 'text-davinci', "value": 'text-davinci-003'},
                                {"label": 'gpt-35', "value": 'gpt-35-turbo'},
                            ],
                            value='text-davinci-003',
                            inline=True,
                        ),
                        width=True,
                    ),
                ],
                align="center",
                style={"margin-bottom": "10px"},
            ),
            html.Br(),
            html.Br(),
            dbc.Row([
                dbc.Col([
                    dcc.Markdown(
                        '''
                            - How WTO members protect biodiversity through their trade policy?
                            - How tariff rate quota (TRQ) is administered by WTO members?
                            - How WTO members subsidize energy and fossil fuel sector?
                            - How WTO members promote environmental services?
                            - How governments regulate wildlife trade?
                            - How WTO members support the circular economy?
                            - What trade restrictions are used most by WTO Members?
                            - Which countries have the most export restrictions?
                            - Which WTO members provide the export subsidies, in the last three years?
                            - Which members impose export tariffs or duties?
                            - How the United States trade policy changed in the past 5 years?
                        '''
                        ),
                ], width=12),
            ], justify="center", className="header", id='sample-queries2'),
            html.Br(),
            html.Br(),
            dbc.Row([ 
                # html.Div(id="search-results", className="results"),
                dbc.Col([
                        dcc.Loading(id="loading2", type="default", children=html.Div(id="search-results2"), fullscreen=False),
                    ], width=12),
            ], justify="center"),
        ]), pathname






    elif pathname == "/page-3":
        # return html.P("This is the content of page 2. Yay!")
        return html.Div([
                html.H4('List of members, years and reports: value = document symbol numbers'),
                dash_table.DataTable(
                    id='table',
                    columns=[{"name": i, "id": i} for i in matrix.columns],
                    data=matrix.to_dict('records'),
                    style_cell_conditional=[
                        {'if': {'column_id': 'Member'},
                         'width': '100px'},
                    ]
                )
            ]), pathname
    elif pathname == "/page-4":
        return html.Div([
                    # dbc.Container(
                    #     [
                            html.H4("About TPR Report Dataset", className="display-about"),
                            html.P(
                                "Explore information of the reports in a convinient way...",
                                className="lead",
                            ),
                            html.Hr(className="my-2"),
                            dcc.Markdown(markdown_about, id='topic',
                                         style={
                                            "display": "inline-block",
                                            "width": "100%",
                                            "margin-left": "0px",
                                            "align": "left",
                                            # "verticalAlign": "top"
                                        }),
                    #     ]
                    # )
                ]), pathname











    else:
        return html.P("404: Not found"), pathname
















#################################################
#####    Search
#################################################

# call back for returning results
@app.callback(
        [Output("search-results", "children"),  
        #  Output("top-space", "style"),
         Output("sample-queries", "style")
         ],
        [Input("search-button", "n_clicks")], 
        [State("search-box", "value"),
        State('radio-select-top', 'value')]
        )
def search(n_clicks, search_terms, top):
    # Check if the search button was clicked
    if n_clicks <=0 or search_terms=='' or search_terms is None:
        return "",  None
    else:
        
        df = search_docs(search_terms, top = top)
        
        csv_string = df.to_csv(index=False, encoding='utf-8')
        csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)

        df['meta'] = df['member'] + '\n' + df['symbol'] + '\n' + df['date'] + '\n Score: ' + df['score'].astype(str) 
        df['text'] = df['text'] + '\n\n [Topic]: ' + df['topic']

        matches = df[['meta', 'text']]
        matches.columns = ['Meta','Text (Paragraph)']

    # Display the results in a datatable
    return html.Div(style={'width': '100%'},
                     children=[
                        html.P('Find ' + str(len(matches)) +" paragraphs, with score ranging from " + str(df['score'].min()) + ' to ' + str(df['score'].max())),
                        html.A('Download CSV', id='download-link', download="rawdata.csv", href=csv_string, target="_blank",),
                        html.Br(),
                        dash_table.DataTable(
                                id="search-results-table",
                                columns=[{"name": col, "id": col} for col in matches.columns],
                                data=matches.to_dict("records"),

                                editable=False,
                                # filter_action="native",

                                sort_action="native",
                                sort_mode="multi",
                                
                                column_selectable=False,
                                row_selectable=False,
                                row_deletable=False,
                                
                                selected_columns=[],
                                selected_rows=[],
                                
                                page_action="native",
                                page_current= 0,
                                page_size= 20,
                                style_table={'width': '900px'},
                                style_header={'fontWeight': 'bold'},
                                style_cell={
                                    # 'height': 'auto',
                                    # 'minWidth': '50px', 
                                    # 'maxWidth': '800px',
                                    # # 'width': '100px',
                                    # 'whiteSpace': 'normal',
                                    'textAlign': 'left',
                                    'fontSize': '14px',
                                    'verticalAlign': 'top',
                                    'whiteSpace': 'pre-line'
                                },
                                style_cell_conditional=[
                                    # {'if': {'column_id': 'Symbol'},
                                    #  'width': '50px'},
                                    # {'if': {'column_id': 'Member'},
                                    #  'width': '90px'},
                                    # {'if': {'column_id': 'Date'},
                                    #  'width': '80px'},
                                    # {'if': {'column_id': 'Section/Topic'},
                                    #  'width': '200px'},
                                    {'if': {'column_id': 'Text (Paragraph)'},
                                    'width': '1000px'},
                                    # {'if': {'column_id': 'Score'},
                                    #  'width': '80px', 'textAlign': 'right'},
                                ],
                                style_data_conditional=[
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': 'rgb(250, 250, 250)',
                                    }
                                ],
                                style_as_list_view=True,
                            )
                        ]
            ),  {'display': 'none'}

#################################################
#####     Chat page
#################################################

# call back for returning results
@app.callback(
        [Output("search-results2", "children"),  
        #  Output("top-space2", "style"),
         Output("sample-queries2", "style")
         ],
        [Input("search-button2", "n_clicks")], 
        [State("search-box2", "value"),
        State('radio-select-top2', 'value')
        ]
        )
def chat(n_clicks, search_terms, model):
    # Check if the search button was clicked
    if n_clicks <=0 or search_terms=='' or search_terms is None:
        return "",  None
    else:
        chatgpt = complete(search_terms, model)
        # print(chatgpt)
        query_with_contexts = retrieve(search_terms)
        chatgpttpr = complete(query_with_contexts, model)
    return html.Div(
    dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(html.H4("Answer by OpenAI"), width={"size": 6, "offset": 0}),
                    dbc.Col(html.H4("Answer by OpenAI + TPR"), width={"size": 6, "offset": 0}),
                ],
                justify="between",
                style={"margin-bottom": "20px"},
            ),
            dbc.Row(
                [
                    dbc.Col(html.P(dcc.Markdown(chatgpt)), width={"size": 6, "offset": 0}),
                    dbc.Col(html.P(dcc.Markdown(chatgpttpr)), width={"size": 6, "offset": 0}),
                ],
                justify="between",
            ),
        ],
    )
),  {'display': 'none'}
 

#################################################
# end of function page
#################################################

















































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
    app.run_server(port=8888, debug=True)
