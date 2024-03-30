This is the **data preparation** - a.k.a scraping module of my [lyrics_nerds](https://www.notion.so/calibretaliation/5a1644dad498484cbf67cf555a8300fd?v=58bc7c95bfdf4bac881d7172fa9ae38d&pvs=4) project.  
     
Basically, it does the job of getting a singer's information, his/her songs and the song's information like lyrics, etc...   
   
**For MongoDB connection**, please edit the connectino information in configs/config.py    
**Please sign up for AWS API Gateway for scraping efficiently.** Instruction: https://docs.aws.amazon.com/powershell/latest/userguide/pstools-appendix-sign-up.html
# Usage:
```
conda create -n scraping python=3.10 

conda activate scraping

git clone https://github.com/calibretaliation/lyrics_nerds_scraping

cd lyrics_nerds_scraping

pip install -r requirements.txt

SONG_URL=https://www.azlyrics.com/lyrics/taylorswift/carolina.html                                                     

python scraping.py --mode song --print-result --test --song-url $SONG_URL                                                     
```