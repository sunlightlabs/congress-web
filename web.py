from os import environ
import re

from flask import Flask, abort, redirect, render_template
import requests

from cache import Dummycached, Memcached

COMPROMISE_MORALS = True


#
# the app
#

app = Flask(__name__)


# app store URLs

ANDROID_URL = "https://play.google.com/store/apps/details?id=com.sunlightlabs.android.congress&hl=en"
IOS_URL = "http://sunlightfoundation.com"


# load environment variables

app.config['SUNLIGHT_KEY'] = environ.get("SUNLIGHT_KEY")

app.config['MEMCACHED_SERVERS'] = environ.get('MEMCACHIER_SERVERS')
app.config['MEMCACHED_USERNAME'] = environ.get('MEMCACHIER_USERNAME')
app.config['MEMCACHED_PASSWORD'] = environ.get('MEMCACHIER_PASSWORD')

try:
    # try to load local settings from settings.py
    app.config.from_object('settings')
except ImportError:
    pass  # no worries, CONTINUE!


# other constants

BILL_TYPES = ("hr", "hres", "hjres", "hconres", "s", "sres", "sjres", "sconres")
BILL_ID_RE = re.compile(r"^(?P<type>[a-z]+)(?P<number>\d+)-(?P<session>\d+)$")
VOTE_ID_RE = re.compile(r"^(?P<chamber>[sh])(?P<number>\d+)-(?P<year>\d{4})$")

# set up cache

if app.config.get('MEMCACHED_SERVERS'):
    cache = Memcached(
        app.config['MEMCACHED_SERVERS'].split(','),
        app.config['MEMCACHED_USERNAME'],
        app.config['MEMCACHED_PASSWORD'],
        timeout=10)
else:
    cache = Dummycached()


# data loading methods

def load_legislator(bioguide_id):

    moc = cache[bioguide_id]

    if not moc:

        app.logger.debug('bioguide_id cache miss: %s' % bioguide_id)

        session = requests.session()
        session.headers = {'User-Agent': 'congress-web'}

        params = {
            'apikey': app.config['SUNLIGHT_KEY'],
            'bioguide_id': bioguide_id,
        }

        # load from Sunlight API

        url = "http://congress.api.sunlightfoundation.com/legislators"
        resp = session.get(url, params=params)

        if resp.status_code != 200:
            abort(resp.status_code)

        data = resp.json()

        if 'results' not in data or not data['results']:
            abort(404)

        moc = data['results'][0]

        # load Influence Explorer ID

        url = "http://transparencydata.com/api/1.0/entities/id_lookup.json"
        resp = session.get(url, params=params)

        if resp.status_code == 200:
            data = resp.json()
            if data:
                moc['influenceexplorer_id'] = data[0]['id']

        cache[bioguide_id] = moc

    return moc


def load_vote(vote_id):
    pass


#
# basic templates and redirects
#

@app.route('/')
def index():
    return android()


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
    moc = load_legislator(bioguide_id)
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

    govtrack_url = "http://www.govtrack.us/congress/bills/%s/%s%s" % (session, bill_type, number)
    opencongress_url = "http://www.opencongress.org/bill/%s-%s%s/show" % (session, bill_type, number)

    return redirect(opencongress_url if COMPROMISE_MORALS else govtrack_url)


#
# votes
#

@app.route('/v/<vote_id>')
def vote_id(vote_id):

    match = VOTE_ID_RE.match(vote_id)

    if not match:
        return redirect('/')

    (chamber, number, year) = match.groups()
    session = ((int(year) + 1) / 2) - 894

    govtrack_url = "http://www.govtrack.us/congress/votes/%s-%s/%s%s" % (session, year, chamber, number)
    opencongress_url = "http://www.opencongress.org/vote/%s/%s/%s" % (year, chamber, number)

    return redirect(opencongress_url if COMPROMISE_MORALS else govtrack_url)


#
# debug views
#

if app.debug:

    @app.route('/config')
    def configuration():
        items = "\n".join("<dt>%s</dt><dd>%s</dd>" % (k, v) for k, v in app.config.items())
        return "<dl>%s</dl>" % items


#
# cli
#

if __name__ == '__main__':
    app.run(port=8000, host="0.0.0.0")
