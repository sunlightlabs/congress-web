from os import environ
import re

from flask import Flask, redirect, render_template
import requests

try:
    import settings
except ImportError:
    pass  # no local settings found, just ignore


app = Flask(__name__)

CONGRESS_KEY = environ.get("SUNLIGHT_KEY")

ANDROID_URL = "https://play.google.com/store/apps/details?id=com.sunlightlabs.android.congress&hl=en"
IOS_URL = "http://sunlightfoundation.com"

BILL_TYPES = ("hr", "hres", "hjres", "hconres", "s", "sres", "sjres", "sconres")
BILL_ID_RE = re.compile(r"(?P<bill_type>[a-z]+)(?P<number>\d+)(?:-(?P<session>\d+))?")


#
# basic templates and redirects
#

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/android')
def android():
    return redirect(ANDROID_URL)


@app.route('/ios')
def ios():
    return redirect(IOS_URL)


#
# legislators
#

@app.route('/l/<bioguide_id>')
def legislator(bioguide_id):

    params = {
        'apikey': CONGRESS_KEY,
        'bioguide_id': bioguide_id,
    }

    url = "http://congress.api.sunlightfoundation.com/legislators"

    resp = requests.get(url, params=params)

    if resp.status_code == 200:

        data = resp.json()

        if 'results' in data and data['results']:
            moc = data['results'][0]
            return render_template("legislator.html", moc=moc)


#
# bills
#


@app.route('/b/<bill_id>')
def bill_id(bill_id):

    match = BILL_ID_RE.match(bill_id)

    if not match:
        return redirect('/')

    (bill_type, number, session) = match.groups()
    url = "http://www.govtrack.us/congress/bills/%s/%s%s" % (session, bill_type, number)

    return redirect(url)


#
# cli
#

if __name__ == '__main__':
    app.run(debug=True, port=8000, host="0.0.0.0")
