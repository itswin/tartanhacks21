from gevent import monkey
monkey.patch_all()
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import spotify_test as spt
from flask import Flask, redirect, render_template, request, Response
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
import base64
import requests
import json
from app import app
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from wtforms import StringField, SubmitField, SelectField, RadioField
from wtforms.fields.html5 import IntegerRangeField
from wtforms.validators import DataRequired, NumberRange

genre_map = dict([(1,"Pop"), 
            (2,"hip-hop"),
            (3,"Rock"),
            (4,"edm"),
            (5,"Latin"),
            (6,"alt_rock"),
            (7,"Classical"),
            (9,"Country"),
            (10,"Metal")])

limit_map = dict([(1,"10"), 
            (2,"20"),
            (3,"30"),
            (4,"40"),
            (5,"50"),
            (6,"60"),
            (7,"70"),
            (8,"80"),
            (9,"90"),
            (10,"100")])

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import base64
import io

class RecommendationForm(FlaskForm):
    # acoustic = RadioField('Acoustic Level:', choices = [(1,"10%")])
    acoustic = IntegerRangeField('Acousticness', [NumberRange(min=0, max=100)])
    danceable = IntegerRangeField('Danceability', [NumberRange(min=0, max=100)])
    energy = IntegerRangeField('Energy', [NumberRange(min=0, max=100)])
    positivity = IntegerRangeField('Positivity', [NumberRange(min=0, max=100)])
    instrumental = IntegerRangeField('Instrumentalness', [NumberRange(min=0, max=100)])
    liveness = IntegerRangeField('Liveness', [NumberRange(min=0, max=100)])
    genre = SelectField('Genre To Base Off Of', choices = [(1,"Pop"), 
                                                            (2,"Hip Hop/Rap"),
                                                            (3,"Rock"),
                                                            (4,"Dance/EDM"),
                                                            (5,"Latin"),
                                                            (6,"Indie/Alternative"),
                                                            (7,"Classical"),
                                                            (9,"Country"),
                                                            (10,"Metal")])
    limit = SelectField('How Many Songs to Search For', choices = [(1,"10"), 
                                                            (2,"20"),
                                                            (3,"30"),
                                                            (4,"40"),
                                                            (5,"50"),
                                                            (6,"60"),
                                                            (7,"70"),
                                                            (8,"80"),
                                                            (9,"90"),
                                                            (10,"100")])
    submit = SubmitField('Search')

clientId = "a8bdd721f4804917bef2258bd38e62c2"
clientSecret = "17248bb726b44503976fdb357cb229d1"

authUrl = "https://accounts.spotify.com/authorize"
tokenUrl = "https://accounts.spotify.com/api/token"
apiUrl = "https://api.spotify.com/v1"

refreshToken = None

redirectUri = "http://127.0.0.1:5000/app_host"
scope = 'user-read-private user-read-playback-state user-modify-playback-state user-library-read user-read-currently-playing user-read-recently-played playlist-read-private playlist-read-collaborative'

authQueryParams = {
    "response_type" : "code",
    "redirect_uri" : redirectUri,
    "scope" : scope,
    "client_id" : clientId
}

auth_manager = spotipy.oauth2.SpotifyOAuth(client_id = clientId, client_secret = clientSecret, redirect_uri = redirectUri, scope = scope, show_dialog = True)
token_info = auth_manager.get_cached_token()
sp = None

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/spotify_auth')
def spotify_auth():
    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)

@app.route('/app_host', methods=['GET','POST'])
def spotify_analysis():
    global refreshToken
    global token_info
    global sp
    # print(auth_manager.is_token_expired(token_info))
    if (request.method == 'POST'):
        print("here inside post request")
        token_info = auth_manager.refresh_access_token(refreshToken)
        token = token_info['access_token']
        sp = spotipy.Spotify(auth = token, auth_manager = auth_manager)
        print("created new post request sp")
    else:
    # authCode = None
    # if request.method == 'POST':
    #     print("here from form submission, refresh token is " + str(refreshToken))
    #     auth_manager.refresh_access_token(refreshToken)
    # else:
        authCode = request.args['code']
        # print(authCode)
        codePayload = {
            "grant_type" : "authorization_code",
            "code" : str(authCode),
            "redirect_uri" : redirectUri
        }
        base64val = base64.b64encode("{}:{}".format(clientId, clientSecret).encode())
        headers = {"Authorization" : "Basic {}".format(base64val.decode())}

        postReq = requests.post(tokenUrl, data = codePayload, headers = headers)
        response = json.loads(postReq.text)
        # print(response)
        accessToken = response["access_token"]
        refreshToken = response["refresh_token"]
        tokenType = response["token_type"]
        expiresIn = response["expires_in"]

        sp = spotipy.Spotify(auth = accessToken, auth_manager = auth_manager)

    # auth_manager.refresh_access_token(refreshToken)

    # print(sp.current_user())
    recently_played_info = spt.analyze_user_recently_played(sp)
    # last_day_tracks = spt.get_tracks_in_date_range(datetime(2021, 3, 6, 0, 0, 0, 0),datetime(2021, 3, 7, 0, 0, 0, 0),all_tracks)
    playlist_info = spt.analyze_playlists(sp)
    # for curr_dict in information:
    # name = information[0]['name']
    # # avg_vals = information[0]['averages']
    # emotions_list = [["Danceability", "Energy", "Tempo", "Valence"]]
    # emotions_list.append(spt.create_vector_values(sp, "happy_songs"))
    # emotions_list.append(spt.create_vector_values(sp, "sad_songs"))
    # emotions_list.append(spt.create_vector_values(sp, "angry_songs"))

    #create the form
    print("beforehere")
    form = RecommendationForm()
    print("here")
    message = ""
    if form.validate_on_submit():
        print(genre_map)
        genre_seed = [genre_map[int(form.genre.data)].lower()]
        limit = int(limit_map[int(form.limit.data)])
        acousticness = int(form.acoustic.data) / 100
        danceability = int(form.danceable.data) / 100
        energy = int(form.energy.data) / 100
        positivity = int(form.positivity.data) / 100
        instrumental = int(form.instrumental.data) / 100
        liveness = int(form.liveness.data) / 100
        attributes = {'target_acousticness' : acousticness,
                      'target_danceability' : danceability,
                      'target_energy' : energy,
                      'target_valence' : positivity,
                      'target_instrumentalness' : instrumental}
        print(genre_seed)
        print(attributes)
        recommendations = spt.get_recommendations(sp, seed_genres=genre_seed, attributes=attributes, limit=limit)
        print(recommendations)
        message = recommendations
        print("submitted form")
    print("here2")
    # form = None


    for info in playlist_info:
        info['averages']['Danceability'] = round(info['averages']['Danceability'], 2)
        info['averages']['Energy'] = round(info['averages']['Energy'], 2)
        info['averages']['Tempo'] = round(info['averages']['Tempo'], 2)

    recently_played_info['averages']['Danceability'] = round(recently_played_info['averages']['Danceability'], 2)
    recently_played_info['averages']['Energy'] = round(recently_played_info['averages']['Energy'], 2)
    recently_played_info['averages']['Tempo'] = round(recently_played_info['averages']['Tempo'], 2)

    return render_template('landing_page.html', playlist_info = playlist_info, recently_played_info = recently_played_info,
                                                form = form,
                                                form_submit_msg = message)

@app.route('/mood_graph.png')
def get_mood_graph():
    global sp

    # create recently played mood graph
    df = spt.get_recent_moods(sp)

    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    df.plot(x='Time', y='Mood', ax=ax, color='#f44336')
    plt.xlabel("Date")
    plt.ylabel("Mood")

    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')



@app.route('/asdf')
def hello():
    print("got here in hello")
