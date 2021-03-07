from bs4 import BeautifulSoup
import grequests
import requests
from pprint import pprint

# from gevent import monkey as curious_george
# curious_george.patch_all(thread=False, select=False)



# Genius API stuff from here:
# https://dev.to/willamesoares/how-to-integrate-spotify-and-genius-api-to-easily-crawl-song-lyrics-with-python-4o62

CLIENT_ACCESS_TOKEN = 'cGnIJArtyxYY2VXGPsv7P9SJbL5MoldKpReMn_5FPJ8YLOA_kcbUOWpbaZmfAqEk'


def request_song_info(song_title, artist_name):
    base_url = 'https://api.genius.com'
    headers = {'Authorization': 'Bearer ' + CLIENT_ACCESS_TOKEN}
    search_url = base_url + '/search'
    data = {'q': song_title + ' ' + artist_name}
    response = requests.get(search_url, data=data, headers=headers)

    return response


def request_song_info_batch(tracks):
    base_url = 'https://api.genius.com'
    headers = {'Authorization': 'Bearer ' + CLIENT_ACCESS_TOKEN}
    search_url = base_url + '/search'

    batch_data = [{'q': song_title + ' ' + artist_name} for song_title, artist_name in tracks]

    reqs = [grequests.get(search_url, data=data, headers=headers) for data in batch_data]

    responses = grequests.map(reqs)

    return responses


def scrape_song_url(url):
    page = requests.get(url)
    html = BeautifulSoup(page.text, 'html.parser')
    lyrics = html.find('div', class_='lyrics').get_text()

    return lyrics


'''
Genius lyrics have things like: "[Intro], [Chorus], etc"
Removes those sections from the lyrics
TODO: What to do about lyrics in parenthesis
'''
def cleanup_lyrics(lyrics):
    ret = []
    lines = lyrics.split("\n")
    for l in lines:
        if "[" not in l:
            ret += [l]
    return " ".join(ret)

'''
Removes all new line characters from lyrics
Might be needed for NLP?
'''
# def flatten_lyrics(lyrics):
#     return lyrics.replace("\n", " ")
# just modify the join


def postprocessing_lyrics(lyrics):
    lyrics = lyrics.strip()
    lyrics = cleanup_lyrics(lyrics)
    # lyrics = flatten_lyrics(lyrics)
    return lyrics


def get_url_from_genius(track, response):
    artist_name = track[1]

    json = response.json()
    remote_song_info = None

    # print(json)
    # print(artist_name)
    # pprint(json)

    for hit in json['response']['hits']:
        # print('consider', hit['result']['primary_artist']['name'])
        # pprint(hit)
        if artist_name.lower() in hit['result']['primary_artist']['name'].lower():
            remote_song_info = hit
            break

    # pprint(remote_song_info)
    if remote_song_info is None:
        # print("Could not find song/artist")
        return None

    remote_song_title, remote_artist_name = remote_song_info['result']['title'], remote_song_info['result']['primary_artist']['name']
    song_url = remote_song_info['result']['url']
    return song_url



def get_song_lyrics(song_title, artist_name):
    # print("getting", song_title, artist_name)

    response = request_song_info(song_title, artist_name)
    json = response.json()
    remote_song_info = None

    # print(json)
    # pprint(json)

    for hit in json['response']['hits']:
        # print('consider', hit['result']['primary_artist']['name'])
        # pprint(hit)
        if artist_name.lower() in hit['result']['primary_artist']['name'].lower():
            remote_song_info = hit
            break

    # pprint(remote_song_info)
    if remote_song_info is None:
        print("Could not find song/artist")
        return None

    remote_song_title, remote_artist_name = remote_song_info['result']['title'], remote_song_info['result']['primary_artist']['name']
    song_url = remote_song_info['result']['url']

    # print("Found song", remote_song_title, remote_artist_name)
    # print("Song URL:", song_url)

    song_lyrics = scrape_song_url(song_url)
    song_lyrics = postprocessing_lyrics(song_lyrics)

    return song_lyrics


def get_song_lyrics_batch(tracks):
    print("-----[START GET BATCH]")
    # print(tracks)

    '''
    song_infos = []
    for song_title, artist_name in tracks:
        response = request_song_info(song_title, artist_name)
        json = response.json()
        remote_song_info = None

        # print(json)
        # pprint(json)

        for hit in json['response']['hits']:
            # print('consider', hit['result']['primary_artist']['name'])
            # pprint(hit)
            if artist_name.lower() in hit['result']['primary_artist']['name'].lower():
                remote_song_info = hit
                break

        # pprint(remote_song_info)
        if remote_song_info is None:
            print("Could not find song/artist")
            continue

        remote_song_title, remote_artist_name = remote_song_info['result']['title'], remote_song_info['result']['primary_artist']['name']
        song_url = remote_song_info['result']['url']

        print("Found song", remote_song_title, remote_artist_name)
        print("Song URL:", song_url)

        song_infos += [(remote_song_title, remote_artist_name, song_url)]

    # print("---[SONGS]---")
    # print(song_infos)

    reqs = [grequests.get(x[2]) for x in song_infos]
    '''
    song_infos = request_song_info_batch(tracks)
    song_urls = [get_url_from_genius(tracks[i], song_infos[i]) for i in range(len(tracks))]

    temp = []
    reqs = []
    for i in range(len(song_urls)):
        if song_urls[i] is not None:
            reqs += [grequests.get(song_urls[i])]
            temp += [tracks[i]]

    print("len", len(reqs))

    responses = grequests.map(reqs)

    print("batch responses")
    # print(responses)

    batch_lyrics = []

    for i in range(len(responses)):
        html = BeautifulSoup(responses[i].text, 'html.parser')
        lyrics = html.find('div', class_='lyrics').get_text()
        lyrics = postprocessing_lyrics(lyrics)
        batch_lyrics += [(tracks[i], lyrics)]
        # print(lyrics)
        # break

    print("done")

    return batch_lyrics


def get_input():
    return input("Song title: "), input("Artist name: ")


if __name__ == "__main__":
    with open("reference_songs/sad_songs.txt", "r") as f:
        lines = f.readlines()
        song_list = [x.strip() for x in lines[0::2]]
        artist_list = [x.strip() for x in lines[1::2]]

    for i in range(len(artist_list)):
        print("[GET]", song_list[i], artist_list[i])
        filename = "lyrics/" + song_list[i] + "_" + artist_list[i] + ".txt"
        song_lyrics = get_song_lyrics(song_list[i], artist_list[i])

        if song_lyrics is not None:
            with open(filename, "w") as f:
                f.write(song_lyrics)
            # print(song_lyrics)

    while True:
        song_title, artist_name = get_input()
        song_lyrics = get_song_lyrics(song_title, artist_name)
        print(song_lyrics)
