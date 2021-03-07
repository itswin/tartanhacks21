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
import math

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

def create_vector_values(sp,txt):
    song_list, artist_list = None, None
    with open("reference_songs/" + txt + ".txt", "r") as f:
        lines = f.readlines()
        song_list = [x.strip() for x in lines[0::2]]
        artist_list = [x.strip() for x in lines[1::2]]
    track_ids = []
    for index in range(len(song_list)):
        track, artist = song_list[index], artist_list[index]

        track_id = sp.search(q='track:' + track, limit=1,type='track')
        track_id = track_id['tracks']['items'][0]['id']
        track_ids.append(track_id)
    main_frame = pd.DataFrame()
    main_frame['Song ID'] = track_ids
    final_audio_features = []
    all_song_ids = main_frame['Song ID']
    num_songids = len(all_song_ids)
    # print("song ids:" + str(num_songids))
    TRACK_REQUEST_LIMIT = 100
    for index in range(0, num_songids, TRACK_REQUEST_LIMIT):
        print(index)
        curr_songids = all_song_ids[index:min(num_songids, index + TRACK_REQUEST_LIMIT)]
        features = sp.audio_features(curr_songids)
        final_audio_features += features

    danceabilities = [features['danceability'] for features in final_audio_features]
    energies = [features['energy'] for features in final_audio_features]
    tempos = [features['tempo'] for features in final_audio_features]
    valences = [features['valence'] for features in final_audio_features]

    # print(len(all_tracks))
    # print(len(danceabilities))

    main_frame['Danceability'] = danceabilities
    main_frame['Energy'] = energies
    main_frame['Tempo'] = tempos
    main_frame['Valence'] = valences
    return (main_frame['Danceability'].mean(),main_frame['Energy'].mean(), main_frame['Tempo'].mean(),main_frame['Valence'].mean())

def classify_song_emotion(song_values): #song values is the tuple of the values of the song we are trying to classify in order "Danceability", "Energy", "Tempo", "Valence"
    def error(v1, v2):
        temp = 0
        for i in range(len(v1)):
            currV1 = v1[i]
            currV2 = v2[i]
            temp += abs(currV1 - currV2)
        return math.sqrt(temp)

    classifier_dict = {"Happy": (0.6575, 0.6685, 124.95204999999999, 0.6319), "Sad": (0.52105, 0.43390000000000006, 111.12160000000002, 0.27843999999999997), "Angry": (0.6049, 0.7454500000000001, 108.40515, 0.5322499999999999)}
    best_error = float('inf')
    best_emotion = None
    for key, value in classifier_dict.items():
        if error(value, song_values) < best_error:
            best_error = error(value, song_values)
            best_emotion = key
    return best_emotion


def get_tracks_from_raw(sp, data):
    TRACK_REQUEST_LIMIT = 100
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

    main_frame =pd.DataFrame(data_for_dataframe, columns = ['Name', 'Artist', 'Time', 'Song ID'])

    final_audio_features = []
    all_song_ids = main_frame['Song ID']
    num_songids = len(all_song_ids)
    # print("song ids:" + str(num_songids))
    for index in range(0, num_songids, TRACK_REQUEST_LIMIT):
        # print(index)
        curr_songids = all_song_ids[index:min(num_songids, index + TRACK_REQUEST_LIMIT)]
        features = sp.audio_features(curr_songids)
        final_audio_features += features

    danceabilities = [features['danceability'] for features in final_audio_features]
    energies = [features['energy'] for features in final_audio_features]
    tempos = [features['tempo'] for features in final_audio_features]
    valences = [features['valence'] for features in final_audio_features]

    # print(len(all_tracks))
    # print(len(danceabilities))

    main_frame['Danceability'] = danceabilities
    main_frame['Energy'] = energies
    main_frame['Tempo'] = tempos
    main_frame['Valence'] = valences


    return main_frame

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

# Change to True to execute sentiment analysis ONCE
callSentimentAnalysis = False
def get_emotion_value_from_playlist(zipped=None, danceability=0, energy=0, tempo=0, valence=0):
    global callSentimentAnalysis
    # print("getting new emotion value from playlist", callSentimentAnalysis)
    analysis = None
    if zipped is not None and callSentimentAnalysis:
        callSentimentAnalysis = False
        lyrics = lyrics_getter.get_song_lyrics_batch(zipped)
        # print(lyrics)
        lyrics = [l[1] for l in lyrics]

        # 25, 5
        MAX_SAMPLE_LEN = 6
        MAX_BATCH_LEN = 3
        sampled_lyrics = random.sample(lyrics, min(MAX_SAMPLE_LEN, len(lyrics)))
        batched_lyrics = [". ".join(sampled_lyrics[i:i+MAX_BATCH_LEN]) for i in range (0, len(sampled_lyrics), MAX_BATCH_LEN)]

        analyses = [sentiment_analysis.analyze_text_sentiment_workaround(batch) for batch in batched_lyrics]
        analysis = {'score' : sum(res['score'] for res in analyses) / len(analyses),
                    'magnitude' :  sum(res['magnitude'] for res in analyses) / len(analyses)}
    else:
        #junk code for now to not use up cloud requests (CHANGE FOR REAL THING)
        sign = 1
        if (random.random()) > 0.5:
            sign = -1
        analysis = {'score' : random.random() * sign, 'magnitude' : random.random()}

    sentiment = analysis['score'] * analysis['magnitude']

    return (sentiment * 2) + (danceability * 3) + (energy * 3) + (tempo * 3) + (valence * 3)

def get_average_values_from_playlist(dataframe, zipped=None):
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
        # song_analysis = sp.audio_features([song_id])
        # if not song_analysis:
        #     print("[BAD]")
        #     continue
        # danceability = song_analysis[0]['danceability']
        # energy = song_analysis[0]['energy']
        # tempo = song_analysis[0]['tempo']
        # valence = song_analysis[0]['valence']
        # # emotion_score = get_emotion_value_from_song(song_title, artist_name, danceability, energy, tempo, valence)
        data_for_dataframe.append([song_title, artist_name, song_id])
    return pd.DataFrame(data_for_dataframe, columns = ['Name', 'Artist', 'Song ID'])

def get_playlist_tracks(sp, id, num_tracks):
    TRACK_REQUEST_LIMIT = 100

    all_tracks = None
    playlist_tracks = None

    for index in range(0, num_tracks, TRACK_REQUEST_LIMIT):
        playlist_track_data = sp.playlist_tracks(id, limit=TRACK_REQUEST_LIMIT, offset=index)
        playlist_tracks = get_playlist_tracks_from_raw(playlist_track_data, sp)
        if all_tracks is None:
            all_tracks = playlist_tracks
        else:
            all_tracks = all_tracks.append(playlist_tracks, ignore_index=True)

    final_audio_features = []
    all_song_ids = all_tracks['Song ID']
    num_songids = len(all_song_ids)
    # print("song ids:" + str(num_songids))
    for index in range(0, num_songids, TRACK_REQUEST_LIMIT):
        # print(index)
        curr_songids = all_song_ids[index:min(num_songids, index + TRACK_REQUEST_LIMIT)]
        features = sp.audio_features(curr_songids)
        final_audio_features += features

    danceabilities = [features['danceability'] for features in final_audio_features]
    energies = [features['energy'] for features in final_audio_features]
    tempos = [features['tempo'] for features in final_audio_features]
    valences = [features['valence'] for features in final_audio_features]

    # print(len(all_tracks))
    # print(len(danceabilities))

    all_tracks['Danceability'] = danceabilities
    all_tracks['Energy'] = energies
    all_tracks['Tempo'] = tempos
    all_tracks['Valence'] = valences

    # print("done")

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

    recently_played = get_tracks_from_raw(sp, recently_played_data)

    return recently_played

def analyze_user_recently_played(sp):
    tracks_dataframe = get_current_user_recently_played(sp)
    curr_avg_vals = get_average_values_from_playlist(tracks_dataframe)
    curr_emotion = classify_song_emotion((curr_avg_vals['Danceability'],
                                              curr_avg_vals['Energy'],
                                              curr_avg_vals['Tempo'],
                                              curr_avg_vals['Valence']))
    curr_dict = {'averages' : curr_avg_vals, 'emotion' : curr_emotion}
    return curr_dict

def get_playlist_lyrics(sp, name, id, num_tracks):
    playlist_lyrics = []
    print(name)
    tracks = get_playlist_tracks(sp, id, num_tracks)
    print("[FOUND SONGS]", len(tracks), "songs")

    for index, track_item in tracks.iterrows():
        print(track_item)
        song_title, artist_name = track_item["Name"], track_item["Artist"]
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
        curr_emotion = classify_song_emotion((curr_avg_vals['Danceability'],
                                              curr_avg_vals['Energy'],
                                              curr_avg_vals['Tempo'],
                                              curr_avg_vals['Valence']))
        curr_dict = {'name' : name, 'dataframe' : curr_dataframe, 'averages' : curr_avg_vals, 'emotion' : curr_emotion}
        information = information.append(curr_dict)

    return information

def add_to_tracks(df, new_tracks):
    df = df.append(new_tracks, ignore_index = True)
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

    return get_tracks_from_raw_rec(sp, recs)

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
        playlist_lyrics = get_playlist_lyrics(sp, name, id, num_tracks)

        print()
