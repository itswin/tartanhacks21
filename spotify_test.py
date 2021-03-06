from pprint import pprint
import time
import sys
import os
import shutil
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import datetime


import lyrics_getter


'''
Make sure you run:

. setup_spotify_environment

before running this script.
'''




def init_spotify():
    scope = "user-read-currently-playing user-read-recently-played playlist-read-private playlist-read-collaborative"
    # scope = "user-read-recently-played"

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    return sp


def get_tracks_from_raw(data):
    final_data_frame = None
    data_for_dataframe = []
    for p in data['items']:
        if p['track'] is None:
            print("[BAD]")
            continue
            # pprint(tracks)
            # pprint(p)
        song_title = p['track']['name']
        artist_name = p['track']['artists'][0]['name']

        played_at = p['played_at']
        data_for_dataframe.append([song_title, artist_name, played_at])

    return pd.DataFrame(data_for_dataframe, columns = ['Name', 'Artist', 'Time'])


def get_playlist_tracks(sp, id, num_tracks):
    TRACK_REQUEST_LIMIT = 100

    all_tracks = None
    playlist_tracks = None

    for index in range(0, num_tracks, TRACK_REQUEST_LIMIT):
        playlist_track_data = sp.playlist_tracks(id, limit=TRACK_REQUEST_LIMIT, offset=index)
        playlist_tracks = get_tracks_from_raw(playlist_track_data)
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
        # pprint(p)
        # break

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
def add_to_tracks(df, new_tracks):
    df.append(new_tracks, ignore_index = True)
    return df
def get_tracks_in_date_range(min_time, max_time, df):
    def inRange(row):
        time_string = row["Time"]
        corresonding_time = datetime.datetime.strptime(time_string,"%Y-%m-%dT%H:%M:%S.%fZ")
        return min_time < corresonding_time and corresonding_time < max_time
    return df[df.apply(inRange, axis=1)]

# def get_mood_in_date_range(raage, tracks):


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

    # cur_track = sp.current_user_playing_track()
    # print(cur_track)

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

        # for song_title, artist_name, lyrics in playlist_lyrics:
        #     title = ''.join(ch for ch in song_title if ch.isalnum())
        #     file_name = song_title + "_" + artist_name + ".txt"
        #     path = folder_name + file_name
        #     with open(path, "w") as f:
        #         f.write(lyrics)

        print()



    # recently_played = get_current_user_recently_played(sp)
    # print(recently_played)

    # for (song_title, artist_name) in recently_played:
    #     print(song_title, artist_name)
    #     song_lyrics = lyrics_getter.get_song_lyrics(song_title, artist_name)
    #
    #     if song_lyrics is not None:
    #         filename = "recently_played_lyrics/" + song_title + "_" + artist_name
    #         with open(filename, "w") as f:
    #             f.write(song_lyrics)
