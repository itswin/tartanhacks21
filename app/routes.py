from flask import Flask, redirect, render_template, request
import base64
import requests
import json
from app import app
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

clientId = "a8bdd721f4804917bef2258bd38e62c2"
clientSecret = "17248bb726b44503976fdb357cb229d1"

authUrl = "https://accounts.spotify.com/authorize"
tokenUrl = "https://accounts.spotify.com/api/token"
apiUrl = "https://api.spotify.com/v1"

redirectUri = "http://127.0.0.1:5000/spotify_analysis"
scope = 'user-read-private user-read-playback-state user-modify-playback-state user-library-read'

authQueryParams = {
    "response_type" : "code",
    "redirect_uri" : redirectUri,
    "scope" : scope,
    "client_id" : clientId
}

auth_manager = spotipy.oauth2.SpotifyOAuth(client_id = clientId, client_secret = clientSecret, redirect_uri = redirectUri, scope = scope, show_dialog = True)

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/spotify_auth')
def spotify_auth():
    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)

@app.route('/spotify_analysis')
def spotify_analysis():
    authCode = request.args['code']
    codePayload = {
        "grant_type" : "authorization_code",
        "code" : str(authCode),
        "redirect_uri" : redirectUri
    }
    base64val = base64.b64encode("{}:{}".format(clientId, clientSecret).encode())
    headers = {"Authorization" : "Basic {}".format(base64val.decode())}

    print("waiting")
    postReq = requests.post(tokenUrl, data = codePayload, headers = headers)
    print("here now!")
    response = json.loads(postReq.text)
    accessToken = response["access_token"]
    refreshToken = response["refresh_token"]
    tokenType = response["token_type"]
    expiresIn = response["expires_in"]

    sp = spotipy.Spotify(auth = accessToken, auth_manager = auth_manager)

    print(sp.current_user())

    return render_template('main.html', username = sp.current_user())