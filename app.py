# standard library
import datetime
import math
import os

# dash libs
import dash
from dash.dependencies import Output, Event
import dash_core_components as dcc
import dash_html_components as html
import plotly.figure_factory as ff

# misc libraries
import requests
import maya
import pandas as pd

# constants
CTA_BASE_URL = 'http://www.ctabustracker.com/bustime/api/v2/getpredictions'
CTA_API_KEY = os.getenv('CTA_API_KEY', None)


###########################
# Data Manipulation / Model
###########################

def fetch_cta_data(route=None):
    CTA_BASE_URL = 'http://www.ctabustracker.com/bustime/api/v2/getpredictions'
    CTA_API_KEY = os.getenv('CTA_API_KEY', None)

    payload = {
        'key': CTA_API_KEY,
        'stpid': 1066,
        'format': 'json'
    }

    if route is not None:
        payload['rt'] = route

    r = requests.get(CTA_BASE_URL, params=payload)
    right_now = maya.MayaDT.from_datetime(datetime.datetime.now())

    upcoming_buses = []
    for bus in r.json()['bustime-response']['prd']:
        predicted_time = maya.parse(bus['prdtm'])
        min_till_next_bus = (predicted_time.epoch - right_now.epoch) / 60

        upcoming_buses.append(
            (bus['rt'], math.floor(min_till_next_bus))
        )

    return pd.DataFrame.from_records(upcoming_buses, columns=['Bus', 'ETA'])


#########################
# Dashboard Layout / View
#########################

# Set up Dashboard and create layout
app = dash.Dash()
app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})

app.layout = html.Div([

    # Page Header
    html.Div([
        html.H1('SivMetrics'),
        dcc.Interval(
            id='cta-interval-component',
            interval=20*1000,
        ),
        dcc.Graph(id='cta-upcoming-buses')
    ]),

])


#############################################
# Interaction Between Components / Controller
#############################################

# Refresh the page and based on time of day, call the CTA API function
@app.callback(
    Output(component_id='cta-upcoming-buses', component_property='figure'),
    events=[Event('cta-interval-component', 'interval')]
)
def load_uncoming_buses():
    results = fetch_cta_data()

    table = []
    if len(results) > 0:
        table = ff.create_table(results)

    return table


# start Flask server
if __name__ == '__main__':
    app.run_server(
        debug=True,
        host='0.0.0.0',
        port=8050
    )
