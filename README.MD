# Crawler API

## Repo Overview

This repo is for crawling data from other sources. We do not develop this all of these crawlers. Instagram-crawler is forked by [this repo](https://github.com/huaying/instagram-crawler) and we made a bit of modification for our use. MarketStoreCrawler is to convert xlsx to json format. The xlsx files are so heavy and have unnecessary informations. Skt-crawler is for converting data given by skt telecom into easy-to-use data format.(like json)

## 사용법
일단 소스코드 다운로드 받고 필요한 라이브러리 다운로드 받기
```bash
git clone https://github.com/hankyul-needs-girfriends/woowa-crawler.git
pip install -r "requirements.txt"
```
인스타그램에서 음식점을 위주로 해시태그를 검색하고 싶을 때 

```python
python crawler.py jieun
```

인스타그램에서 먹스타를 위주로 검색하고 댓글 또한 같이 크롤링 하고 싶을 때

```python
python crawler.py hankyul
```

인스타그램에서 피드 정보를 수집하고 싶을 때

```python
python crawler.py cheol
```

