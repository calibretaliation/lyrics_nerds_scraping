import re
from bs4 import BeautifulSoup
import requests
import tqdm
from configs.config import Config
from requests_ip_rotator import ApiGateway, EXTRA_REGIONS, ALL_REGIONS
import time
import random
import logging
from utils.utils import hash_string_to_number
from objects.objects import Singer, Song
from datetime import datetime
import hashlib
import pymongo
from stem.control import Controller
from stem import Signal
import stem.process
from stem.util import term
import traceback
import os, os.path
if not os.path.exists("log/"):
    os.makedirs("log/")
from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.service import Service

logging.basicConfig(filename='log/all.log', 
                    format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p',
                    encoding='utf-8', 
                    level=logging.DEBUG)

log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')
handler = logging.FileHandler('log/scraper.log')
handler.setFormatter(log_format)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False

config = Config()
class Scraper:

  user_agents = open("configs/user-agents.txt", "r").read().splitlines() 

  # def print_bootstrap_lines(line):
  #   if "Bootstrapped " in line:
  #     print(term.format(line, term.Color.BLUE))
  # tor_process = stem.process.launch_tor_with_config(
  #   config = {
  #     'ControlPort':str(config.CONTROL_PORT),
  #     'SocksPort': str(config.SOCKS_PORT),
  #     'ExitNodes': '{ru}',
  #   },
  #   init_msg_handler = print_bootstrap_lines,
  # )

  check_const = config.check_const
  az = "https://www.azlyrics.com"

  def __init__(self, debug: bool = True, tor: bool = True, use_webdriver: bool = True):
    self.gateway = None
    self.failed_request_list = []
    self.failed_singer_list = []
    self.failed_song_list = []
    self.client = pymongo.MongoClient(config.mongodb_host,config.mongodb_port)
    self.mydb = self.client["lyrics_nerds"]
    self.singers_table = self.mydb["singers"]
    self.songs_table = self.mydb["songs"]
    self.debug = debug
    self.tor = tor
    self.use_webdriver = use_webdriver
    
  def test_public_ip(self):
    
    headers = {'User-Agent': random.choice(self.user_agents)}
    try:
      if self.tor: 
        self.start_session()
        with Controller.from_port(port=config.CONTROL_PORT) as c:
          c.authenticate()
          c.signal(Signal.NEWNYM)
        proxies = {'http': config.PROXY, 'https': config.PROXY}
        response = requests.get('https://api.ipify.org', proxies=proxies, headers=headers)
      else:
        self.gateway = ApiGateway("https://api.ipify.org", 
                                regions=EXTRA_REGIONS, 
                                access_key_id=config.get_aws_access_key_id(), 
                                access_key_secret=config.get_aws_access_key_secret())
        self.gateway.start()
        self.session = requests.Session()
        self.session.mount("https://api.ipify.org", self.gateway)
        response = self.session.get('https://api.ipify.org', headers=headers)

      if response.status_code == 200:
          print("IP BEING SEEN: ", response.text)
          logger.info(f"IP BEING SEEN: {response.text}")
          if self.tor: 
            self.tor_process.kill()
          else: 
            self.session.close()

      else:
          print("ERROR CHECKING IP BEING SEEN")
          logger.info(f"ERROR CHECKING IP BEING SEEN")
          if self.tor: 
            self.tor_process.kill()
          else: 
            self.session.close()
            self.gateway.shutdown()
    except Exception as e:
      if self.tor: 
        self.tor_process.kill()
      else: 
        self.session.close()
        self.gateway.shutdown()

      print(traceback.print_exception(e))
  
  def start_session(self):
    logger.info("Starting session...")
    def print_bootstrap_lines(line):
      if "Bootstrapped " in line:
        print(term.format(line, term.Color.BLUE))
    if self.tor:
      self.tor_process = stem.process.launch_tor_with_config(
        config = {
          'ControlPort':str(config.CONTROL_PORT),
          'SocksPort': str(config.SOCKS_PORT),
          'ExitNodes': '{ru}',
        },
        init_msg_handler = print_bootstrap_lines,
      ) 

    else:  
      self.gateway = ApiGateway("https://www.azlyrics.com", 
                                regions=ALL_REGIONS, 
                                access_key_id=config.get_aws_access_key_id(), 
                                access_key_secret=config.get_aws_access_key_secret())
      self.gateway.start()
      self.session = requests.Session()
      self.session.mount("https://www.azlyrics.com", self.gateway)
      return self.session
    logger.info("Session ready!")

  def stop_session(self):
    if self.tor:
      self.tor_process.kill()
    else:
      self.gateway.shutdown()

    logger.info("Stopped session")
  
  def _make_request(self, url):
    sleep_time = random.randint(config.MIN_SLEEP,config.MAX_SLEEP)
    logger.info("Making request to {}. Sleeping: {}".format(url, sleep_time))
    time.sleep(sleep_time)
    headers = {'User-Agent': random.choice(self.user_agents)}
    try:
      with Controller.from_port(port=9051) as c:
        c.authenticate()
        c.signal(Signal.NEWNYM)
      proxies = {'http': config.PROXY, 'https': config.PROXY}
      page = requests.get(url, headers=headers, proxies=proxies)
      if self.debug:
        print(page.headers)
        response = requests.get('https://api.ipify.org', proxies=proxies, headers=headers)
        if response.status_code == 200:
            print("IP BEING SEEN: ", response.text)
            logger.info(f"IP BEING SEEN: {response.text}")
    except Exception as e:
      logger.error("Making request FAILED: {}".format(url))

    return page.content

  def _make_request_web_driver(self, url):
    sleep_time = random.randint(config.MIN_SLEEP,config.MAX_SLEEP)
    logger.info("Making request to USING WEBDRIVER {}. Sleeping: {}".format(url, sleep_time))
    time.sleep(sleep_time)
    try:
      with Controller.from_port(port=9051) as c:
        c.authenticate()
        c.signal(Signal.NEWNYM)
      if self.debug:
        self.driver.get('https://api.ipify.org')
        for request in self.driver.requests:
          print(request.headers) # <----------- Request headers
          print(request.response.headers) # <
          print(request.response.body) # <--------------- Request url
          
          # if response.status_code == 200:
          #     print("IP BEING SEEN: ", response.text)
          #     logger.info(f"IP BEING SEEN: {response.text}")
      self.driver.get(url)
      page = self.driver.page_source
      self.driver.quit()
    except Exception as e:
      logger.error("Making request FAILED: {}".format(url))
      self.driver.quit()

    return page
  
  def start_webdriver(self):
    
    profile = FirefoxProfile("/home/hudigeck/Downloads/tor-browser-linux-x86_64-13.0.13/tor-browser/Browser/TorBrowser/Data/Browser/profile.default")
    profile.set_preference('network.proxy.type', 1)
    profile.set_preference('network.proxy.socks', '127.0.0.1')
    profile.set_preference('network.proxy.socks_port', 7000)
    profile.set_preference("network.proxy.socks_remote_dns", False)
    profile.set_preference("general.useragent.override", random.choice(self.user_agents))
    profile.update_preferences()
    # webdriver_options.add_argument(f"--user-agent={random.choice(self.user_agents)}")
    # webdriver_options.add_argument("--headless")
    webdriver_options = Options()
    webdriver_options.profile = profile
    # driver_service = Service(executable_path="/home/hudigeck/Downloads/tor-browser-linux-x86_64-13.0.13/tor-browser/Browser/firefox")
    webdriver_options.binary="/home/hudigeck/Downloads/tor-browser-linux-x86_64-13.0.13/tor-browser/Browser/firefox"
  
    # webdriver_options.add_argument(f"--proxy-server={config.PROXY}")
    # proxy = Proxy()
    # proxy.proxy_type = ProxyType.MANUAL
    # proxy.http_proxy = config.PROXY
    # proxy.ssl_proxy = config.PROXY
    # proxy.socks_proxy= config.PROXY
    # webdriver_options.proxy = proxy
    self.driver = webdriver.Firefox(
      # service=driver_service,
      options=webdriver_options,
      )
    return self.driver
  
  def test_tor_webdriver(self):
    assert self.driver is not None, "WEBDRIVER HAVENT INITIALIZED YET, please run scraper.start_webdriver()"
    self.driver.get("https://api.ipify.org")
    time.sleep(10)
    self.driver.quit()
  
  def _make_request_with_rerun(self, url, num_retry):
    current = 0
    while current < num_retry:
      page = self._make_request(url)
      if self.check_const in page.decode("utf-8"):
        return current, page
      else:
          logger.warn("Retry time {} of request: {}".format(current,url))
          current += 1
    else:
      logger.warn("Reached maximum number of retry, failing request: {}".format(url))
      self.failed_request_list.append(url)
      return current, None
  
  def _make_request_webdriver_with_rerun(self, url, num_retry):
    current = 0
    while current < num_retry:
      page = self._make_request_web_driver(url)
      if self.check_const in page:
        return current, page
      else:
          logger.warn("Retry time {} of request: {}".format(current,url))
          current += 1
    else:
      logger.warn("Reached maximum number of retry, failing request: {}".format(url))
      self.failed_request_list.append(url)
      return current, None
  
  def _insert_singer_to_db(self, singer: Singer, overwrite= True):
    singer_document = singer.__dict__
    if not overwrite:
      if self.singers_table.count_documents({'song_id': singer_document["singer_id"]}):
        print("**Error: You're already in the database**")
        logger.error("Song document already exists, not overwriting")
    else:
      if not self.debug:
        self.singers_table.insert_one(singer_document)
    return None
  
  def _insert_song_to_db(self, song: Song, overwrite: bool = True):
    song_document = song.__dict__
    if not overwrite:
      if self.songs_table.count_documents({'song_id': song_document["song_id"]}):
        print("**Error: You're already in the database**")
        logger.error("Song document already exists, not overwriting")
    else:
      if not self.debug:
        self.songs_table.replace_one({'song_id': song_document["song_id"]}, song_document, upsert = True)
    return None

  def get_songs_by_singer(self, singer: Singer):
    song_list = singer.songs()
    logger.info("Getting songs of {}.".format(singer.name))
    for song_id in song_list.keys():
      self.get_song(song_id, song_list["song"], singer.singer_id)
    return None 
  
  def get_singer(self, singer_url) -> Singer:
    # assert self.session is not None, "Please start the Scraper's session first by calling scraper.start_session()"
    logger.info("Getting singer information: {}".format(singer_url))
    start_singer = time.time()
    if self.use_webdriver:
      num_retry, singer_page = self._make_request_webdriver_with_rerun(singer_url, 5)
    else:
      num_retry, singer_page = self._make_request_with_rerun(singer_url, 5)
    soup = BeautifulSoup(singer_page, "lxml")
    try:
      name = soup.find("h1").get_text().replace(" Lyrics", "")
      id = hash_string_to_number(name)
      singer = Singer(singer_id = id,
                      url=singer_url,
                      is_scraped_sucessful=1,
                      name=name,
                      num_retry=num_retry,
                      date_created=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                      date_updated=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
      logger.info("Singer information successful: {}".format(name))
      
      # Find albums
      for page in soup.findAll("div", {"class":"album"}):
        singer.albums.append(page.find("b").text.strip("\""))
      logger.info("Found albums of {}, number: ".format(name, len(singer.albums)))

      # Find songs
      for div in tqdm.tqdm(soup.find_all("div", {"class": "listalbum-item"})):
        song_url = div.find("a").get("href")
        song_id = hash_string_to_number(str(song_url).split("/")[-1])
        if "https" not in song_url:
          song_url = self.az + song_url
        singer.songs.update({song_id:song_url})  
      logger.info("Found songs of {}, number: ".format(name, len(singer.songs)))
      singer.num_albums = len(singer.albums)
      singer.num_songs = len(singer.songs)
      self._insert_singer_to_db(singer)
      logger.info("{} inserted to db.".format(name))
      logger.info("DONE scraping singer {} in: {} seconds.".format(name, time.time() - start_singer))

    except Exception as e:
      logger.error(f"{e.with_traceback()}")
      self.failed_singer_list.append(singer_url)
      singer = Singer(url=singer_url,
                      is_scraped_sucessful=0,
                      num_retry=num_retry,
                      )
      logger.info("Singer information failed: {}".format(name))
    return singer
  
  def get_song(self, song_id, song_url, singer_id) -> Song:
    # assert self.session is not None, "Please start the Scraper's session first by calling scraper.start_session()"
    start_song = time.time()
    if self.use_webdriver:
      num_retry, song_page = self._make_request_webdriver_with_rerun(song_url, 5)
    else:
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
            logger.info("Found song: {}".format(name))

        fields = re.findall(genre_pattern, script.text)
        if len(fields) != 0:
            genre = fields[0]
            logger.info("Found genre of {}: {}".format(name, genre))

      id = song_id
      singer_id = singer_id
      
      # Find writers
      for small in soup.body.findAll("small"):
        writers = re.findall(writers_pattern, small.text)
        if len(writers) != 0:
          writers = writers[0]
          logger.info("Found writers of {}: {}".format(name, writers))
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
                  song_id = id,
                  singer = singer_id,
                  url = song_url,
                  name = name,
                  genre = genre,
                  writer= writers,
                  album = album,
                  year_written = year,
                  num_retry = num_retry,
                  date_created=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                  date_updated=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
      
      # Find lyrics (raw)
      main = soup.body.find("div", {"class":"col-xs-12 col-lg-8 text-center"})
      song.lyrics = "".join(div.text for div in main.findAll("div", {"class":None})).strip()
      logger.info("Found LYRICS of {}, len: {}".format(name, len(song.lyrics)))
      self._insert_song_to_db(song)

      logger.info("DONE scraping song {} in: {} seconds.".format(name, time.time() - start_song))
    else: 
      song = Song(is_scraped_successful=0,
                  num_retry=num_retry)
    return song

  def get_singer_url_by_letter(self, letter):
    return None
  
  def get_all_alphabet_url(self):
    return None
  
  def get_song_from_html(self, song_page, song_url = None, singer_id = None) -> Song:
    # assert self.session is not None, "Please start the Scraper's session first by calling scraper.start_session()"
    start_song = time.time()
    
    song_name_pattern = re.compile(r"SongName\s*=\s*\"([^\"]*)\"")
    genre_pattern = re.compile(r"\[\"genre\"\, \"(\w+)\"\]")
    year_pattern = re.compile(r"\d+")
    writers_pattern = re.compile(r"Writer\(s\): \s*(.*)")
    
    soup = BeautifulSoup(song_page, "lxml")
    name = None
    genre = None
    writers = None
    album = "other songs:"
    year = None
    if song_url is None:
      song_url = soup.find("link", {"rel":"canonical"})["href"]
    # Find song name and genre
    for script in soup.head.findAll("script", {"type": "text/javascript"}):

      fields = re.findall(song_name_pattern, script.text)
      if len(fields) != 0:
          name = fields[0]
          logger.info("Found song: {}".format(name))

      fields = re.findall(genre_pattern, script.text)
      if len(fields) != 0:
          genre = fields[0]
          logger.info("Found genre of {}: {}".format(name, genre))

    id = hash_string_to_number(name)
    singer_id = singer_id
    
    # Find writers
    for small in soup.body.findAll("small"):
      writers = re.findall(writers_pattern, small.text)
      if len(writers) != 0:
        writers = writers[0]
        logger.info("Found writers of {}: {}".format(name, writers))
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
                song_id = id,
                singer = singer_id,
                url = song_url,
                name = name,
                genre = genre,
                writer=writers,
                album=album,
                year_written = year,
                num_retry=0,
                date_created=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                date_updated=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    
    # Find lyrics (raw)
    main = soup.body.find("div", {"class":"col-xs-12 col-lg-8 text-center"})
    song.lyrics = "".join(div.text for div in main.findAll("div", {"class":None})).strip()
    logger.info("Found LYRICS of {}, len: {}".format(name, len(song.lyrics)))
    self._insert_song_to_db(song)

    logger.info("DONE scraping song {} in: {} seconds.".format(name, time.time() - start_song))

    return song