# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import os
import traceback

#%%
class AZLyrics_Spider():
    def __init__(self, artist_url):
        self.url = artist_url
        self.header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"}
    
    def get_song_urls(self):
      try:            
        page = requests.get(self.url, headers=self.header)
        soup = BeautifulSoup(page.content, 'html5lib')

        #- Extracting the HREF
        self.song_urls = []
        for song in soup.select('div#listAlbum a'):
          self.song_urls.append('https://www.azlyrics.com'+song['href'][2:])
          print('.')
                
      except:
          print('Error encountered while scraping lyrics. See traceback :\n {}'.format(traceback.print_exc(5)))

    def export_text(self):
      with open('eminem_lyrics.txt', 'w') as file:
        for item in self.lyrics:
          file.write('{}'.format(item))
                
    def scrape_lyrics(self):
      self.lyrics = []
      for song in self.song_urls:
        try:
          song_page = requests.get(song, headers=self.header)
          song_soup = BeautifulSoup(song_page.content, 'html5lib')
        except:
          continue

        self.lyrics.append(song_soup.select('div.row div')[10].get_text())
        
      self.export_text()
      print('File successfully exported!')

#%%
path = r'C:/Users/nholl/Dropbox/2019 FALL/Text Analytics/Code/Scrape'
os.chdir(path)

if __name__ == "main":
    crawl = AZLyrics_Spider('https://www.azlyrics.com/e/eminem.html')
    crawl.get_song_urls()
    crawl.scrape_lyrics()





