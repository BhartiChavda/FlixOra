import requests
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
r = requests.get('https://www.imdb.com/title/tt9544034/', headers=headers)
m = re.search(r'"aggregateRating":\{.*?"ratingValue":([0-9.]+)', r.text)
if m:
    print('IMDb Rating:', m.group(1))
else:
    print('Not found')
