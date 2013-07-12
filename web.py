from os import environ
import re

from flask import Flask, abort, g, redirect, render_template, request
# import httpagentparser
import requests

from cache import Dummycached, Memcached

COMPROMISE_MORALS = False


#
# the app
#

app = Flask(__name__)


# app store URLs

ANDROID_URL = "https://play.google.com/store/apps/details?id=com.sunlightlabs.android.congress&hl=en"
IOS_URL = "http://appstore.com/congressbysunlightfoundation"

WEB_URL = "http://congress.sunlightfoundation.com/"
CONTACT_URL = "http://sunlightfoundation.com/contact/?slot=Congress%20for%20Android%20and%20iOS"


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

# setup requests

http = requests.Session()
http.headers = {'User-Agent': 'congress-web'}


# data loading methods

def load_legislator(bioguide_id):

    key = "legislator:%s" % bioguide_id

    moc = cache[key]

    if not moc:

        app.logger.debug('bioguide_id cache miss: %s' % bioguide_id)

        params = {
            'apikey': app.config['SUNLIGHT_KEY'],
            'bioguide_id': bioguide_id,
        }

        # load from Sunlight API

        url = "http://congress.api.sunlightfoundation.com/legislators"
        resp = http.get(url, params=params)

        if resp.status_code != 200:
            abort(resp.status_code)

        data = resp.json()

        if 'results' not in data or not data['results']:
            abort(404)

        moc = data['results'][0]

        # load Influence Explorer ID

        url = "http://transparencydata.com/api/1.0/entities/id_lookup.json"
        resp = http.get(url, params=params)

        if resp.status_code == 200:
            data = resp.json()
            if data:
                moc['influenceexplorer_id'] = data[0]['id']

        cache[key] = moc

    return moc


def load_bill(bill_id):

    key = "bill:%s" % bill_id

    bill = cache[key]

    if not bill:

        app.logger.debug('bill_id cache miss: %s' % bill_id)

        params = {
            'apikey': app.config['SUNLIGHT_KEY'],
            'bill_id': bill_id,
        }

        # load from Sunlight API

        url = "http://congress.api.sunlightfoundation.com/bills"
        resp = http.get(url, params=params)

        if resp.status_code != 200:
            abort(resp.status_code)

        data = resp.json()

        if 'results' not in data or not data['results']:
            abort(404)

        bill = data['results'][0]
        cache[key] = bill

    return bill


def load_vote(vote_id):

    key = "vote:%s" % vote_id

    vote = cache[key]

    if not vote:

        app.logger.debug('vote_id cache miss: %s' % vote_id)

        params = {
            'apikey': app.config['SUNLIGHT_KEY'],
            'vote_id': vote_id,
        }

        # load from Sunlight API

        url = "http://congress.api.sunlightfoundation.com/votes"
        resp = http.get(url, params=params)

        if resp.status_code != 200:
            abort(resp.status_code)

        data = resp.json()

        if 'results' not in data or not data['results']:
            abort(404)

        vote = data['results'][0]
        cache[key] = vote

    return vote


#
# request lifecycle
#

def is_ios(agent):
    if 'dist' in agent:
        return agent['dist']['name'] in ('iPad', 'iPhone')
    return False


def is_android(agent):
    if 'dist' in agent:
        return agent['dist']['name'] == 'Android'
    return False


# @app.before_request
# def before_request():
#     ua = request.headers.get('User-Agent', '')
#     agent = httpagentparser.detect(ua)
#     g.is_ios = is_ios(agent)
#     g.is_android = is_android(agent)


#
# basic templates and redirects
#

@app.route('/')
def index():

    host = request.headers.get('Host', '')
    if host.lower() == 'cngr.es':
        return redirect('http://congress.sunlightfoundation.com')

    return render_template("index.html")


@app.route('/android')
def android():
    return redirect(ANDROID_URL)


@app.route('/ios')
def ios():
    return redirect(IOS_URL)


@app.route('/code')
def code():
    return redirect('https://github.com/sunlightlabs')


@app.route('/code/android')
def android_code():
    return redirect('https://github.com/sunlightlabs/congress-android')


@app.route('/code/ios')
def io_code():
    return redirect('https://github.com/sunlightlabs/congress-ios')


@app.route('/contact')
def contact():
    return redirect(CONTACT_URL)


@app.route('/urlschemes')
def urlschemes():
    return render_template("urlschemes.html")


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

def opencongress_bill_type(bill_type):
    return 'h' if bill_type == 'hr' else bill_type


def bill_url(bill_id):
    bill = load_bill(bill_id)
    provider = 'opencongress' if COMPROMISE_MORALS else 'govtrack'
    return bill['urls'].get(provider, '/')


@app.route('/b/<bill_id>')
def bill_id(bill_id):
    url = bill_url(bill_id)
    return redirect(url)


@app.route('/b/<bill_id>/text')
def bill_fulltext(bill_id):
    url = re.sub(r'/show/?$', '', bill_url(bill_id))
    return redirect('{0}/text'.format(url))


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
