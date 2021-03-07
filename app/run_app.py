from gevent import monkey
monkey.patch_all()
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import spotify_test as spt
from flask import Flask, redirect, render_template, request
import base64
import requests
import json
from app import app
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyOAuth

clientId = "a8bdd721f4804917bef2258bd38e62c2"
clientSecret = "17248bb726b44503976fdb357cb229d1"

authUrl = "https://accounts.spotify.com/authorize"
tokenUrl = "https://accounts.spotify.com/api/token"
apiUrl = "https://api.spotify.com/v1"

redirectUri = "http://127.0.0.1:5000/app_host"
scope = 'user-read-private user-read-playback-state user-modify-playback-state user-library-read user-read-currently-playing user-read-recently-played playlist-read-private playlist-read-collaborative'

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

@app.route('/app_host')
def spotify_analysis():
    authCode = request.args['code']
    codePayload = {
        "grant_type" : "authorization_code",
        "code" : str(authCode),
        "redirect_uri" : redirectUri
    }
    base64val = base64.b64encode("{}:{}".format(clientId, clientSecret).encode())
    headers = {"Authorization" : "Basic {}".format(base64val.decode())}

    postReq = requests.post(tokenUrl, data = codePayload, headers = headers)
    response = json.loads(postReq.text)
    accessToken = response["access_token"]
    refreshToken = response["refresh_token"]
    tokenType = response["token_type"]
    expiresIn = response["expires_in"]

    sp = spotipy.Spotify(auth = accessToken, auth_manager = auth_manager)

    # print(sp.current_user())
    # all_tracks = spt.get_current_user_recently_played(sp)
    # last_day_tracks = spt.get_tracks_in_date_range(datetime(2021, 3, 6, 0, 0, 0, 0),datetime(2021, 3, 7, 0, 0, 0, 0),all_tracks)
    # information = spt.analyze_playlists(sp)
    # for curr_dict in information:
    # name = information[0]['name']
    # avg_vals = information[0]['averages']
    emotions_list = [["Danceability", "Energy", "Tempo", "Valence"]]
    emotions_list.append(spt.create_vector_values(sp, "happy_songs"))
    emotions_list.append(spt.create_vector_values(sp, "sad_songs"))
    emotions_list.append(spt.create_vector_values(sp, "angry_songs"))


    return render_template('main.html', information = emotions_list)
