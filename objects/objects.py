class Singer:
    def __init__(self,
                id: int = None,
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
        self.metadata = {
            "id": id,
            "is_scraped_sucessful":is_scraped_sucessful,
            "name": name,
            "year_born":year_born,
            "num_songs":num_songs,
            "num_albums":num_albums,
            "region":region,
            "gender":gender,
            "url":url,
            "num_retry": num_retry,
            "date_created":date_created,
            "date_updated":date_updated,
                    }
    songs = {}
    albums = []
    
    
class Song:
    def __init__(self, 
                    id: int = None, 
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
        self.metadata = {
            "id": id,
            "is_scraped_successful":is_scraped_successful,
            "name": name,
            "singer":singer,
            "year_written": year_written,
            "album": album,
            "writer": writer,
            "url": url,
            "num_retry": num_retry,
            "genre": genre,
            "date_created":date_created,
            "date_updated":date_updated,
            }
    lyrics = None
    other_info = None
    