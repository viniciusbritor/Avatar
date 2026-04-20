import urllib.request
import re

url = 'https://www.youtube.com/watch?v=a0sO5yp6mh4'
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read().decode('utf-8')
    match = re.search(r'"ownerChannelName":"([^"]+)"', html)
    if match:
        print('Canal:', match.group(1).encode('utf-8').decode('unicode_escape'))
    else:
        print('Nao encontrou o canal.')
except Exception as e:
    print('Erro:', str(e))
