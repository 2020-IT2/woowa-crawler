# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import argparse
import json
import sys
import os
import os.path
from tqdm import tqdm
from datetime import datetime
from io import open

from inscrawler import InsCrawler
from inscrawler.settings import override_settings
from inscrawler.settings import prepare_override_settings
from inscrawler.utils import *


def usage():
    return """
        python crawler.py posts -u cal_foodie -n 100 -o ./output
        python crawler.py posts_full -u cal_foodie -n 100 -o ./output
        python crawler.py profile -u cal_foodie -o ./output
        python crawler.py profile_script -u cal_foodie -o ./output
        python crawler.py hashtag -t taiwan -o ./output

        The default number for fetching posts via hashtag is 100.
    """


def get_posts_by_user(username, number, detail, debug):
    ins_crawler = InsCrawler(has_screen=debug)
    return ins_crawler.get_user_posts(username, number, detail)


def get_profile(username):
    ins_crawler = InsCrawler()
    return ins_crawler.get_user_profile(username)


def get_profile_from_script(username):
    ins_cralwer = InsCrawler()
    return ins_cralwer.get_user_profile_from_script_shared_data(username)


def get_posts_by_hashtag(tag, number, debug):
    ins_crawler = InsCrawler(has_screen=debug)
    return ins_crawler.get_latest_posts_by_tag(tag, number)


def arg_required(args, fields=[]):
    for field in fields:
        if not getattr(args, field):
            parser.print_help()
            sys.exit()


def check_for_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def output(data, type):
    filepath = "../data/instagram/" + datetime.today().strftime('%Y-%m-%d') + "/"
    fileName = "instagram_ver_"+datetime.today().strftime('%Y_%m_%d_%H_%M_%S') + "_" + type + ".json"
    check_for_dir(filepath)
    with open(filepath+fileName, "w", encoding="utf8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instagram Crawler", usage=usage())
    parser.add_argument(
        "mode", help="options: [posts, posts_full, profile, profile_script, hashtag, parse_img_tag]"
    )
    parser.add_argument("-n", "--number", type=int, help="number of returned posts")
    parser.add_argument("-u", "--username", help="instagram's username")
    parser.add_argument("-t", "--tag", help="instagram's tag name")
    parser.add_argument("-o", "--output", help="output file name(json format)")
    parser.add_argument("-p", "--part", help="region part")
    parser.add_argument("--debug", action="store_true")

    prepare_override_settings(parser)

    args = parser.parse_args()

    override_settings(args)

    if args.mode in ["posts", "posts_full"]:
        arg_required("username")
        output(
            get_posts_by_user(
                args.username, args.number, args.mode == "posts_full", args.debug
            ),
            args.output,
        )
    elif args.mode == "profile":
        arg_required("username")
        output(get_profile(args.username), args.output)
    elif args.mode == "profile_script":
        arg_required("username")
        output(get_profile_from_script(args.username), args.output)
    elif args.mode == "hashtag":
        arg_required("part")
        city_names = '../data/korea_city_names_and_populations.json'
        if not os.path.exists(city_names):
            save_population_to_json()
        for tag in tqdm(get_city_names(city_names, int(args.part))):
            if tag == '남양주':
                continue
            tag = tag + "맛집"
            print(tag)
            post_detail, user_detail, post_set, user_set = get_posts_by_hashtag(tag, args.number or 100, args.debug)
            output(post_detail, tag+"_post_detail")
            output(user_detail, tag+"_user_detail")
            output(list(post_set), tag+"_post_set")
            output(list(user_set), tag+"_user_set")
    else:
        usage()
