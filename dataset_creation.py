''' Importing packages and liraries'''
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

''' Defining all our lists here'''
artists_clean = []
titles_clean = []
spotify_artists = []
check_dat = []
preview_url = [] # track data
track_id = []
artist_id = []
track_popularity = []
artists_df = []
titles_df = []



''' Defining some important variables like the spotify client id and secret and creating an instance of the spotify's api'''
configur = ConfigParser()
configur.read('config.ini')
client_id = configur['main']['client_id']
client_secret = configur['main']['client_secret']
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager) # sp is the instance of the spotipy api
sleep_min = 1
sleep_max = 3


''' Defining all our functions here'''
def pre_process_text(text):
    text = text.lower()
    text = re.sub(r'[^\x00-\x7F]+',' ', text)
    return text


''' In is_same_artist function I check whether the artist the we found in our query is the same one from our dataset.'''
def is_same_artist(query, data, index):
    if pre_process_text(data[index]) in pre_process_text(query['tracks']['items'][0]['artists'][0]['name']):
        return True

''' In track_preview_available function I am checking that the query returned by spotify's api is not empty and if its not I check if the preview url is available.'''
def track_preview_available(query):
    if query['tracks']['items']:
        if query['tracks']['items'][0]['preview_url']:
            return True
        return True
''' To check if the atists data is available at first place'''
def artist_available(query):
    if query['tracks']['items']:
        return True




# Reading and Cleaning Data
''' Reading our data fronm the csv file with the lang_detect_spacy column as 'en' that is english. '''
data = pd.read_csv('/Users/ytkd/Desktop/LY_Artist_lyrics_genre_data_from_big5_mft_users_likes_final.csv')
data = data[data['lang_detect_spacy']=='en']
sample_dataset = data[:200]

artists = list(sample_dataset['Artist'])
titles = list(sample_dataset['title'])

for i in tqdm(range(len(artists))):
    artists_clean.append(pre_process_text(artists[i]))
    titles_clean.append(pre_process_text(titles[i]))

''' Getting correct artist names from spotify'''
request_count = 0
start_time = time.time()
for i in tqdm(range(len(artists))):
    query = sp.search(f'artist:{artists_clean[i]} track:{titles_clean[i]}')
    if query['tracks']['items']:
        spotify_artists.append(query['tracks']['items'][0]['artists'][0]['name'])
        check_dat.append(query['tracks']['items'][0]['artists'][0]['name'])
    else:
        spotify_artists.append(artists[i])
        
    request_count+=1
    if request_count % 5 == 0:
        # print(str(request_count) + " requests sent")
        time.sleep(np.random.uniform(sleep_min, sleep_max))
        # print('Elapsed Time: {} seconds'.format(time.time() - start_time))
print('Extracted correct artist names from spotify...')




request_count = 0
start_time = time.time()
for index in tqdm(range(len(spotify_artists))):
    artist_name = spotify_artists[index]
    song_title = titles_clean[index]
    search = f'artist:{artist_name} track:{song_title}'
    query = sp.search(search, type='track')

    # in the below line of code I am checking that the query returned by spotify's api is not empty and if its not I check if the preview url is available, and
    # even further I check a third condition whether the artist the we found in our query is the same from our dataset.

    # if query['tracks']['items'] and query['tracks']['items'][0]['preview_url'] and query['tracks']['items'][0]['artists'][0]['name'] in alpha_artists_titles[index]:
    if track_preview_available(query) and is_same_artist(query,artists,index):
        preview_url.append(query['tracks']['items'][0]['preview_url'])
        track_id.append(query['tracks']['items'][0]['id'])
        artist_id.append(query['tracks']['items'][0]['artists'][0]['id'])
        track_popularity.append(query['tracks']['items'][0]['popularity'])
        artists_df.append(spotify_artists[index])
        titles_df.append(titles_clean[index])
        
    else:
        preview_url.append(None)
        track_id.append(None)
        artist_id.append(None)
        track_popularity.append(None)
        artists_df.append(spotify_artists[index])
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

# Downloading these song data according track id
track_data.set_index('track_id',inplace=True)
track_data.to_csv('track_data.csv')

print('Dataframe with artists,tracks,artist_id,track_id,popularity and track url created...')

os.mkdir('/Users/ytkd/Desktop/downloaded_songs')
audio_path = '/Users/ytkd/Desktop/downloaded_songs'
for i,url in enumerate(preview_url):
    if url is not None:
        response = requests.get(url, verify=False)
        if os.path.exists(f'{audio_path}/{track_id[i][:1]}') is False:
            os.mkdir(f'{audio_path}/{track_id[i][:1]}')
        open(f"{os.path.join(audio_path,track_id[i][:1],track_id[i]+'.mp3')}", 'wb').write(response.content)  


print('Dataset Downloaded ....')