from scraper.scraper import Scraper
from objects.objects import *
import argparse
import sys 
import random
import traceback
parser = argparse.ArgumentParser(
    description="Welcome to the lyrics scraper")
parser.add_argument("--mode", default = "song", choices=["song","singer"],
                    help = "Choose \"song\" mode to scrape only one song's information, choose \"singer\" mode to scrape all song belong to that singer")
parser.add_argument("--print-result", action='store_true', 
                    help = "whether to print the scraped information to console or not")
parser.add_argument("--song-url", default = None, 
                    help = "Song URL to get lyrics and information, only available with mode = \"song\"")
parser.add_argument("--singer-url", default = None, 
                    help = "Singer URL to get their songs' lyrics and information, only available with mode = \"singer\"")
parser.add_argument("--test", action='store_true',
                    help = "Debug mode, not write to DB, should be used with --print-result option")
parser.add_argument("--tor", action='store_true',
                    help = "Whether to USE Tor or not, default = True = Use Tor")
parser.add_argument("--use_webdriver", action='store_true',
                    help = "Whether to USE WEBDRIVER or not, default = True = Use Tor")
# parser.add_argument("--test", type=bool, default=False,
#                     help = "Debug mode, not write to DB, should be used with --print-result option")


if __name__ == '__main__':
    args = parser.parse_args()
    scraper = Scraper(debug=args.test, tor=args.tor, use_webdriver=args.use_webdriver)
    # scraper.test_public_ip()
    try:
        # scraper.start_session()
        if args.use_webdriver:
            scraper.start_webdriver()
            scraper.test_tor_webdriver()
        # if args.mode=="song":
        #     song_url = args.song_url
        #     song = scraper.get_song(song_url=song_url, 
        #                             singer_id=random.randint(10000000,99999999), 
        #                             song_id=random.randint(10000000,99999999))
        #     if args.print_result:
        #         print("Sucessfully scraped song: {}\nMetadata: {}".format(song.metadata["name"],song.metadata))
        #         print("Lyrics: ", song.lyrics)
        # elif args.mode=="singer":
        #     singer_url = args.singer_url
        #     singer = scraper.get_singer(singer_url)
        #     singer_songs = scraper.get_songs_by_singer(singer)
        #     if args.print_result:
        #         print("Sucessfully scraped singer: {}\nMetadata: {}".format(singer.metadata["name"],singer.metadata))
        scraper.stop_session()
    except Exception as e:
        scraper.stop_session()
        traceback.print_exception(e)
     
    