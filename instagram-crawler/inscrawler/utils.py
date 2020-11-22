# -*- coding: utf-8 -*-
import random
import requests
import openpyxl
import json
from tqdm import tqdm
from functools import wraps
from time import sleep

from .exceptions import RetryException


def instagram_int(string):
    return int(string.replace(",", ""))

def save_json(file_name, json_data):
    with open("../data/"+file_name+'.json', "w", encoding = 'utf8') as json_file:
        json.dump(json_data, json_file, indent=4, ensure_ascii=False)

def read_json(file_name):
    json_data = {}
    with open(file_name, encoding = 'utf8') as json_file:
        json_data = json.load(json_file)
    return json_data

def get_city_names(json_data, part):
    city_names = []
    for city_info in read_json(json_data):
        if city_info['population'] < 200000:
            continue
        if (int(city_info['rank'])-1)//13 != part-1:
            continue
        _names = city_info['cityName'].split("\xa0")[-1]
        city_name = _names.strip("광역자치특별시군")
        # 에외처리 하기
        if len(city_name) == 1:
            city_name = _names[0] + city_name
        # 광주광역시와 경기도 광역시 구분
        if "광역시" not in city_info['cityName'] and city_name == "광주":
            city_name = "경기도" + city_name
        print(city_name)
        city_names.append(city_name)
    return city_names

def save_population_to_json():
    # 엑셀파일 열기
    wb = openpyxl.load_workbook('korea_city_names_and_populations.xlsx')

    # 현재 Active Sheet 얻기
    ws = wb.active

    # 국영수 점수를 읽기
    korea_city = []
    for r in tqdm(ws.rows):
        if r[0].row == 1:
            continue

        korea_city.append({
            "rank" : r[0].value,
            "cityName" : r[1].value,
            "region" : r[2].value,
            "population" : r[4].value,
            "male" : r[5].value,
            "female" : r[6].value,
            "gender_ratio" : r[7].value
        })

    save_json("korea_city_names_and_populations", korea_city)

    return korea_city

def get_html(url):
    headers = {
        "user-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"
    }
    html = requests.get(url, headers = headers).text
    return html

def retry(attempt=10, wait=0.3):
    def wrap(func):
        @wraps(func)
        def wrapped_f(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except RetryException:
                if attempt > 1:
                    sleep(wait)
                    return retry(attempt - 1, wait)(func)(*args, **kwargs)
                else:
                    exc = RetryException()
                    exc.__cause__ = None
                    raise exc

        return wrapped_f

    return wrap


def randmized_sleep(average=1):
    _min, _max = average * 1 / 2, average * 3 / 2
    sleep(random.uniform(_min, _max))


def validate_posts(dict_posts):
    """
        The validator is to verify if the posts are fetched wrong.
        Ex. the content got messed up or duplicated.
    """
    posts = dict_posts.values()
    contents = [post["datetime"] for post in posts]
    # assert len(set(contents)) == len(contents)
    if len(set(contents)) == len(contents):
        print("These post data should be correct.")
