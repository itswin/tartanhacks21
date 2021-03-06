import requests
from pprint import pprint
from bs4 import BeautifulSoup

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
    return "\n".join(ret)

'''
Removes all new line characters from lyrics
Might be needed for NLP?
'''
def flatten_lyrics(lyrics):
    return lyrics.replace("\n", " ")


def postprocessing_lyrics(lyrics):
    lyrics = lyrics.strip()
    lyrics = cleanup_lyrics(lyrics)
    lyrics = flatten_lyrics(lyrics)
    return lyrics


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

    print("Found song", remote_song_title, remote_artist_name)
    print("Song URL:", song_url)

    song_lyrics = scrape_song_url(song_url)
    song_lyrics = postprocessing_lyrics(song_lyrics)

    return song_lyrics


def get_input():
    return input("Song title: "), input("Artist name: ")


if __name__ == "__main__":
    with open("sample_songs.txt", "r") as f:
        lines = f.readlines()
        song_list = [x.strip() for x in lines[0::2]]
        artist_list = [x.strip() for x in lines[1::2]]

    for i in range(len(artist_list)):
        print("[GET]", song_list[i], artist_list[i])
        filename = "lyrics/" + song_list[i] + "_" + artist_list[i]
        song_lyrics = get_song_lyrics(song_list[i], artist_list[i])

        if song_lyrics is not None:
            with open(filename, "w") as f:
                f.write(song_lyrics)
            # print(song_lyrics)

    while True:
        song_title, artist_name = get_input()
        song_lyrics = get_song_lyrics(song_title, artist_name)
        print(song_lyrics)
