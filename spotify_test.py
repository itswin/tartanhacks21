import lyrics_getter
from pprint import pprint
import time
import sys
import os
import shutil
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import datetime
import random

import sentiment_analysis

'''
Make sure you run:

. setup_spotify_environment

before running this script.
'''




def init_spotify():
    scope = "user-read-currently-playing user-read-recently-played playlist-read-private playlist-read-collaborative"

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    return sp


def get_tracks_from_raw(data):
    final_data_frame = None
    data_for_dataframe = []
    for p in data['items']:
        if p['track'] is None:
            print("[BAD]")
            continue
        song_title = p['track']['name']
        artist_name = p['track']['artists'][0]['name']

        played_at = p['played_at']
        id = p['track']['id']
        data_for_dataframe.append([song_title, artist_name, played_at,id])

    return pd.DataFrame(data_for_dataframe, columns = ['Name', 'Artist', 'Time', 'ID', ])

def get_sentiment_from_song(title, artist):
    lyrics = lyrics_getter.get_song_lyrics(title, artist)
    if lyrics is None:
        return None
    analysis = sentiment_analysis.analyze_text_sentiment(lyrics)

    # #junk code for now to not use up cloud requests (CHANGE FOR REAL THING)
    # sign = 1
    # if (math.random()) > 0.5:
    #     sign = -1
    # analysis = {'score' : math.random() * sign, 'magnitude' : math.random()}

    return analysis['score'] * analysis['magnitude']

def get_emotion_value_from_song(title, artist, danceability=0, energy=0, tempo=0, valence=0):
    #possibly update with better heuristic
    sentiment = get_sentiment_from_song(title, artist)
    if sentiment is None:
        sentiment = 0
    return (sentiment * 2) + (danceability * 3) + (energy * 3) + (tempo * 3) + (valence * 3)

def get_emotion_value_from_playlist(zipped, danceability=0, energy=0, tempo=0, valence=0):
    print("getting new emotion value from playlist")
    lyrics = lyrics_getter.get_song_lyrics_batch(zipped)
    # print(lyrics)
    lyrics = ". ".join([l[1] for l in lyrics])
    # analysis = sentiment_analysis.analyze_text_sentiment(lyrics)

    #junk code for now to not use up cloud requests (CHANGE FOR REAL THING)
    sign = 1
    if (random.random()) > 0.5:
        sign = -1
    analysis = {'score' : random.random() * sign, 'magnitude' : random.random()}

    return analysis['score'] * analysis['magnitude']

def get_average_values_from_playlist(dataframe, zipped):
    res = {}
    avg_danceability = dataframe['Danceability'].mean()
    avg_energy = dataframe['Energy'].mean()
    avg_tempo = dataframe['Tempo'].mean()
    avg_valence = dataframe['Valence'].mean()
    avg_emotion = get_emotion_value_from_playlist(zipped, avg_danceability, avg_energy, avg_tempo, avg_valence)

    res['Danceability'] = avg_danceability
    res['Energy'] = avg_energy
    res['Tempo'] = avg_tempo
    res['Valence'] = avg_valence
    res['Emotion Score'] = avg_emotion

    return res

def get_playlist_tracks_from_raw(data, sp):
    final_data_frame = None
    data_for_dataframe = []
    for p in data['items']:
        if p['track'] is None:
            print("[BAD]")
            continue
        song_title = p['track']['name']
        artist_name = p['track']['artists'][0]['name']
        song_id = p['track']['id']
        if not song_id:
            print("[BAD]")
            continue
        song_analysis = sp.audio_features([song_id])
        if not song_analysis:
            print("[BAD]")
            continue
        danceability = song_analysis[0]['danceability']
        energy = song_analysis[0]['energy']
        tempo = song_analysis[0]['tempo']
        valence = song_analysis[0]['valence']
        # emotion_score = get_emotion_value_from_song(song_title, artist_name, danceability, energy, tempo, valence)
        data_for_dataframe.append([song_title, artist_name, danceability, energy, tempo, valence])
    return pd.DataFrame(data_for_dataframe, columns = ['Name', 'Artist', 'Danceability', 'Energy', 'Tempo', 'Valence'])

def get_playlist_tracks(sp, id, num_tracks):
    TRACK_REQUEST_LIMIT = 100

    all_tracks = None
    playlist_tracks = None

    for index in range(0, num_tracks, TRACK_REQUEST_LIMIT):
        playlist_track_data = sp.playlist_tracks(id, limit=TRACK_REQUEST_LIMIT, offset=index)
        playlist_tracks = get_playlist_tracks_from_raw(playlist_track_data, sp)
        if all_tracks is None: all_tracks = playlist_tracks
        else: all_tracks.append(playlist_tracks, ignore_index=True)

    return all_tracks


'''
Returns an array of tuples (playlist_name, playlist_id, playlist_track_count)
'''
def get_current_user_playlists(sp):
    playlist_data = sp.current_user_playlists()

    playlists = []
    for p in playlist_data['items']:
        playlists += [(p['name'], p['id'], p['tracks']['total'])]

    return playlists


def get_current_user_recently_played(sp):
    recently_played_data = sp.current_user_recently_played(limit=50)

    recently_played = get_tracks_from_raw(recently_played_data)

    return recently_played


def get_playlist_lyrics(name, id, num_tracks):
    playlist_lyrics = []
    print(name)
    tracks = get_playlist_tracks(sp, id, num_tracks)
    print("[FOUND SONGS]", len(tracks), "songs")

    for track_item in tracks.iterrows():
        song_title, artist_name, played_at = track_item["Name"], track_item["Artist"], track_item["Time"]
        lyrics = lyrics_getter.get_song_lyrics(song_title, artist_name)
        if lyrics is not None:
            playlist_lyrics += [(song_title, artist_name, lyrics)]

            folder_name = "lyrics/" + name + "/"
            title = ''.join(ch for ch in song_title if ch.isalnum())
            file_name = title + "_" + artist_name + ".txt"
            path = folder_name + file_name
            with open(path, "w") as f:
                f.write(lyrics)

    print("[FOUND LYRICS]", len(playlist_lyrics), "songs")

    return playlist_lyrics

def analyze_playlists(sp):
    playlist_data = sp.current_user_playlists()
    information = []
    for playlist in playlist_data['items']:
        id = playlist['id']
        num_tracks = playlist['tracks']['total']
        name = playlist['name']
        curr_dataframe = get_playlist_tracks(sp, id, num_tracks)

        names = curr_dataframe['Name'].tolist()
        artists = curr_dataframe['Artist'].tolist()
        zipped = list(zip(names, artists))

        curr_avg_vals = get_average_values_from_playlist(curr_dataframe, zipped)
        curr_dict = {'name' : name, 'dataframe' : curr_dataframe, 'averages' : curr_avg_vals}
        information.append(curr_dict)

    return information

def add_to_tracks(df, new_tracks):
    df.append(new_tracks, ignore_index = True)
    return df

def get_tracks_in_date_range(min_time, max_time, df):
    def inRange(row):
        time_string = row["Time"]
        corresonding_time = datetime.datetime.strptime(time_string,"%Y-%m-%dT%H:%M:%S.%fZ")
        return min_time < corresonding_time and corresonding_time < max_time
    return df[df.apply(inRange, axis=1)]

def get_mood_in_date_range(min_time, max_time, tracks):
    pd = get_tracks_in_date_range(min_time, max_time, tracks)
    



def get_tracks_from_raw_rec(data):
    tracks = []
    for p in data['tracks']:
        song_title = p['name']
        artist_name = p['artists'][0]['name']
        tracks += [(song_title, artist_name)]

    return tracks


'''
Valid types are album, artist, playlist, track, show, and episode.
'''
def get_spotify_ids(sp, queries, type='track'):
    if not queries:
        return queries

    key = type + 's'
    ids = []
    for q in queries:
        res = sp.search(q, limit=1, offset=0, type=type)
        id = res[key]['items'][0]['id']
        ids.append(id)

    return ids


'''
Need at least one of seed_artists, seed_genres, seed_tracks
1-5 seeds per type.

attributes is a dict with each target attribute (e.g. min_valence, target_liveness)

Returns a list of tuple (song_title, artist_name)
'''
def get_recommendations(sp, seed_artists=None, seed_genres=None, seed_tracks=None, attributes=None):
    seed_artist_ids = get_spotify_ids(sp, seed_artists, 'artist')
    seed_track_ids = get_spotify_ids(sp, seed_tracks, 'track')

    if attributes:
        recs = sp.recommendations(seed_artists=seed_artist_ids, seed_genres=seed_genres, seed_tracks=seed_track_ids, **attributes)
    else:
        recs = sp.recommendations(seed_artists=seed_artist_ids, seed_genres=seed_genres, seed_tracks=seed_track_ids)

    return get_tracks_from_raw_rec(recs)


if __name__ == "__main__":
    sp = init_spotify()

    playlists = get_current_user_playlists(sp)
    print(playlists)
    print()

    for name, id, num_tracks in playlists:
        folder_name = "lyrics/" + name + "/"
        if os.path.isdir(folder_name):
            shutil.rmtree(folder_name)
        os.makedirs(folder_name)

    for name, id, num_tracks in playlists:
        playlist_lyrics = get_playlist_lyrics(name, id, num_tracks)

        print()
