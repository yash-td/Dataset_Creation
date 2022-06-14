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
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
This method is used to pre-process our text.
Removing all the non-ascii characters and handling apostrophes which might cause
problems when comapring titles and tracks in spotify with our dataset.
'''
# def pre_process_text(text):
#     text = text.lower()
#     text = re.sub(r'[^\x00-\x7F]+',' ', text)
#     return text
def pre_process_text(text):
    text = text.lower()
    text = re.sub(r"[^\x00-\x7F]+",'', text)
    text = text.replace("'",'')
    text = text.replace("(" or ")", '')
    return text


''' Using the pre_process_text function to create new clean lists of artists and titles'''
def clean_data(artists,titles):
    artists_clean = []
    titles_clean = []
    for i in range(len(artists)):
        artists_clean.append(pre_process_text(artists[i]))
        titles_clean.append(pre_process_text(titles[i]))
    return artists_clean, titles_clean


'''
In this function I check whether the artist and title that we found in our query is the same one from our dataset.
'''

def is_same_artist_and_title(query, artist, title, index):
    artist_data = pre_process_text(artist[index])
    artist_spotify = pre_process_text(query['tracks']['items'][0]['artists'][0]['name']) 
    title_data = pre_process_text(title[index])
    title_spotify = pre_process_text(query['tracks']['items'][0]['name'])
    is_same_artist = artist_data in artist_spotify or artist_spotify in artist_data
    is_same_title = title_data in title_spotify or title_spotify in title_data
    return is_same_artist and is_same_title


'''
In track_preview_available function I am checking that the query returned by spotify's api is not empty and if its not
I check if the preview url is available.
'''
def track_preview_available(query):
    if query['tracks']['items']:
        if query['tracks']['items'][0]['preview_url']:
            return True
        return True

'''
This is the main function where we make our artist + track_name query to spotify and extract various fields from spotify
like the track_id, artist_id, track_popularity, preview_url and both artist and track names. One important thing to note 
here is that I have added a random sleep time (1 to 3 seconds) after every 5 requests sent to spotify to avoid the 429 
error response from Spotify’s Web API which indicates an exceed in rate limit. 
'''
def extract_track_data(artists_clean, titles_clean,artists,titles):
    # creating lists to store artist and track data from spotify
    preview_url = []
    track_id = []
    artist_id = []
    track_popularity = []
    artists_df = []
    titles_df = []

    request_count = 0
    start_time = time.time()
    print('Extracting artist and track data from Spotify....')
    for index in tqdm(range(len(artists_clean))):
        artist_name = artists_clean[index]
        song_title = titles_clean[index]
        search = f"artist:{artist_name} track:{song_title}"
        query = sp.search(search, type='track')

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
            artists_df.append(artists[index])
            titles_df.append(titles[index])
            '''
            If data is not found and the above if conditions are not satisfied I have added 'None' values to
            those fields as seen in this block, but maintained the artists and title names so that we still 
            have the original index of all the artists and tracks while we can handle None values later.
            '''

        request_count+=1
        if request_count % 5 == 0: # after every 5 requests adding a random sleep time
            # print(str(request_count) + " records fetched")
            time.sleep(np.random.uniform(sleep_min, sleep_max))
            # print('Loop #: {}'.format(request_count))
            # print('Elapsed Time: {} seconds'.format(time.time() - start_time))
    print('Total Time Elapsed in extracting data: {} seconds'.format(time.time() - start_time))
    track_data = pd.DataFrame(artists_df, columns=['artists'])
    track_data['tracks'] = titles_df
    track_data['artist_id'] = artist_id
    track_data['track_id'] = track_id
    track_data['track_popularity'] = track_popularity
    track_data['track_url'] = preview_url

    print('Dataframe with artists,tracks,artist_id,track_id,popularity and track url created...')
    return track_data, preview_url, track_id # returning preview_url and track_id along with track_data as it will be used to download songs and extract features.


'''
This function is used to download 30s song previews using the track_id and the preview_url that we previosuly extracted. 
The directory tree and the file names are made using track_id as the reference. For example a track id '0fHvKAddOl23DNbklkGhMS'
is stored under a folder named '0f' with the file name '0fHvKAddOl23DNbklkGhMS.mp3'.
'''
def download_songs(preview_url, track_id):
    audio_path = '/Users/ytkd/Desktop/downloaded_songs'
    if os.path.exists('/Users/ytkd/Desktop/downloaded_songs') is False:
        os.mkdir('/Users/ytkd/Desktop/downloaded_songs')
    start_time = time.time()
    for i in tqdm(range(len(preview_url))):
        if preview_url[i] is not None:
            response = requests.get(preview_url[i], verify=False)
            if os.path.exists(f'{audio_path}/{track_id[i][:1]}') is False:
                os.mkdir(f'{audio_path}/{track_id[i][:1]}')
            open(f"{os.path.join(audio_path,track_id[i][:1],track_id[i]+'.mp3')}", 'wb').write(response.content)
            time.sleep(0.01)
            
    print('Total Time Elapsed in downloading songs: {} seconds'.format(time.time() - start_time))
