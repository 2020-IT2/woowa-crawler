#-*-coding:utf-8-*-
import codecs
import re
import json
from datetime import datetime

regex = re.compile(r"window._sharedData = (.*?);</script>", re.DOTALL)

def parseFeedInfo(html, dict_post):
    # match_obj = regex.search(html)
    # json_data = match_obj.group(1)
    # dict_data = dict(json.loads(json_data))['entry_data']['PostPage'][0]['graphql']['shortcode_media']
    dict_data = dict(json.loads(html))['graphql']['shortcode_media']
    user_data = getUserData(dict_data['owner'])
    hash_tag = []
    original_caption = ""
    if 'edge_media_to_caption' in dict_data and len(dict_data["edge_media_to_caption"]['edges']) >= 1 :
        hash_tag = getHashTag(dict_data["edge_media_to_caption"]['edges'][0]['node']['text'])
        original_caption = dict_data['edge_media_to_caption']['edges'][0]['node']['text']
    needed_data = {
        "time" : datetime.utcfromtimestamp(int(dict_data['taken_at_timestamp'])).strftime('%Y-%m-%d %H:%M:%S'), # 글을 올린 시간
        "location" : dict_data['location'], # 위치 정보
        "username" : user_data['username'], # 사용자 아이디
        "is_video" : dict_data['is_video'], # 비디오 유무
        "is_ad" : dict_data['is_ad'], # 광고 유무
        "hash_tag" : hash_tag, # 캡션 및 해시태그
        "original_caption" : original_caption,
        "num_like" : dict_data['edge_media_preview_like']['count'], # 좋아요
        "num_reply" : dict_data['edge_media_to_parent_comment']['count'] # 댓글
    }
    # "tagged_target_info" : dict_data['edge_media_to_tagged_user']['edges'], # tag 한 장소, 인물

    dict_post.update(needed_data)
    return user_data

def getHashTag(caption):
    hash_tag = []
    pattern = re.compile(r"#(.*)")
    for cap in caption.split(" "):
        match = pattern.search(cap)
        if match:
            hash_tag.append(match.group(1))
    return hash_tag

def getUserData(dict_owner):
    owner = {
        'id' : dict_owner['id'],
        'username' : dict_owner['username'],
        'full_name' : dict_owner['full_name'],
        'feed_nums' : dict_owner['edge_owner_to_timeline_media']['count'],
        'follower' : dict_owner['edge_followed_by']['count'],
        'feed_urls' : []
    }
    return owner

def parseFeedImageCaption(caption, dict_post):
    # caption = "Photo by 다찬 in Haeundae, Busan. 이미지: 사람 1명, 바다, 하늘, 구름, 실외, 물, 자연. 부산사나이가 되고싶은 촌놈"
    image_captions = None
    loc_captions = None
    type_pattern = re.compile(r"이미지: (.*?)*?\.")
    match = type_pattern.search(caption)
    if match:
        image_captions = match.group(0).split(":")[1].strip(". ").split(",")
        dict_post['image_type'] = image_captions
        # print(image_captions)

    # loc_pattern = re.compile(r"Photo by .*? in (.*?)\.")
    # match = loc_pattern.search(caption)
    # if match:
        # loc_captions = match.split(":")[1].strip(". ").split(",")
        # loc_captions = match.group(1)
        # dict_post['image_loc'] = loc_captions
        # print(loc_captions)

    return image_captions


# parseFeedImageCaption()
