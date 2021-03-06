from pprint import pprint
import time
import sys
import os
import shutil
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd

import lyrics_getter


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
        data_for_dataframe.append([song_title, artist_name, played_at])
    return pd.DataFrame(data_for_dataframe, columns = ['Name', 'Artist', 'Time'])

def get_sentiment_from_song(sp, title, artist) {
    lyrics = lyrics_getter.get_song_lyrics(title, artist)

}

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
        loudness = song_analysis[0]['loudness']
        liveness = song_analysis[0]['liveness']
        data_for_dataframe.append([song_title, artist_name, danceability, energy, loudness, liveness])
    return pd.DataFrame(data_for_dataframe, columns = ['Name', 'Artist', 'Danceability', 'Energy', 'Loudness', 'Liveness'])

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
    dataframes = []
    for playlist in playlist_data['items']:
        id = playlist['id']
        num_tracks = playlist['tracks']['total']
        dataframes.append(get_playlist_tracks(sp, id, num_tracks))
    return dataframes


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