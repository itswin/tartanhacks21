import spotify_test
import lyrics_getter
import sentiment_analysis
import os, shutil
import pandas as pd
import datetime


def get_all_songs(sp):
    playlist_data = sp.current_user_playlists()
    all_data = []

    index = 0

    for playlist in playlist_data['items']:
        id = playlist['id']
        num_tracks = playlist['tracks']['total']
        name = playlist['name']
        curr_dataframe = spotify_test.get_playlist_tracks(sp, id, num_tracks)

        print(name, num_tracks)
        names = curr_dataframe['Name'].tolist()
        artists = curr_dataframe['Artist'].tolist()

        tracks = [(names[i], artists[i]) for i in range(len(names))]
        tracks = tracks[:100]
        lyrics = lyrics_getter.get_song_lyrics_batch(tracks)

        lyrics_dict = {l[0][0]: l[1] for l in lyrics}

        filtered_data = []
        for index, row in curr_dataframe.iterrows():
            if row['Name'] in lyrics_dict:
                new_row = list(row) + [lyrics_dict[row['Name']]]
                all_data += [new_row]

        print(len(lyrics))

        new_columns = [x for x in curr_dataframe.columns] + ["Lyrics"]

        if index == 5:
            break

        index += 1

    all_dataframe = pd.DataFrame(data=all_data, columns=new_columns)
    print(all_dataframe)
    return all_dataframe


def add_timestamps(df):
    start_date = datetime.datetime.now() + datetime.timedelta(days=-df.shape[0])
    df['Time'] = [start_date + datetime.timedelta(days=i) for i in range(df.shape[0])]


def add_sentiment_data(df):
    sent_score = []
    sent_mag = []

    all_lyrics = [row['Lyrics'] for i, row in df.iterrows()]

    batch_size = 10
    for i in range(0, len(all_lyrics), batch_size):
        # all_lyrics = all_lyrics[:5]
        # print(all_lyrics[0])
        # print(len(all_lyrics))
        print("row", i)
        res = sentiment_analysis.analyze_text_sentiment_batch(all_lyrics[i: min(i+batch_size, len(all_lyrics))])
        sent_score += [r['score'] for r in res]
        sent_mag += [r['magnitude'] for r in res]
        save_df = pd.DataFrame(data=[sent_score, sent_mag])
        save_df.to_csv("temp_save/temp" + str(i) + ".csv")

    df['sentiment_score'] = sent_score
    df['sentiment_mag'] = sent_mag


if __name__ == "__main__":
    sp = spotify_test.init_spotify()

    # playlists = spotify_test.get_current_user_playlists(sp)
    # print(playlists)
    # print()
    # result = get_all_songs(sp)
    # print("SAVING")
    # result.to_csv("example_data.csv")

    # df = pd.read_csv("example_data.csv")
    # print(df)
    #
    # add_timestamps(df)
    # print(df)
    # df.to_csv("example_data_timed.csv")
    #
    # add_sentiment_data(df)
    # df.to_csv("example_data_sentiment.csv")

    df = pd.read_csv("example_data_sentiment.csv")
    print(df)

    df = df.drop(columns='Lyrics')
    print(df)
    df.to_csv("example_data_clean.csv")
