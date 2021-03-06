from pprint import pprint
import time
import sys
import os
import shutil
import spotipy
from spotipy.oauth2 import SpotifyOAuth

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
    tracks = []
    for p in data['items']:
        if p['track'] is None:
            print("[BAD]")
            continue
            # pprint(tracks)
            # pprint(p)
        song_title = p['track']['name']
        artist_name = p['track']['artists'][0]['name']
        played_at = p['played_at']
        tracks += [(song_title, artist_name, played_at)]

    return tracks


def get_playlist_tracks(sp, id, num_tracks):
    TRACK_REQUEST_LIMIT = 100

    all_tracks = []
    playlist_tracks = None

    for index in range(0, num_tracks, TRACK_REQUEST_LIMIT):
        playlist_track_data = sp.playlist_tracks(id, limit=TRACK_REQUEST_LIMIT, offset=index)
        playlist_tracks = get_tracks_from_raw(playlist_track_data)
        all_tracks += playlist_tracks

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

    for song_title, artist_name in tracks:
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
