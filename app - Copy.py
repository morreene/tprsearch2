"""
This app creates a responsive sidebar layout with dash-bootstrap-components and
some custom css with media queries.

When the screen is small, the sidebar moved to the top of the page, and the
links get hidden in a collapse element. We use a callback to toggle the
collapse when on a small screen, and the custom CSS to hide the toggle, and
force the collapse to stay open when the screen is large.

dcc.Location is used to track the current location. There are two callbacks,
one uses the current location to render the appropriate page content, the other
uses the current location to toggle the "active" properties of the navigation
links.

For more details on building multi-page Dash applications, check out the Dash
documentation: https://dash.plot.ly/urls

http://v-stage:8085/index.html

"""
import dash
from dash import html, dcc, dash_table
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
import pandas as pd
import json
import urllib
import datetime
import time

import webbrowser
from threading import Timer
# import markdown
# import os
# import urllib.parse



sever_str = "http://v-stage:8085/"
sever_str = "http://10.82.35.61:8085/"

# read data and markdown files
with open('data/markdown_text_methodology.md', 'r') as markdown_file:
    markdown_text_methodology = markdown_file.read()
# with open('data/markdown_text_help.md', 'r') as markdown_file:
#     markdown_text_help = markdown_file.read()

dict_indicator = pd.read_csv('data/reference_indicator.csv')
dict_inventory_note = dict(zip(dict_indicator['Indicator'], dict_indicator['InventoryNote']))
dict_indicator = dict(zip(dict_indicator['Indicator'], dict_indicator['Name']))

dict_country = pd.read_csv('data/reference_reporter.csv')
dict_country = dict_country.sort_values('displayOrder')
dict_country = dict(zip(dict_country['reporter'], dict_country['name']))

dict_product = pd.read_csv('data/reference_hs.csv', dtype='str')
dict_product['Combined'] = dict_product['HSCode'] + ' (' + dict_product['HSV'] + ') ' + dict_product['HSDescription'].str[0:80]
dict_product = dict_product.sort_values('Combined')
dict_product = dict(zip(dict_product['HSCode'], dict_product['Combined']))

list_year = [str(year) for year in range(2023, 1987, -1)]

ds = pd.read_csv('data/reference_schemes.csv')

all_country = list(dict_country.keys())
all_year = [str(year) for year in range(2023, 1987, -1)]

# dash app
external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css']
# with "__name__" local css under assets is also included
app = dash.Dash(__name__, external_stylesheets = external_stylesheets)

app.title = 'WTO Analytical Database'
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

server = app.server
app.config.suppress_callback_exceptions = True
# we use the Row and Col components to construct the sidebar header
# it consists of a title, and a toggle, the latter is hidden on large screens
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
                    dbc.NavLink("Download and API", href="/page-1", id="page-1-link"),
                    dbc.NavLink("Data Inventory", href="/page-2", id="page-2-link"),
                    dbc.NavLink("Reference Tables", href="/page-3", id="page-3-link"),
                    dbc.NavLink("Methodology", href="/page-4", id="page-4-link"),
                    dbc.NavLink("Help", href="/page-5", id="page-5-link"),
                ],
                vertical=True,
                pills=False,
            ),
            id="collapse",
        ),
        html.Div([
                html.P(
                    "V0.92 (20230504)",
                    # className="lead",
                ),
                ],
                id="blurb-bottom",
        ),
    ],
    id="sidebar",
)

content = html.Div(id="page-content")

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

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

@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname in ["/", "/page-1"]:
        return html.Div(
                [
                    html.H4("API Builder and Data Downloader", className="display-about"),
                    html.Br(),
                    html.H6("Selection Required"),
                    html.Hr(className="my-2"),  

                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Span('Indicator'),
                                    dcc.Dropdown(
                                        id='dropdown_indicator',
                                        multi=False,
                                        options=[{'label': i[1], 'value': i[0]} for i in dict_indicator.items()],
                                        value='MFN_Appl_1',
                                        clearable=False
                                    ),
                                ]
                            )
                        ]
                    ),

                    html.Br(),
                    html.Br(),

                    html.H6("Selections Optional"),
                    html.Hr(className="my-2"),  
                    # html.P("Not all combinations of selections will return data. Please press button 'Show row count and sample' to check."),
                    dcc.Markdown("*Not all combinations of selections will return data. Please press button 'Show row count and sample' to check.*"),
                    
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Span('Reporters'),
                                    dcc.Dropdown(
                                        id='dropdown_reporter',
                                        multi=True,
                                        options=[{'label': i[1], 'value': i[0]} for i in dict_country.items()],
                                        value=[],
                                        placeholder= 'All',
                                        clearable=False,
                                        maxHeight=200,
                                    ),
                                ], width=6
                            ),
                            dbc.Col(
                                [
                                    html.Span('Years'),
                                    dcc.Dropdown(
                                        id='dropdown_year',
                                        multi=True,
                                        options=[{'label': i, 'value': i} for i in list_year],
                                        value=[],
                                        placeholder= 'All',
                                        clearable=False
                                    ),
                                ], width=6
                            ),
                            # dbc.Col(
                            #     [
                            #         html.Span('HS Codes'),
                            #         dcc.Dropdown(
                            #             id='dropdown_hs',
                            #             multi=True,
                            #             options=[{'label': i[1], 'value': i[0]} for i in dict_product.items()],
                            #             value=[],
                            #             placeholder= 'All',
                            #             clearable=False
                            #         ),
                            #     ], width=4
                            # ),

                        ]
                    ),
                    html.Br(),
                    dbc.Row([
                            dbc.Col(
                                [
                                    # html.Span('HS Codes and Descriptions <i>(H1=HS1992, H2=HS1996, H3=HS2002, H4=HS2007, H5=HS2012, H6=HS2017, H7=HS2022)</i>'),
                                    dcc.Markdown('HS Codes and Descriptions *(H1=HS1992, H2=HS1996, H3=HS2002, H4=HS2007, H5=HS2012, H6=HS2017, H7=HS2022)*'),
                                    dcc.Dropdown(
                                        id='dropdown_hs',
                                        multi=True,
                                        options=[{'label': i[1], 'value': i[0]} for i in dict_product.items()],
                                        value=[],
                                        placeholder= 'All',
                                        clearable=False
                                    ),
                                ], width=12
                            ),
                    ]),
                    dbc.Row(
                        [
                            dbc.Col([
                                    html.Span('Partners'),
                                    dcc.Dropdown(
                                        id='dropdown_partner',
                                        multi=True,
                                        options=[{'label': i[1], 'value': i[0]} for i in dict_country.items()],
                                        value=[],
                                        placeholder= 'All',
                                        clearable=False
                                    ),
                                ], width=4, id='conditional_partner', style={'display': 'none'}, 
                            ),

                            dbc.Col([
                                    html.Span('Tariff Schemes (options appear when reporters selected)'),
                                    dcc.Dropdown(
                                        id='dropdown_scheme',
                                        # options=[{'label': i, 'value': i} for i in cat_list],
                                        multi=True,
                                        value=[],
                                        placeholder= 'All',
                                        clearable=False,
                                    )
                                ], id='conditional_scheme', style={'display': 'none'}, 
                            )
                        ]
                    ),
                    dbc.Row([
                            dbc.Col([
                                # html.Button('Button', id='button', n_clicks=0, className='mr-2')
                                html.Br(),
                                # dbc.Button('Reset selections', href='/page-1', color='info', id='reset_button')
                                html.A(dbc.Button('Reset selections', color='info'),href='/'),
                                # dbc.Button('Reset selections', color='info', id='reset_button')
                            ], width={'size': 3, 'offset': 9}, className='text-right')
                    ]),
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(id='alert_api'),

                                    # Store the result of the first callback in this hidden div
                                    dcc.Store(id='api_url_store')
                                ]
                            )
                        ]
                    ),
                    html.Br(),
                    html.H6("Preview and Download"),
                    html.Hr(className="my-2"),  
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Button("Show row count and sample", id="loading_button", n_clicks=0, color="info",),
                                ], width={'size': 6, 'offset': 0},className='text-left'
                                
                            ),
                            dbc.Col(
                                [
                                    dbc.Button('Download data in CSV', href='', color='info', id="download_button")
                                ], width={'size': 3, 'offset': 3}, className='text-right'
                            ),
                        ],
                    ),
                    html.Br(),
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Spinner(html.Div(id="loading_output")),
                                ],
                            ),
                        ]
                    )
                ]
        )
    elif pathname == "/page-2":
        return html.Div(
                [
                    html.H4("Data Inventory", className="display-about"),
                    html.P("Data availablity and source in terms of economy and year",className="lead"),
                    html.Hr(className="my-2"),
                    html.Br(),
                    html.Br(),
                    # html.Hr(className="my-2"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Span('Select a Indicator'),
                                    dcc.Dropdown(
                                        id='inventory_dropdown_indicator',
                                        multi=False,
                                        options=[{'label': i[1], 'value': i[0]} for i in dict_indicator.items()],
                                        value='',
                                        clearable=False
                                    ),
                                ], 
                            ),
                        ]
                    ),

                    html.Div([

                    html.Div(id='inventory_table_container'),
                    dbc.Row(
                        [
                            dbc.Col(
                                [   
                                    html.Br(),
                                    dbc.Button('Download in CSV', href='', id='download_inventory_button', color='info',),
                                    # dcc.Download(id='download_inventory_button')
                                ], width={'size': 3, 'offset': 9}, id='conditional_inventory_button', style={'display': 'none'},  className='text-right',
                            ),
                        ],
                    ),
                ]
            )



        ])
    elif pathname == "/page-3":
        return html.Div([
                    html.H4("Reference Tables", className="display-about"),
                    html.P("Download reference table used by the API or the data dowloaded", className="lead"),
                    html.Hr(className="my-2"),
                    html.Br(),
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Col(html.P("WTO codes and names of countries or customs tarritories")),
                            dbc.Col([
                                    dbc.Button('Download', href='', color='info',id="btn_reference_reporter"),
                                    dcc.Download(id="download_reference_reporter"),
                            ]),
                        ]
                    ),
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Col(html.P("Harmonized System codes and product descriptions")),
                            dbc.Col([
                                    dbc.Button('Download', href='', color='info',id="btn_reference_hs"),
                                    dcc.Download(id="download_reference_hs"),
                            ]),
                        ]
                    ),
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Col(html.P("Harmonized System versions")),
                            dbc.Col([
                                    dbc.Button('Download', href='', color='info',id="btn_reference_hs_version"),
                                    dcc.Download(id="download_reference_hs_version"),
                            ]),
                        ]
                    ),
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Col(html.P("Preferential tariff schemes")),
                            dbc.Col([
                                    dbc.Button('Download', href='', color='info',id="btn_reference_scheme"),
                                    dcc.Download(id="download_reference_scheme"),
                            ]),
                        ]
                    ),
            ])

    elif pathname == "/page-4":
        return html.Div([
                    dbc.Container(
                        [
                            html.H1("Analytical Database Methodology", className="display-about"),
                            html.P("About data integration and processing", className="lead",),
                            html.Hr(className="my-2"),
                            dcc.Markdown(markdown_text_methodology),
                        ]
                    )
                ])
    elif pathname == "/page-5":
        return html.Div([
                    dbc.Container(
                        [
                            html.H1("Analytical Database - How to use API", className="display-about"),
                            html.P("Sample code ..", className="lead",),
                            html.Hr(className="my-2"),
                            dcc.Markdown('''
                                            While this tool provides a convenient way to download data, it is recommended to obtain data from the Analytical Database using its API for optimal performance and reliability. Data can be read into popular data analysis tools such as Python and R for analysis and processing.
                            '''),
                            dbc.Tabs(
                                [
                                    dbc.Tab(
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    dcc.Markdown('''
                                                        ```python

                                                        import pandas as pd
                                                        
                                                        # Set API URL
                                                        apiurl = "http://10.82.35.61:8085/api/Analytical/dataDownload?i=MFN_Appl_1&r=C008&y=2022"

                                                        # Download CSV and read it into a data frame
                                                        df = pd.read_csv(apiurl, compression= 'zip')
                                                        ```'''
                                                    )

                                                ]
                                            ),
                                            className="mt-3",
                                        ), 
                                    label="Python"
                                    ),
                                    dbc.Tab(
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    dcc.Markdown('''
                                                        ```r
                                                        library(httr)
                                                        library(readr)

                                                        # Set API URL
                                                        apiurl <- "http://10.82.35.61:8085/api/Analytical/dataDownload?i=MFN_Appl_1&r=C008&y=2022"

                                                        # Download CSV and read it into a data frame
                                                        download.file(apiurl, destfile = "download.zip", method="curl")
                                                        df <- read_csv("download.zip")
                                                        ```'''
                                                    )
                                                ]
                                            ),
                                            className="mt-3",
                                        ), 
                                    label="R"
                                    ),
                                ]
                            ),
                        ]
                    )
                ])

    # If the user tries to reach a different page, return a 404 message
    return dbc.Container(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )






# @app.callback(
#     Output('dropdown_reporter', 'value'),
#     Output('dropdown_year', 'value'),
#     Output('dropdown_hs', 'value'),
#     Output('dropdown_partner', 'value'),
#     Output('dropdown_scheme', 'value'),
#     Input('reset_button', 'n_clicks')
# )
# def reset_selections(n_clicks):
#     if n_clicks:
#         print('click')
#         return [], [],[], [],[]
#     else:
#         return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update








# show optional dropdowns for 3 indicators
@app.callback([
               Output('conditional_partner', 'style'),
               Output('conditional_scheme', 'style'),
              ],
              Input('dropdown_indicator', 'value')
    )
def show_optional_dropdowns(value):
    if value in ['Pref_IDB_1', 'Pref_RTA_1','Imp_2']:
        return {'display': 'block'}, {'display': 'block'}
    elif value in ['Pref_Best', 'Imp_1', 'Exp_1']:
        return {'display': 'block'}, {'display': 'none'}
    else:
        return {'display': 'none'}, {'display': 'none'}



# change scheme dropdown options according to reporter
@app.callback(
              Output('dropdown_scheme', 'options'),
              Input('dropdown_reporter', 'value')
    )
def update_dropdown_2_options(selected_option):
    # print(selected_option)
    if selected_option =='':
        ds1 = ds.copy()
    else:   
        ds1 = ds[ds['Reporter'].isin(selected_option)].copy()
    return dict(zip(ds1['DS_Code'], ds1['DS']))





# # change scheme dropdown options according to reporter
# @app.callback(
#         [
#             Output('dropdown_year', 'options'),
#         ],
#         [
#             Input('dropdown_reporter', 'value'),
#         ],
#         State('dropdown_year', 'value'),
#         State('dropdown_indicator', 'value'),
#     )
# def reactive_dropdowns(r,y,i):
#     print('r=',r,'y=',y)

#     url = "http://v-stage:8085/api/Analytical/dataInventory?i=" + i
#     response = urllib.request.urlopen(url)
#     inventory = json.loads(response.read().decode())
#     inventory = pd.json_normalize(inventory)

#     selctions = inventory[(inventory['reporter'].isin(r))]

#     if r != [] and y == []:
#         return [{s: s for s in list(selctions['year'].unique())}]
#     else:
#         return [{s : s for s in all_year}]
#     # else:
#     #     return [{'label':'555','value':'666'}]




# # change scheme dropdown options according to reporter
# @app.callback(
#         [
#             Output('dropdown_reporter', 'options'),
#         ],
#         [
#             Input('dropdown_year', 'value'),
#         ],
#         State('dropdown_reporter', 'value'),
#         State('dropdown_indicator', 'value'),
#     )
# def reactive_dropdowns(r,y,i):
#     print('r=',r,'y=',y)

#     url = "http://v-stage:8085/api/Analytical/dataInventory?i=" + i
#     response = urllib.request.urlopen(url)
#     inventory = json.loads(response.read().decode())
#     inventory = pd.json_normalize(inventory)

#     selctions = inventory[(inventory['year'].isin(r))]

#     if r == [] and y != []:
#         return [{s: s for s in list(selctions['reporter'].unique())}]
#     else:
#         return [{s : s for s in all_country}]
#     # else:
#     #     return [{'label':'555','value':'666'}]
















# # change scheme dropdown options according to reporter
# @app.callback(
#         [
#             Output('dropdown_reporter', 'options'),
#             Output('dropdown_year', 'options'),

#         ],
#         [
            
#             Input('dropdown_reporter', 'value'),
#             # Input('dropdown_year', 'value')
#         ],
#         # State('dropdown_year', 'value'),
#         State('dropdown_indicator', 'value'),
#     )
# def reactive_dropdowns(r,i):

#     url = "http://v-stage:8085/api/Analytical/dataInventory?i=" + i
#     response = urllib.request.urlopen(url)
#     inventory = json.loads(response.read().decode())
#     inventory = pd.json_normalize(inventory)

#     # all_country = list(dict_country.keys())
#     # if r=='':
#     #     r=all_country
#     # if y=='':
#     #     y=[str(year) for year in range(2023, 1987, -1)]

#     # selctions = inventory[(inventory['reporter'].isin(r)) & (inventory['year'].isin(y))]

#     # return list(selctions['reporter'].unique()), list(selctions['year'].unique())

#     print('Selection = ', r, y)

#     # if r==None:
#     #     r=all_country
#     # if y==None:
#     #     y=all_year



#     # if r!='':
#     #     selctions = inventory[(inventory['reporter'].isin(r)) & (inventory['year'].isin(y))]
#     #     return all_country, list(selctions['year'].unique())

        
#     # if y!='':
#     #     selctions = inventory[(inventory['reporter'].isin(r)) & (inventory['year'].isin(y))]
#     #     return list(selctions['reporter'].unique()), all_year

#     selctions = inventory[(inventory['reporter'].isin(r)) & (inventory['year'].isin(y))]
    



#     if r!=None and y!=None:
#         print('New options = 1')
#         # , sorted(list(selctions['reporter'].unique())), sorted(list(selctions['year'].unique())))
#         return sorted(list(selctions['reporter'].unique())), sorted(list(selctions['year'].unique()))

#     elif r!=None:
#         print('New options = 2', )
#         # all_country, sorted(list(selctions['year'].unique())))
#         return all_country, sorted(list(selctions['year'].unique()))

#     elif r==None and y!=None:
#         print('New options = 3')
#         # , sorted(list(selctions['reporter'].unique())), all_year)
#         return sorted(list(selctions['reporter'].unique())), all_year
#     elif r==None and y==None:
#         print('New options = 4', all_country, all_year)
#         return all_country, all_year



















# show api url and sign to download button
@app.callback(
        [
            Output("alert_api", "children"), 
            Output("download_button", "href"),
            Output("api_url_store", "data"), 
        ],
        [
            Input('dropdown_indicator', 'value'),
            Input('dropdown_reporter', 'value'),
            Input('dropdown_partner', 'value'),
            Input('dropdown_year', 'value'),
            Input('dropdown_hs', 'value'),
            Input('dropdown_scheme', 'value'),
        ]
    )
def show_api_url(i, r, p, y, pc, ds):
    # "http://v-stage:8085/api/Analytical/data?i=MFN_Appl_1&r=C156&y=2019"
    # api_url = "http://v-stage:8085/api/Analytical/data?i=" + str(i) 
    api_url = "i=" + str(i) 

    if r != []:
        api_url = api_url + "&r=" + ','.join(r)
    if y != []:
        api_url = api_url + "&y=" + ','.join(y)
    if pc != []:
        api_url = api_url + "&pc=" + ','.join(pc)
    if p != []:
        api_url = api_url + "&p=" + ','.join(p)
    if ds != []:
        api_url = api_url + "&ds=" + ','.join(ds)

    # print('change', api_url)
    # print('reporter selected', r)

    return  html.Div([
                        html.H6('API URL'),
                        html.Hr(className="my-2"),  
                        dbc.Alert(sever_str + "api/Analytical/dataDownload?" + api_url, color="#e4f5f2", style={'height':'100px', 'padding-top':'35px'}, id='apiurl'), 
                        dcc.Clipboard(
                            target_id="apiurl",
                            style={
                                "position": "absolute",
                                "top": 45,
                                "right": 30,
                                "fontSize": 20,
                            },
                        ),
                    ]
                ), sever_str + "api/Analytical/dataDownload?" + api_url, api_url, 


# show sample data
@app.callback(
        Output("loading_output", "children"),  
        Input("loading_button", "n_clicks"),
        State("api_url_store", "data"),
        prevent_initial_call=True,
    )
def show_sample(n_clicks, url):
    # print('sample',url)

    if n_clicks >= 1:
        # time.sleep(1)
        # print('sample',api_url)
        # return f"Output loaded {n} times"
        api_url = sever_str + "api/Analytical/data?" + url

        cnt_url = sever_str + "api/Analytical/dataCount?" + url
        response = urllib.request.urlopen(cnt_url)
        count = json.loads(response.read().decode())

        response = urllib.request.urlopen(api_url)
        data = json.loads(response.read().decode())
        df = pd.json_normalize(data, 'data')

        return html.Div(
                    [   html.Br(),
                        html.P(children=['A total of ', html.B(str(count)), ' rows of data will be returned by this query. The first 100 rows are displayed below. '], style={'text-align': 'left'}),
                        dash_table.DataTable(
                            id = 'table',
                            columns = [{"name": i, "id": i} for i in df.columns if i !='inventoryId'],
                            data = df.to_dict('records'),
                            # style={'align': 'left'},
                            fixed_rows={'headers': True, 'data': 0},
                            style_table={'minWidth': '100%'},
                            style_cell={
                                'minWidth': '100px', 
                                # 'overflow': 'hidden',
                            }
                        )
                    ], style={'float':'left'},
                )
    else: 
        return ""



















































# create csv for downloading inventory 
def create_csv_string(df):
    csv_string = df.to_csv(index=False, encoding='utf-8')
    return "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)

# show inventory
@app.callback(
    [
        Output("inventory_table_container", "children"), 
        Output("download_inventory_button", "href"),
        Output('conditional_inventory_button', 'style'),
    ],
    Input("inventory_dropdown_indicator", "value"),
    prevent_initial_call=True,
)
def show_inventory_table(indicator):

    df_member = pd.read_csv('data/reference_reporter.csv', dtype='str')
    df_member['WTOYear'] = ' (' + df_member['WTOYear'] + ')'
    df_member['WTOYear'] = df_member['WTOYear'].fillna('')
    df_member['name'] = df_member['name']  + df_member['WTOYear']
    df_member = df_member.rename(columns = {'name':'Economy (Membership)'})

    url = sever_str + "api/Analytical/dataInventory?i=" + indicator
    # print(url)
    response = urllib.request.urlopen(url)
    inventory = json.loads(response.read().decode())
    inventory = pd.json_normalize(inventory)
    if indicator=='Pref_RTA_1':
        inventory = inventory.groupby(['reporter','year'])['source'].first().reset_index()
    
    
    inventory_download = inventory.copy()
    inventory_download['reporterName']=inventory_download['reporter'].map(dict_country)
    # print(inventory.shape)
    inventory['source'] = inventory['source'].str.replace('CTS_Transposition','CTR')
    inventory['source'] = inventory['source'].str.replace('Draft_Transposition','DTR')
    inventory['source'] = inventory['source'].str.replace('WTO IDB/RTA or WTP','WW')
    inventory['source'] = inventory['source'].str.replace('Comtrade','CTD')

    inventory = pd.merge(inventory,df_member,on='reporter')
    inventory = inventory.pivot(index='Economy (Membership)',columns='year',values='source').reset_index()
    # print(inventory.shape)

    return html.Div(
                [
                    html.Br(),
                    html.H5(dict_indicator[indicator], style={'text-align': 'center'}),
                    dash_table.DataTable(
                        id = 'table',
                        columns = [{"name": i, "id": i} for i in inventory.columns if i !='inventoryId'],
                        data = inventory.to_dict('records'),
                        fixed_rows={'headers': True, 'data': 0},
                        fixed_columns={ 'headers': True, 'data': 2 },
                        style_table={'minWidth': '100%'},
                        style_cell={
                            'minWidth': '40px', 
                            # 'overflow': 'hidden',
                        },
                    ),
                    # html.P('Note: CTR=CTS_Transposition; DTR=Draft_Transposition; WW=WTO IDB/RTA or WTP; CTD=Comtrade'),
                    html.P(dict_inventory_note[indicator])
                    
                ]
            ), create_csv_string(inventory_download), {'display': 'block'}













# Download reference table
@app.callback(
    Output("download_reference_reporter", "data"),
    Input("btn_reference_reporter", "n_clicks"),
    prevent_initial_call=True,
)
def func(n_clicks):
    return dcc.send_file(
        "./data/reference_reporter.csv"
    )

@app.callback(
    Output("download_reference_hs", "data"),
    Input("btn_reference_hs", "n_clicks"),
    prevent_initial_call=True,
)
def func(n_clicks):
    return dcc.send_file(
        "./data/reference_hs.csv"
    )

@app.callback(
    Output("download_reference_hs_version", "data"),
    Input("btn_reference_hs_version", "n_clicks"),
    prevent_initial_call=True,
)
def func(n_clicks):
    return dcc.send_file(
        "./data/reference_hs_version.csv"
    )

@app.callback(
    Output("download_reference_scheme", "data"),
    Input("btn_reference_scheme", "n_clicks"),
    prevent_initial_call=True,
)
def func(n_clicks):
    return dcc.send_file(
        "./data/reference_schemes.csv"
    )










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




'''
Change this part when making executable app
'''
# original
if __name__ == '__main__':
    app.run_server(debug=True)
    # app.run_server(debug=True, host='0.0.0.0', port=8050) # for docker


# if __name__ == '__main__':
#     app.run_server(debug=True, host='0.0.0.0', port=8050)

# # for pyinstaller
# def open_browser():
# 	webbrowser.open_new("http://localhost:{}".format(8050))

# if __name__ == '__main__':
#     Timer(1, open_browser).start();
#     app.run_server(debug=False, port=8050)