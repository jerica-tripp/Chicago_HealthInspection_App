import pandas as pd
from sodapy import Socrata
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
import numpy as np

# ----------CONNECT TO API ---------- #
client = Socrata("data.cityofchicago.org",
                 "XEXKzTKTGiNQ6ipSHWSUDRfly",
                 username="jerica.tripp@yahoo.com",
                 password="iForgot_22")

results = client.get("4ijn-s7e5",
                     where="inspection_date>='2019-01-01T00:00:00.000' AND results <>'No Entry' AND results <> 'Not Ready' AND results <> 'Out of Business'AND results <> 'Business Not Located'",
                     order="inspection_date DESC",
                     limit=300000)

# ---------- BUILD BASE DATA FRAME ---------- #
df = pd.DataFrame.from_records(results)
df['count'] = 1 #This will serve as the record counter
df['inspection_date (YYYY/MM)'] = pd.to_datetime(df['inspection_date']).dt.strftime("%Y/%m")
df['inspection_date'] = pd.to_datetime(df['inspection_date']).dt.strftime("%m/%d/%Y")
df.fillna(0)

# ---------- CLEAN UP DATA FRAME  ---------- #
df = df[df[['latitude', 'longitude', 'zip']].notnull().all(1)]
df['latitude'] = pd.to_numeric(df['latitude'])
df['longitude'] = pd.to_numeric(df['longitude'])
df['zip'] = pd.to_numeric(df['zip'])

# ---------- BUILD DATA FRAME FOR CROSSTAB VIZ  ---------- #

crosstab = df[['dba_name', 'facility_type', 'inspection_date', 'results', 'risk', 'violations']]

# ---------- BUILD DATA FRAMES FOR COLORS, FILTERS,  AND DROP DOWNS ---------- #

# RESULTS OF INSPECTION
results_df = df['results'].sort_values().fillna('NULL').unique()

# RISK LEVEL OF INSPECTION
risk_df = df['risk'].sort_values().fillna('NULL').unique()

# INSPECTION ZIP CODE
ziplist_df = df['zip'].unique()

# RESTAURANT TYPE
restType_df = df['facility_type'].sort_values().fillna('NULL').unique()

# ---------- BUILD DASH APP ---------- #
external_stylesheets = ['static/style.css']
PAGE_SIZE = 10 # VARIABLE SET FOR PAGINATION OF TABULAR VIZ
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server


# ---------- CORE HTML ---------- #
app.layout = html.Div(className="main-container", children=[
    html.Div([
        html.Div(className="tabs-nav", children=[
            html.H1(["Chicago Health Inspections"])
        ])

    ]),
# ---------- DROP DOWNS ---------- #
    html.Div(className="tab-panel", children=[
        html.Div(className="map white chart-pane", children=[
            html.Div(className="map_dropdowns", children=[
                html.P([
                    html.Label("Select Zip Code"),
                    dcc.Dropdown(
                        id='zipfilter',
                        options=[{'label': i, 'value': i} for i in ziplist_df]
                    )]),
                html.P([
                    html.Label("Select Facility Type"),
                    dcc.Dropdown(
                        id='foodtypefilter',
                        options=[{'label': i, 'value': i} for i in restType_df]
                    )]),
            ]),
                dcc.Graph(id='choropleth')
        ]),

        html.Div(className="linegraph white chart-pane", children=[
            html.Div(className="dropdowns", children=[
            html.P([
                html.Label("View"),
                dcc.Dropdown(
                    id='opt',
                    options=[{'label': 'risk', 'value': 'risk'},
                             {'label': 'results', 'value': 'results'}
                             ],
                    value='results'

                )]),
            html.P([
            html.Label("where risk level like:"),
            dcc.Dropdown(
                id='filter2',
                options=[{'label': i, 'value': i} for i in risk_df ]

            )]),
            html.P([
                html.Label("where inspection result like:"),
                dcc.Dropdown(
                    id='filter1',
                    options=[{'label': i, 'value': i} for i in results_df
                             ]

                )])
                ]),
            # ----------  LINE CHART ---------- #
         dcc.Graph(id='scatter')
        ]),
        # ----------  CROSSTAB  ---------- #
        html.Div(className="tabular-chart white chart-pane", children=[
        dash_table.DataTable(
            id='table-paging-and-sorting',
            columns=[{'name': i, 'id': i} for i in sorted(crosstab.columns)],
            page_current=0,
            page_size=PAGE_SIZE,
            page_action='custom',
            sort_action='custom',
            sort_mode='single',
            sort_by=[],
            style_cell_conditional=[
                {
                    'if': {'column_id': 'inspection_date'},
                    'textAlign': 'right'
                },
                {'if': {'column_id': 'violations'},
                'width': '40%'}
            ],
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'},
            ],
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_cell={
                'height': '50px',
                'font-size': '2em',
                # all three widths are needed
                #'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
                'whiteSpace': 'normal'
            },
            style_data={'whiteSpace': 'normal'},
            css=[{
                'selector': '.dash-cell div.dash-cell-value',
                'rule': 'display: block; max-height: 100px; overflow-y: auto;'
            }

            ]
        )])

        ])
    ])


#CHOROPLETH
@app.callback(
    Output("choropleth", "figure"),
    [Input("zipfilter", "value"),
     Input("foodtypefilter", "value")
])

def update_map(zipfilter, foodtypefilter):
    if zipfilter is None and foodtypefilter is None:
        df4 = pd.pivot_table(df, index=['latitude', 'longitude', 'results','risk', 'inspection_date','facility_type','dba_name','zip', 'violations'], values=["count"], aggfunc=np.sum, fill_value=0)
        df4.reset_index(inplace=True)
    if zipfilter is not None and foodtypefilter is not None:
        df4 = pd.pivot_table(df[(df.zip == zipfilter) & (df.facility_type == foodtypefilter)], index=['latitude', 'longitude', 'results','risk', 'inspection_date','facility_type','dba_name','zip', 'violations'], values=["count"], aggfunc=np.sum, fill_value=0)
        df4.reset_index(inplace=True)
    if zipfilter is not None:
        df4 = pd.pivot_table(df[df.zip == zipfilter], index=['latitude', 'longitude', 'results','risk', 'inspection_date','facility_type','dba_name','zip', 'violations'], values=["count"], aggfunc=np.sum, fill_value=0)
        df4.reset_index(inplace=True)
    if foodtypefilter is not None:
        df4 = pd.pivot_table(df[df.facility_type == foodtypefilter], index=['latitude', 'longitude', 'results','risk', 'inspection_date','facility_type','dba_name','zip', 'violations'], values=["count"], aggfunc=np.sum, fill_value=0)
        df4.reset_index(inplace=True)
    return px.scatter_mapbox(
        df4,
        lat='latitude',
        lon='longitude',
        hover_name='dba_name',
        hover_data=['dba_name'],
        color_discrete_sequence=["yellow", "green", "red"],
        color='results',
        zoom=9).update_layout(mapbox_style="open-street-map").update_layout(clickmode='event+select',margin={"r": 0, "t": 0, "l": 0, "b": 0})


#LINE GRAPH
@app.callback(
    Output("scatter", "figure"),
    [Input("opt", "value"),
     Input("filter1", "value"), # result
     Input("filter2", "value")]) # facility_type

def update_graph(opt, filter1, filter2):
    if filter1 is None and filter2 is None:
        df2 = pd.pivot_table(df, index=['inspection_date (YYYY/MM)', opt], values=["count"], aggfunc=np.sum)
        df2.reset_index(inplace=True)
        df2 = df2.fillna(0)
        df2 = df2.sort_values('inspection_date (YYYY/MM)')
    if filter1 is not None and filter2 is None:
        df2 = pd.pivot_table(df[(df.results == filter1)], index=['inspection_date (YYYY/MM)', opt], values=["count"], aggfunc=np.sum).fillna(0)
        df2.reset_index(inplace=True)
        df2 = df2.fillna(0)
        df2 = df2.sort_values('inspection_date (YYYY/MM)')
    if filter1 is None and filter2 is not None:
        df2 = pd.pivot_table(df[(df.risk == filter2)], index=['inspection_date (YYYY/MM)', opt], values=["count"], aggfunc=np.sum).fillna(0)
        df2.reset_index(inplace=True)
        df2 = df2.sort_values('inspection_date (YYYY/MM)')
    if filter1 is not None and filter2 is not None:
        df2 = pd.pivot_table(df[((df.results == filter1) & (df.risk == filter2))], index=['inspection_date (YYYY/MM)', opt], values=["count"], aggfunc=np.sum).fillna(0)
        df2.reset_index(inplace=True)
        df2 = df2.sort_values('inspection_date (YYYY/MM)')
    return px.line(
        df2,
        x='inspection_date (YYYY/MM)',
        y='count',
        color=opt
        ).update_traces(connectgaps=True).update_layout(xaxis=dict(type='category',categoryorder='category ascending'))
#CROSSTAB

@app.callback(
    Output('table-paging-and-sorting', 'data'),
    [Input('table-paging-and-sorting', "page_current"),
     Input('table-paging-and-sorting', "page_size"),
     Input('table-paging-and-sorting', 'sort_by'),
     Input('choropleth', 'selectedData'),
     Input('choropleth', 'clickData')])

def update_table(page_current, page_size, sort_by, clickData, selectData):
    dff = crosstab
    df5 = pd.DataFrame()

    if clickData:
        for i in clickData['points']:
            dba_name_sel = i['customdata']
            df5 = df5.append(crosstab.loc[crosstab['dba_name'] == dba_name_sel[0]])
        dff = df5
    if len(sort_by):
        dff = dff.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False
        )
    return dff.iloc[
            page_current*page_size:(page_current+ 1)*page_size
            ].to_dict('records')



if __name__ == '__main__':
    app.run_server(
        port=8008
    )
# --------------------------------------- #
