from matplotlib import artist
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials 
import requests
import os
import time
import numpy as np
import re
from tqdm import tqdm
from configparser import ConfigParser

''' Defining some important variables like the spotify client id and secret and creating an instance of the spotify's api'''
configur = ConfigParser()
configur.read('config.ini')
client_id = configur['main']['client_id']
client_secret = configur['main']['client_secret']
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager) # sp is the instance of the spotipy api
sleep_min = 1
sleep_max = 3



'''
This method is used to pre-process our text
'''
def pre_process_text(text):
    text = text.lower()
    text = re.sub(r'[^\x00-\x7F]+',' ', text)
    return text


def clean_data(artists,titles):
    artists_clean = []
    titles_clean = []
    for i in tqdm(range(len(artists))):
        artists_clean.append(pre_process_text(artists[i]))
        titles_clean.append(pre_process_text(titles[i]))
    return artists_clean, titles_clean


'''
In is_same_artist_and_title function I check whether the artist the we found in our query is the same one from our dataset.
'''
def is_same_artist_and_title(query, artist, title, index):
    is_same_artist = pre_process_text(artist[index]) in pre_process_text(query['tracks']['items'][0]['artists'][0]['name'])
    is_same_title = pre_process_text(title[index]) in pre_process_text(query['tracks']['items'][0]['name'])
    return is_same_artist and is_same_title


'''
In track_preview_available function I am checking that the query returned by spotify's api is not empty and if its not I check if the preview url is available.
'''
def track_preview_available(query):
    if query['tracks']['items']:
        if query['tracks']['items'][0]['preview_url']:
            return True
        return True


def extract_track_data(artists_clean, titles_clean,artists,titles):

    preview_url = []
    track_id = []
    artist_id = []
    track_popularity = []
    artists_df = []
    titles_df = []

    request_count = 0
    start_time = time.time()
    for index in tqdm(range(len(artists_clean))):
        artist_name = artists_clean[index]
        song_title = titles_clean[index]
        search = f'artist:{artist_name} track:{song_title}'
        query = sp.search(search, type='track')

        # in the below line of code I am checking that the query returned by spotify's api is not empty and if its not I check if the preview url is available, and
        # even further I check a third condition whether the artist the we found in our query is the same from our dataset.

        # if query['tracks']['items'] and query['tracks']['items'][0]['preview_url'] and query['tracks']['items'][0]['artists'][0]['name'] in alpha_artists_titles[index]:
        if track_preview_available(query) and is_same_artist_and_title(query,artists,titles,index):
            preview_url.append(query['tracks']['items'][0]['preview_url'])
            track_id.append(query['tracks']['items'][0]['id'])
            artist_id.append(query['tracks']['items'][0]['artists'][0]['id'])
            track_popularity.append(query['tracks']['items'][0]['popularity'])
            artists_df.append(query['tracks']['items'][0]['artists'][0]['name'])
            titles_df.append(query['tracks']['items'][0]['name'])
            
        else:
            preview_url.append(None)
            track_id.append(None)
            artist_id.append(None)
            track_popularity.append(None)
            artists_df.append(artists_clean[index])
            titles_df.append(titles_clean[index])

        request_count+=1
        if request_count % 5 == 0:
            print(str(request_count) + " records fetched")
            time.sleep(np.random.uniform(sleep_min, sleep_max))
            print('Loop #: {}'.format(request_count))
            print('Elapsed Time: {} seconds'.format(time.time() - start_time))
        
    track_data = pd.DataFrame(artists_df, columns=['artists'])
    track_data['tracks'] = titles_df
    track_data['artist_id'] = artist_id
    track_data['track_id'] = track_id
    track_data['track_popularity'] = track_popularity
    track_data['track_url'] = preview_url

    print('Dataframe with artists,tracks,artist_id,track_id,popularity and track url created...')
    return track_data, preview_url, track_id


def download_songs(preview_url, track_id):
    audio_path = '/Users/ytkd/Desktop/downloaded_songs'
    if os.path.exists('/Users/ytkd/Desktop/downloaded_songs') is False:
        os.mkdir('/Users/ytkd/Desktop/downloaded_songs')

    for i,url in enumerate(preview_url):
        if url is not None:
            response = requests.get(url, verify=False)
            if os.path.exists(f'{audio_path}/{track_id[i][:1]}') is False:
                os.mkdir(f'{audio_path}/{track_id[i][:1]}')
            open(f"{os.path.join(audio_path,track_id[i][:1],track_id[i]+'.mp3')}", 'wb').write(response.content)  
