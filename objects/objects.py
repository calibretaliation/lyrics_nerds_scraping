class Object:
    def __init__(self):
        pass
    
class Singer(Object):
    def __init__(self,
                singer_id: int = None,
                is_scraped_sucessful: int = None,
                name = None,
                year_born = None,
                num_songs = None,
                num_albums = None,
                region = None,
                gender = None,
                url = None,
                num_retry= None,
                date_created = None,
                date_updated = None,
                 ) -> None:    
            self.singer_id = singer_id
            self.is_scraped_sucessful = is_scraped_sucessful
            self.name =  name
            self.year_born = year_born
            self.num_songs = num_songs
            self.num_albums = num_albums
            self.region = region
            self.gender = gender
            self.url = url
            self.num_retry =  num_retry
            self.date_created = date_created
            self.date_updated = date_updated
    songs = {}
    albums = []
    
    
class Song(Object):
    def __init__(self, 
                    song_id: int = None, 
                    is_scraped_successful: int = None, 
                    name: str = None,
                    singer: int = None,
                    year_written = None,
                    album = None,
                    writer = None,
                    url = None,
                    num_retry= None,
                    genre: str = None,
                    date_created = None,
                    date_updated = None,
                    ) -> None:
            self.song_id= song_id
            self.is_scraped_successful =is_scraped_successful
            self.name = name
            self.singer =singer
            self.year_written = year_written
            self.album = album
            self.writer = writer
            self.url = url
            self.num_retry = num_retry
            self.genre = genre
            self.date_created =date_created
            self.date_updated =date_updated
    lyrics = None
    other_info = None
    
    