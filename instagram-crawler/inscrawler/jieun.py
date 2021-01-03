from __future__ import unicode_literals

import glob
import json
import os
import re
import sys
import time
import requests
import traceback
from builtins import open
from time import sleep

from tqdm import tqdm
from bs4 import BeautifulSoup

def save_json(file_name, json_data):
    with open("../data/"+file_name+'.json', "w", encoding = 'utf8') as json_file:
        json.dump(json_data, json_file, indent=4, ensure_ascii=False)

def read_json(file_name):
    json_data = {}
    with open(file_name, encoding = 'utf8') as json_file:
        json_data = json.load(json_file)
    return json_data

def jieun_analyze():
    guList = ['서초구', '종로구']
    foodCategroy = ['닭/오리요리', '별식/퓨전요리', '분식', '양식', '일식/수산물', '제과제빵떡케익', '중식', '패스트푸드', '한식']
    for gu in guList:
        print(gu)
        foodRestaurantDict = {type : 0 for type in foodCategroy}
        for food in foodCategroy:
            foodName = food.replace('/', '_')
            for tag_info in read_json("../../data/ssgi/ssgi_data_search_result" + gu + "_" + foodName + ".json.json").values():
                foodRestaurantDict[food] += int(tag_info['feed_num'].split(' ')[1].replace(',', ''))
        print(foodRestaurantDict)
jieun_analyze()
