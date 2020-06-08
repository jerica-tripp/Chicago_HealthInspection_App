import pandas as pd
from sodapy import Socrata
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State

#------------------------GET AND BUILD DATA FRAME FROM API -------------------------------------#

client = Socrata("data.cityofchicago.org",
    "XEXKzTKTGiNQ6ipSHWSUDRfly",
    username="jerica.tripp@yahoo.com",
    password="secretttt")

results = client.get("4ijn-s7e5")
df = pd.DataFrame.from_records(results)
df = df.drop(columns=['location'])  # do not need location
df = df.drop(columns=['latitude'])  # do not need location
df = df.drop(columns=['longitude'])  # do not need location
df.columns = ['Inspection_ID', 'DBA_Name', 'AKA_Name', 'License', 'Facility_Type', 'Risk', 'Address', 'City', 'State',
                    'Zip', 'Inspection_Date', 'Inspection Type', 'Results', 'Violations']

df['Inspection_Date'] = pd.to_datetime(df['Inspection_Date']).dt.strftime("%m/%d/%y")
# df['Violations'] = df['Violations'].astype(float)

features = df.columns

#-----------------------------------------------------------------------------------------------#



app = dash.Dash(__name__)

app.layout = html.Div([
    dash_table.DataTable(
        id='datatable-interactivity',
        style_cell_conditional=[
            {
                'if': {'column_id': c},
                'textAlign': 'left'
            } for c in ['Date', 'Region']
        ],
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ],
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },

        style_cell={'textAlign': 'left'},
        style_data={'whiteSpace': 'normal'},
        css=[{
            'selector': '.dash-cell div.dash-cell-value',
            'rule': 'display: block; max-height: 100px; overflow-y: auto;'
        },

        ],

        columns=[
            {"name": i, "id": i, "deletable": True,"selectable": True} for i in df.columns
        ],
        data=df.to_dict('records'),
        editable=False,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        column_selectable="multi",
        # row_selectable="multi",
        row_deletable=True,
        # selected_columns=[],
        # selected_rows=[],
        page_action="native",
        page_current= 0,
        page_size= 10,
    ),
    html.Div(id='datatable-interactivity-container')
])

if __name__ == '__main__':
    app.run_server(debug=True)
