# Crawler API Read Me

<p align="center">
    <img src="pic/main.png" height="500"/>
</p>
<h4 align="center">사용자 기반 음식 추천 & 요식업계 시장 분석 어플리케이션</h4>

<p align="center">
    이 어플리케이션은 2020년 아주대학교 집중 교육의 일환으로 제작되었습니다. 이 어플리케이션은 실제 상업적 목적이 포함되어 있지 않습니다. 전체적인 디자인 모티브로 배달의 민족 어플리케이션을 참고하였습니다. 이 프로젝트는 <a href="https://github.com/hankyul-needs-girfriends/woowa-appserver">서버</a>, <a href="https://github.com/hankyul-needs-girfriends/woowa-crawler">크롤링</a>, <a href="https://github.com/hankyul-needs-girfriends/woowa-ML">머신러닝</a> 레포와 같이 운영되어 왔습니다. 하지만 프로젝트의 주요 레포지토리는 <a href="https://github.com/hankyul-needs-girfriends/woowa-android-main-">안드로이드 레포지토리</a> 입니다. 이 프로젝트는 강*결, 윤*은, 허*철의 도움으로 만들어졌습니다. 같이 고생한 팀원분들께 감사의 말을 전합니다.
</p>




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

