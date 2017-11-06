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

# global variables
cta_counter = 0
cta_results = []


###########################
# Data Manipulation / Model
###########################

def fetch_cta_data(route=None, stop_id='1066'):
    CTA_BASE_URL = 'http://www.ctabustracker.com/bustime/api/v2/getpredictions'
    CTA_API_KEY = os.getenv('CTA_API_KEY', None)

    # set up request parameters
    payload = {
        'key': CTA_API_KEY,
        'stpid': stop_id,
        'format': 'json'
    }
    if route is not None:
        payload['rt'] = route

    right_now = maya.MayaDT.from_datetime(datetime.datetime.now())
    r = requests.get(CTA_BASE_URL, params=payload)
    upcoming_buses = r.json().get('bustime-response', None).get('prd', None)
    cleaned_results = []
    for bus in upcoming_buses:
        predicted_time = maya.parse(bus['prdtm'])
        min_till_next_bus = (predicted_time.epoch - right_now.epoch) / 60

        cleaned_results.append(
            (bus['rt'], math.floor(min_till_next_bus))
        )

    return pd.DataFrame.from_records(cleaned_results, columns=['Bus', 'ETA'])


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
    # between 6am and 9pm, we will refresh every 20 seconds
    # during the rest of the day, refresh every 2 minutes
    global cta_counter
    global cta_results  # global scope keeps result from previous API request

    # do we need to poll the API?
    now = datetime.datetime.now()
    early_morning = 6 <= now.hour <= 9
    counter_full = cta_counter >= 2
    refresh_data = early_morning or counter_full

    if refresh_data:
        cta_results = fetch_cta_data()
        cta_counter = 0
    else:
        cta_counter += 1

    table = []
    if len(cta_results) > 0:
        table = ff.create_table(cta_results)

    return table


# start Flask server
if __name__ == '__main__':
    app.run_server(
        debug=True,
        host='0.0.0.0',
        port=8050
    )
