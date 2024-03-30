import re
from bs4 import BeautifulSoup
import requests
import tqdm
from configs.config import Config
from requests_ip_rotator import ApiGateway, EXTRA_REGIONS, ALL_REGIONS
import time
import random
import logging
from objects.objects import Singer, Song
from datetime import datetime
import hashlib
import pymongo
import os, os.path
if not os.path.exists("log/"):
    os.makedirs("log/")
logger = logging.getLogger(__name__)
logging.basicConfig(filename='log/all.log', 
                    format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p',
                    encoding='utf-8', 
                    level=logging.DEBUG)
logger.addHandler(logging.FileHandler('log/scraper.log'))
logger.propagate = False

config = Config()
class Scraper:

  user_agents = open("configs/user-agents.txt", "r").read().splitlines() #TODO: repllace haardcode


  check_const = config.check_const
  az = "https://www.azlyrics.com"

  def __init__(self, debug: bool = True):
    self.gateway = None
    self.failed_request_list = []
    self.failed_singer_list = []
    self.failed_song_list = []
    self.client = pymongo.MongoClient(config.mongodb_host,config.mongodb_port)
    self.mydb = self.client["lyrics_nerds"]
    self.singers_table = self.mydb["singers"]
    self.songs_table = self.mydb["songs"]
    self.debug = debug
  def test_public_ip(self):
    self.gateway = ApiGateway("https://api.ipify.org", 
                              regions=EXTRA_REGIONS, 
                              access_key_id=config.get_aws_access_key_id(), 
                              access_key_secret=config.get_aws_access_key_secret())
    self.gateway.start()
    try:
      self.session = requests.Session()
      self.session.mount("https://api.ipify.org", self.gateway)
      response = self.session.get('https://api.ipify.org')
      if response.status_code == 200:
          print("IP BEING SEEN: ", response.text)
          logger.info(f"IP BEING SEEN: {response.text}")
          self.session.close()
      else:
          print("ERROR CHECKING IP BEING SEEN")
          logger.info(f"ERROR CHECKING IP BEING SEEN")
          self.session.close()
      self.gateway.shutdown()
    except Exception as e:
      self.session.close()
      self.gateway.shutdown()
      print(e)

  def start_session(self):
    logger.info("[SCRAPER] Starting session...")
    self.gateway = ApiGateway("https://www.azlyrics.com", 
                              regions=EXTRA_REGIONS, 
                              access_key_id=config.get_aws_access_key_id(), 
                              access_key_secret=config.get_aws_access_key_secret())
    self.gateway.start()
    self.session = requests.Session()
    self.session.mount("https://www.azlyrics.com", self.gateway)
    logger.info("[SCRAPER] Session ready!")

    return self.session

  def stop_session(self):
    self.gateway.shutdown()
    logger.info("[SCRAPER] Stopped session")

  def hash_string_to_number(string):
    # Create an SHA-256 hash object
    sha256_hash = hashlib.sha256()

    # Convert the string to bytes and update the hash object
    sha256_hash.update(string.encode('utf-8'))

    # Get the hexadecimal representation of the hash value
    hash_value = sha256_hash.hexdigest()

    # Convert the hexadecimal hash value to an integer
    hash_int = int(hash_value, 16)

    # Map the integer to an 8-digit number within the desired range
    mapped_number = hash_int % 100000000

    return mapped_number
  
  def _make_request(self, url):
    headers = {'User-Agent': random.choice(self.user_agents)}
    #TODO:  proxies = {'http': SCRAPE_PROXY, 'https': SCRAPE_PROXY}
    time.sleep(random.randint(config.MIN_SLEEP,config.MAX_SLEEP))
    logger.info("[SCRAPER] Making request to {}.".format(url))
    page = self.session.get(url, headers=headers)
    if self.debug:
      print(page.headers)
    return page.content

  def _make_request_with_rerun(self, url, num_retry):
    current = 1
    while current < num_retry:
      page = self._make_request(url)
      if self.check_const in page.decode("utf-8"):
        return current, page
      else:
          logger.warn("[SCRAPER] Retry time {} of request: {}".format(current,url))
          current += 1
      if current == num_retry:
        logger.warn("[SCRAPER] Reached maximum number of retry, failing request: {}".format(url))
        self.failed_request_list.append(url)
        return current, None
  
  def _insert_singer_to_db(self, singer: Singer):
    singer_document = {"metadata": singer.metadata,
                       "songs": singer.songs,
                       "albums": singer.albums}
    if not self.debug:
      self.singers_table.insert_one(singer_document)
    return None
  
  def _insert_song_to_db(self, song: Song):
    song_document = {"metadata": song.metadata,
                     "lyrics": song.lyrics,
                     "other_info": song.other_info}
    if not self.debug:
      self.songs_table.insert_one(song_document)
    return None

  def get_songs_by_singer(self, singer: Singer):
    song_list = singer.songs()
    logger.info("[SCRAPER] Getting songs of {}.".format(singer.metadata["name"]))
    for song_id in song_list.keys():
      self.get_song(song_id, song_list["song"], singer.metadata["id"])
    return None 
  
  def get_singer(self, singer_url) -> Singer:
    assert self.session is not None, "Please start the Scraper's session first by calling scraper.start_session()"
    logger.info("[SCRAPER] Getting singer information: {}".format(singer_url))
    start_singer = time.time()
    num_retry, singer_page = self._make_request_with_rerun(singer_url, 5)
    soup = BeautifulSoup(singer_page, "lxml")
    try:
      name = soup.find("h1").get_text().replace(" Lyrics", "")
      id = self.hash_string_to_number(name)
      singer = Singer(id = id,
                      url=singer_url,
                      is_scraped_sucessful=1,
                      name=name,
                      num_retry=num_retry,
                      date_created=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                      date_updated=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
      logger.info("[SCRAPER] Singer information successful: {}".format(name))
      
      # Find albums
      for page in soup.findAll("div", {"class":"album"}):
        singer.albums.append(page.find("b").text.strip("\""))
      logger.info("[SCRAPER] Found albums of {}, number: ".format(name, len(singer.albums)))

      # Find songs
      for div in tqdm.tqdm(soup.find_all("div", {"class": "listalbum-item"})):
        song_url = div.find("a").get("href")
        song_id = self.hash_string_to_number(str(song_url).split("/")[-1])
        if "https" not in song_url:
          song_url = self.az + song_url
        singer.songs.update({song_id:song_url})  
      logger.info("[SCRAPER] Found songs of {}, number: ".format(name, len(singer.songs)))
      singer.metadata.update({"num_albums":len(singer.albums),
                              "num_songs":len(singer.songs)})
      self._insert_singer_to_db(singer)
      logger.info("[SCRAPER] {} inserted to db.".format(name))
      logger.info("[SCRAPER] DONE scraping singer {} in: {} seconds.".format(name, time.time() - start_singer))

    except Exception as e:
      logger.error(f"[SCRAPER] {e.with_traceback()}")
      self.failed_singer_list.append(singer_url)
      singer = Singer(url=singer_url,
                      is_scraped_sucessful=0,
                      num_retry=num_retry,
                      )
      logger.info("[SCRAPER] Singer information failed: {}".format(name))
    return singer
  
  def get_song(self, song_id, song_url, singer_id) -> Song:
    assert self.session is not None, "Please start the Scraper's session first by calling scraper.start_session()"
    start_song = time.time()
    num_retry, song_page = self._make_request_with_rerun(song_url,5)
    song_name_pattern = re.compile(r"SongName\s*=\s*\"([^\"]*)\"")
    genre_pattern = re.compile(r"\[\"genre\"\, \"(\w+)\"\]")
    year_pattern = re.compile(r"\d+")
    writers_pattern = re.compile(r"Writer\(s\): \s*(.*)")
    
    if song_page is not None:
      soup = BeautifulSoup(song_page, "lxml")
      name = None
      genre = None
      writers = None
      album = "other songs:"
      year = None
      
      # Find song name and genre
      for script in soup.head.findAll("script", {"type": "text/javascript"}):

        fields = re.findall(song_name_pattern, script.text)
        if len(fields) != 0:
            name = fields[0]
            logger.info("[SCRAPER] Found song: {}".format(name))

        fields = re.findall(genre_pattern, script.text)
        if len(fields) != 0:
            genre = fields[0]
            logger.info("[SCRAPER] Found genre of {}: {}".format(name, genre))

      id = song_id
      singer_id = singer_id
      
      # Find writers
      for small in soup.body.findAll("small"):
        writers = re.findall(writers_pattern, small.text)
        if len(writers) != 0:
          writers = writers[0]
          logger.info("[SCRAPER] Found writers of {}: {}".format(name, writers))
          break
        
      # Find album and year
      for div in soup.body.findAll("div" ,{"class":"songinalbum_title"}):
        if "album" in div.text:
          album = div.find("b").text.strip("\"")
          try:
            year = re.findall(year_pattern, div.text)[0]

          except Exception as e:
            print(e)
          break     
                
      song = Song(is_scraped_successful=1,
                  id = id,
                  singer = singer_id,
                  url = song_url,
                  name = name,
                  genre = genre,
                  writer=writers,
                  album=album,
                  year_written = year,
                  num_retry=num_retry,
                  date_created=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                  date_updated=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
      
      # Find lyrics (raw)
      main = soup.body.find("div", {"class":"col-xs-12 col-lg-8 text-center"})
      song.lyrics = "".join(div.text for div in main.findAll("div", {"class":None})).strip()
      logger.info("[SCRAPER] Found LYRICS of {}, len: {}".format(name, len(song.lyrics)))
      self._insert_song_to_db(song)

      logger.info("[SCRAPER] DONE scraping song {} in: {} seconds.".format(name, time.time() - start_song))
    else: 
      song = Song(is_scraped_successful=0,
                  num_retry=num_retry)
    return song

  def get_singer_url_by_letter(self, letter):
    return None
  
  def get_all_alphabet_url(self):
    return None