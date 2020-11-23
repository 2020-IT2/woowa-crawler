# Crawler API

## Repo Overview

This repo is for crawling data from other sources. We do not develop this all of these crawlers. Instagram-crawler is forked by [this repo](https://github.com/huaying/instagram-crawler) and we made a bit of modification for our use. MarketStoreCrawler is to convert xlsx to json format. The xlsx files are so heavy and have unnecessary informations. Skt-crawler is for converting data given by skt telecom into easy-to-use data format.(like json)

## 사용법
명령창에 이렇게 치고
```python
python crawler.py hashtag -p 1
```

아래 사진 부분처럼 검색할 태그 검색하면 됨
![status](https://github.com/hankyul-needs-girfriends/Crawler/blob/master/pictures/code.png?raw=true)

크롤링 할 때 너무 빠르게 크롤링하면 안되니깐 아래 사진의 wait time 조절해주는게 좋아
![code](https://github.com/hankyul-needs-girfriends/Crawler/blob/master/pictures/setting.png?raw=true)

그리고 중간에 error 뜨면 그냥 바로 꺼지게 코드 만들어놨는데 이건 그냥 잘 저장되는지 볼려고 한거니깐 지워도 됨.

현재 내 상태는 아래 사진처럼 제제를 먹은 상황이야... 조심해서 크롤링 하도록!
![status](https://github.com/hankyul-needs-girfriends/Crawler/blob/master/pictures/status.png?raw=true)
