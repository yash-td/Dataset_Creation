
from utils import *


# Reading and Cleaning Data
''' Reading our data fronm the csv file with the lang_detect_spacy column as 'en' that is english. '''
data = pd.read_csv('/Users/ytkd/Desktop/LY_Artist_lyrics_genre_data_from_big5_mft_users_likes_final.csv')
data = data[data['lang_detect_spacy']=='en']
sample_dataset = data[:200]

artists = list(sample_dataset['Artist'])
titles = list(sample_dataset['title'])


artists_clean, titles_clean = clean_data(artists,titles)
    
track_data, preview_url, track_id = extract_track_data(artists_clean,titles_clean,artists,titles)
# Downloading these song data according track id
track_data.set_index('track_id',inplace=True)
track_data.to_excel('track_data.xlsx')

download_songs(preview_url, track_id)
print('Dataset Downloaded ....')

if __name__ == "__main__":
   print("Executed...")