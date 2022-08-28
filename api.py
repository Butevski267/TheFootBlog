import requests
import os
from dotenv import load_dotenv
from pprint import pprint
load_dotenv()

url = 'https://newsdata.io/api/1/news'
API_KEY= os.getenv('API_KEY')

headers = {
    'X-ACCESS-KEY': API_KEY,
}

parameters = {
    'language': 'en',
    'q': 'Premier League'
}

posts = requests.get(url=url, headers=headers, params=parameters).json()['results'][0:10]



