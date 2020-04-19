# Please see LICENSE.md
import os, json, time;
from flask import (
    Blueprint, request, render_template, redirect, flash, url_for, abort
)
import requests;
from oauthlib.oauth2 import WebApplicationClient;

from . import db_user;

bp = Blueprint('auth', __name__, url_prefix='/auth')

#
# Configuration
#
# I run stuff behind an nginx https server, so OAUTHLIB may see http traffic
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# Load
with open(os.environ.get('GOOGLE_OAUTH_JSON')) as f:
    d = json.load(f);
GOOGLE_CLIENT_ID = d['web']['client_id'];
GOOGLE_CLIENT_SECRET = d['web']['client_secret'];
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
);
# Not ideal, but soit: extract hostname from GOOGLE_OAUTH_JSON
URL_ROOT = [ uri.replace('/auth/redirected','')
             for uri in d['web']['redirect_uris']
             if '/auth/redirected' in uri ][0];


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json();


def construct_google_request_uri():
    print('Constructing google_request_uri');
    # Get google's config for Google login
    google_provider_cfg = get_google_provider_cfg();

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    client = WebApplicationClient(GOOGLE_CLIENT_ID);
    request_uri = client.prepare_request_uri(
        google_provider_cfg["authorization_endpoint"],
        redirect_uri=URL_ROOT + url_for('auth.redirected'),
        scope=["openid", "email", "profile"]
    )
    return request_uri;


# This will be requested often; so (poor man's) cache it
_google_request_uri = None;
_google_request_uri_age = 0;
def get_google_request_uri():
    global _google_request_uri, _google_request_uri_age;
    t = time.perf_counter();
    print('age is %s' % (t - _google_request_uri_age));
    if _google_request_uri is None or (t - _google_request_uri_age) > 3600:
        _google_request_uri = construct_google_request_uri();
        _google_request_uri_age = t;
    return _google_request_uri;


# Static route for privacy policy
@bp.route('/privacy-policy/')
def privacy_policy():
    return render_template('auth/privacy-policy.html');


# Login callback
# Do not change this route lightly, it's also stored in Google's credentials
@bp.route('/redirected')
def redirected():
    # Succesfull
    code = request.args.get("code");
    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg[ "token_endpoint" ];
    # Get the tokens (POST request to Google)
    client = WebApplicationClient(GOOGLE_CLIENT_ID);
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response = request.url,
        redirect_url = URL_ROOT + url_for('auth.redirected'),
        code = code
    )
    token_response = requests.post(
        token_url,
        headers = headers,
        data = body,
        auth = (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )
    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))
    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg[ "userinfo_endpoint" ];
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers = headers, data = body);
    # Ensure their email is verified; get the rest of the details
    if userinfo_response.json().get("email_verified"):
        urj = userinfo_response.json();
        db_user.process_valid_google_login(urj);
        flash("User %s authenticated succesfully" % urj['email']);
    else:
        flash("User email not available or not verified by Google.");
    return redirect(url_for('user.info'));


@bp.route('/login', methods = [ 'GET' ])
def login_show():
    return render_template('auth/login.html',
                           user_details = db_user.get_db_user_details(),
                           request_uri = get_google_request_uri());



