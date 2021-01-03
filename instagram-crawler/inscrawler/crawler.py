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
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

from . import secret
from .browser import Browser
from .exceptions import RetryException
from .fetch import fetch_caption
from .fetch import fetch_comments
from .fetch import fetch_datetime
from .fetch import fetch_imgs
from .fetch import fetch_likers
from .fetch import fetch_likes_plays
from .fetch import fetch_details
from .utils import instagram_int
from .utils import randmized_sleep
from .utils import retry
from .utils import get_html
from .utils import read_json
from .utils import save_json
from .parsingFeed import parseFeedInfo
from .parsingFeed import parseFeedImageCaption


class Logging(object):
    PREFIX = "instagram-crawler"

    def __init__(self):
        try:
            timestamp = int(time.time())
            self.cleanup(timestamp)
            self.logger = open("/tmp/%s-%s.log" % (Logging.PREFIX, timestamp), "w")
            self.log_disable = False
        except Exception:
            self.log_disable = True

    def cleanup(self, timestamp):
        days = 86400 * 7
        days_ago_log = "/tmp/%s-%s.log" % (Logging.PREFIX, timestamp - days)
        for log in glob.glob("/tmp/instagram-crawler-*.log"):
            if log < days_ago_log:
                os.remove(log)

    def log(self, msg):
        if self.log_disable:
            return

        self.logger.write(msg + "\n")
        self.logger.flush()

    def __del__(self):
        if self.log_disable:
            return
        self.logger.close()


class InsCrawler(Logging):
    URL = "https://www.instagram.com"
    RETRY_LIMIT = 10

    def __init__(self, has_screen=False):
        super(InsCrawler, self).__init__()
        self.browser = Browser(has_screen)
        self.page_height = 0
        self.login()

    def _dismiss_login_prompt(self):
        ele_login = self.browser.find_one(".Ls00D .Szr5J")
        if ele_login:
            ele_login.click()

    def login(self):
        browser = self.browser
        url = "%s/accounts/login/" % (InsCrawler.URL)
        browser.get(url)
        u_input = browser.find_one('input[name="username"]')
        u_input.send_keys(secret.username)
        p_input = browser.find_one('input[name="password"]')
        p_input.send_keys(secret.password)

        login_btn = browser.find_one(".L3NKy")
        login_btn.click()

        @retry()
        def check_login():
            if browser.find_one('input[name="username"]'):
                raise RetryException()

        check_login()

    def get_user_profile(self, username):
        browser = self.browser
        url = "%s/%s/" % (InsCrawler.URL, username)
        browser.get(url)
        name = browser.find_one(".rhpdm")
        desc = browser.find_one(".-vDIg span")
        photo = browser.find_one("._6q-tv")
        post_num, follower_num, following_num = browser.find(".g47SY")
        return {
            "id" : username,
            "name": name.text,
            "desc": desc.text if desc else None,
            "photo_url": photo.get_attribute("src"),
            "post_num": int(post_num.text.replace(',', '')),
            "follower_num": int(follower_num.get_attribute('title').replace(',', '')),
            "following_num": int(following_num.text.replace(',', '')),
        }

    def get_user_profile_from_script_shared_data(self, username):
        browser = self.browser
        url = "%s/%s/" % (InsCrawler.URL, username)
        browser.get(url)
        source = browser.driver.page_source
        p = re.compile(r"window._sharedData = (?P<json>.*?);</script>", re.DOTALL)
        json_data = re.search(p, source).group("json")
        data = json.loads(json_data)

        user_data = data["entry_data"]["ProfilePage"][0]["graphql"]["user"]

        return {
            "name": user_data["full_name"],
            "desc": user_data["biography"],
            "photo_url": user_data["profile_pic_url_hd"],
            "post_num": int(user_data["edge_owner_to_timeline_media"]["count"]),
            "follower_num": int(user_data["edge_followed_by"]["count"]),
            "following_num": user_data["edge_follow"]["count"],
            "website": user_data["external_url"],
        }

    def get_user_posts(self, username, number=None, detail=False):
        user_profile = self.get_user_profile(username)
        if not number:
            number = instagram_int(user_profile["post_num"])

        self._dismiss_login_prompt()

        if detail:
            return self._get_posts_full(number)
        else:
            return self._get_posts(number)

    def get_latest_posts_by_tag(self, tag, num):
        self.tag = tag
        url = "%s/explore/tags/%s/" % (InsCrawler.URL, tag)
        self.browser.get(url)
        return self._get_posts(num)

    def auto_like(self, tag="", maximum=1000):
        self.login()
        browser = self.browser
        if tag:
            url = "%s/explore/tags/%s/" % (InsCrawler.URL, tag)
        else:
            url = "%s/explore/" % (InsCrawler.URL)
        self.browser.get(url)

        ele_post = browser.find_one(".v1Nh3 a")
        ele_post.click()

        for _ in range(maximum):
            heart = browser.find_one(".dCJp8 .glyphsSpriteHeart__outline__24__grey_9")
            if heart:
                heart.click()
                randmized_sleep(2)

            left_arrow = browser.find_one(".HBoOv")
            if left_arrow:
                left_arrow.click()
                randmized_sleep(2)
            else:
                break

    def _get_posts_full(self, num):
        @retry()
        def check_next_post(cur_key):
            ele_a_datetime = browser.find_one(".eo2As .c-Yi7")

            # It takes time to load the post for some users with slow network
            if ele_a_datetime is None:
                raise RetryException()

            next_key = ele_a_datetime.get_attribute("href")
            if cur_key == next_key:
                raise RetryException()

        browser = self.browser
        browser.implicitly_wait(1)
        browser.scroll_down()
        ele_post = browser.find_one(".v1Nh3 a")
        ele_post.click()
        dict_posts = {}

        pbar = tqdm(total=num)
        pbar.set_description("fetching")
        cur_key = None

        all_posts = self._get_posts(num)
        i = 1

        # Fetching all posts
        for _ in range(num):
            dict_post = {}

            # Fetching post detail
            try:
                if(i < num):
                    check_next_post(all_posts[i]['key'])
                    i = i + 1

                # Fetching datetime and url as key
                ele_a_datetime = browser.find_one(".eo2As .c-Yi7")
                cur_key = ele_a_datetime.get_attribute("href")
                dict_post["key"] = cur_key
                fetch_datetime(browser, dict_post)
                fetch_imgs(browser, dict_post)
                fetch_likes_plays(browser, dict_post)
                fetch_likers(browser, dict_post)
                fetch_caption(browser, dict_post)
                fetch_comments(browser, dict_post)

            except RetryException:
                sys.stderr.write(
                    "\x1b[1;31m"
                    + "Failed to fetch the post: "
                    + cur_key or 'URL not fetched'
                    + "\x1b[0m"
                    + "\n"
                )
                break

            except Exception:
                sys.stderr.write(
                    "\x1b[1;31m"
                    + "Failed to fetch the post: "
                    + cur_key if isinstance(cur_key,str) else 'URL not fetched'
                    + "\x1b[0m"
                    + "\n"
                )
                traceback.print_exc()

            self.log(json.dumps(dict_post, ensure_ascii=False))
            dict_posts[browser.current_url] = dict_post

            pbar.update(1)

        pbar.close()
        posts = list(dict_posts.values())
        if posts:
            posts.sort(key=lambda post: post["datetime"], reverse=True)
        return posts

    def _get_posts(self, num):
        """
            To get posts, we have to click on the load more
            button and make the browser call post api.
        """
        session_obj = requests.Session()
        for cookie in self.browser.driver.get_cookies():
            print(cookie['name'], cookie['value'])
            session_obj.cookies.set(cookie['name'], cookie['value'])
        TIMEOUT = 600
        browser = self.browser
        key_set = set()
        user_set = set()
        posts = []
        users = {}
        pre_post_num = 0
        wait_time = 1
        read_feed = 0

        pbar = tqdm(total=num)

        def start_fetching(pre_post_num, wait_time, read_feed):
            ele_posts = browser.find(".v1Nh3 a")
            for ele in ele_posts:
                key = ele.get_attribute("href")
                if key not in key_set:
                    read_feed += 1
                    dict_post = { "key": key }
                    ele_img = browser.find_one(".KL4Bh img", ele)
                    dict_post["caption"] = ele_img.get_attribute("alt")
                    dict_post["img_url"] = ele_img.get_attribute("src")
                    html = get_html(key+"?__a=1", session_obj)
                    try:
                        img_type = parseFeedImageCaption(dict_post['caption'], dict_post)
                        user_data = parseFeedInfo(html, dict_post)
                    except:
                        print(html)
                        # output(posts, tag+"_post_detail")
                        return
                        print("exception occur")
                        traceback.print_exc()
                        continue

                    # 이미지의 타입이 없거나 혹은 이미지의 타입이 음식이 아닌 경우
                    if not img_type or "음식" not in img_type:
                        # print("fail:", "no image type or no image loc")
                        continue
                    # 피드의 위치가 포함되지 않는 경우
                    # elif not dict_post['location']:
                        # print("fail:", "image type is not food")
                        # continue
                    # 피드의 개수가 20개 이하일 경우 500개 이상일 경우 제외
                    elif user_data['feed_nums'] < 20:
                        continue
                    # 팔로워수가 1000명 이하일 경우 제외
                    # elif user_data['follower'] < 500:
                    #     continue
                    # 검색한 해시 태그가 피드에 포함되어 있지 않은 경우
                    # elif "맛집" not in dict_post['hash_tag']:
                        # print("fail:", "feed does not have hashtag")
                        # print(dict_post['hash_tag'])
                        # continue
                    # print('success')
                    # 유저 정보 추가
                    if user_data['username'] not in users:
                        users[user_data['username']] = user_data
                        user_set.add(user_data['username'])

                    users[user_data['username']]['feed_urls'].append(dict_post['key'])

                    key_set.add(key)
                    posts.append(dict_post)

                    if len(posts) == num and len(users) == num:
                        break

            if pre_post_num == len(posts):
                pbar.set_description("Wait for %s sec" % (wait_time))
                pbar.set_description("fetching so far: %s" % (read_feed))

                wait_time = 3 # 나중에 조정해봐야지!
                browser.scroll_up(300)
            else:
                wait_time = 5
            wait_time = 4
            sleep(wait_time)

            pre_post_num = len(posts)
            browser.scroll_down()

            return pre_post_num, wait_time, read_feed

        pbar.set_description("fetching")
        while len(posts) < num or len(users) < num:
            read_feed_before = read_feed
            post_num, wait_time, read_feed = start_fetching(pre_post_num, wait_time, read_feed)
            pbar.update(post_num - pre_post_num)
            pre_post_num = post_num

            loading = browser.find_one(".W1Bne")
            if not loading and wait_time > TIMEOUT / 2:
                break
            if read_feed_before == read_feed or read_feed > 10000:
                print("post_num:", post_num)
                print("finish")
                break

        pbar.close()
        print("Done. Fetched %s posts." % (min(len(posts), num)))
        return posts, users, key_set, user_set

    def jieun(self):
        guList = ['동대문구', '구로구']
        # guList.reverse()
        foodCategroy = ['닭/오리요리', '별식/퓨전요리', '분식', '양식', '일식/수산물', '제과제빵떡케익', '중식', '패스트푸드', '한식']
        foodRestaurantDict = {type : 0 for type in foodCategroy}
        for gu in guList:
            print(gu)
            for food in foodCategroy:
                if gu =='동대문구' and food in ['한식', '닭/오리요리']:
                    continue
                tag = food
                if '/' in food:
                    tag = food.split('/')[0]
                self.browser.get("https://www.instagram.com/explore/tags/"+tag)
                sleep(1)
                foodName = food.replace('/', '_')
                restaurant_info = read_json("../data/ssgi/ssgi_data_" + gu + "_" + foodName + ".json")
                search_result = self.top_search(restaurant_info)
                save_json("ssgi/ssgi_data_search_result" + gu + "_" + foodName + ".json", search_result)

    def top_search(self, querys):
        result = {}
        for query in tqdm(querys):
            # try:
            q = query['상호명']
            # u_input = self.browser.driver.find_element_by_css_selector('input.XTCLo.x3qfX')
            # print(self.browser.driver.page_source)
            u_input = self.browser.find_one('.XTCLo')
            u_input.clear()
            u_input.send_keys(q)
            sleep(0.6)
            # tags = self.browser.driver.find_elements_by_class_name("Ap253")
            # nums = self.browser.driver.find_elements_by_class_name("Fy4o8")
            soup = BeautifulSoup(self.browser.driver.page_source, 'html.parser')
            tags = soup.find_all('span', {'class':'Ap253'})
            nums = soup.find_all('div', {'class':'Fy4o8'})
            if not tags or not nums:
                continue
            for tag, num in zip(tags, nums):
                if tag.text == '#'+q:
                    result[query['상호명']] = {'tag':q, 'feed_num':num.text}
            # print(result)
            # q = query['상호명']
            # self.browser.get("https://www.instagram.com/explore/tags/"+q)
            # num = self.browser.find_one('.g47SY')
            # if not num:
            #     continue
            # result[query['상호명']] = {'tag':q, 'feed_num':num.text}
            # sleep(0.3)
            # except:
            #     sleep(300)
        return result

    def hankyul(self):
        # setting 1
        iter = "forth_iter"
        # user_list = read_json("../data/muckstar/firststart.json")['users']
        user_list = list(set(read_json("../data/muckstar/hankyul_new_user_list.json")))
        crawled_user_list = list(set([r['id'] for r in read_json("../data/muckstar/forth_iter_users.json")]))
        user_list = list(filter(lambda x : x not in crawled_user_list, user_list))
        # print(user_list)
        new_users = []
        posts = []
        users = []
        for user_info in tqdm(user_list):
            try:
                # setting 2
                # username = user_info['user']['username']
                username = user_info
                user = self.get_user_profile(username)
                if user['post_num'] < 70 or user['follower_num'] < 2000:
                    continue
                post, new_user = self.start_fetching(user)
                users.append(user)
                posts.append(post)
                new_users.extend(new_user)
            except:
                save_json(f"muckstar/{iter}_users", users)
                save_json(f"muckstar/{iter}_posts", posts)
                save_json(f"muckstar/{iter}_new_users", new_users)
                continue
        save_json(f"muckstar/{iter}_users", users)
        save_json(f"muckstar/{iter}_posts", posts)
        save_json(f"muckstar/{iter}_new_users", new_users)

    def start_fetching(self, user):
        # 모든 포스트 선택
        browser = self.browser
        ele_posts = browser.find(".v1Nh3 a")
        posts = []
        new_users = []
        for ele in tqdm(ele_posts):
            # 포스트 URL 선택
            key = ele.get_attribute("href")
            dict_post = { "key": key }
            dict_post = {"user" : user['name']}
            dict_post = {"userID" : user['id']}
            # 이미지 정보 선택
            ele_img = browser.find_one(".KL4Bh img", ele)
            hover = ActionChains(browser.driver).move_to_element(ele_img)
            hover.perform()
            dict_post["caption"] = ele_img.get_attribute("alt")
            dict_post["img_url"] = ele_img.get_attribute("src")
            # 이미지가 음식이 아닐 경우 제외
            img_type = ''
            try:
                img_type = parseFeedImageCaption(dict_post['caption'], dict_post)
            except:
                continue
            if not img_type or "음식" not in img_type:
                continue
            # 좋아요, 댓글수 파싱
            soup = BeautifulSoup(browser.driver.page_source, 'html.parser')
            child_qn = list(soup.find('div', {'class':'qn-0x'}).children)[0]
            like_reply = [el.text for el in child_qn.children]
            dict_post["like_reply"] = like_reply
            ele.click()
            sleep(1.7)
            # 페이지 파싱
            soup = BeautifulSoup(browser.driver.page_source, 'html.parser')
            # caption, hashtag, time
            origin_caption = soup.find('div', {'class':'C4VMK'}).find('span', recursive=False)
            hashtags = [hashtag.text for hashtag in origin_caption.find_all('a', {'class':'xil3i'})]
            # time = origin_caption.time['title']
            dict_post['origin_caption'] = origin_caption.text
            dict_post['hashtags'] = hashtags
            # dict_post['time'] = time
            # reply(중복제거)
            def interesting_tags(tag):
                if tag.name == "a":
                    classes = tag.get("class", [])
                    return "sqdOP" in classes and "yWX7d" in classes and "_8A5w5" in classes and "ZIAjV" in classes

            replys = [reply.text for reply in soup.find_all(interesting_tags)]
            replys = list(filter(lambda x : x != user['name'], replys))
            # print(replys)
            dict_post['replys'] = replys
            # 닫기 버튼 선택
            exit_button = browser.find_one(".wpO6b")
            ac = ActionChains(browser.driver)
            ac.move_to_element(exit_button).move_by_offset(0, -50).click().perform()
            sleep(0.3)
            posts.append(dict_post)
            new_users.extend(replys)
        return posts, new_users

    def cheol(self):
        # setting 1
        iter = "first_iter"
        # user_list = read_json("../data/muckstar/firststart.json")['users']
        foodCategroy = ["한식"]
        restaurant_list_data = read_json("../data/postdata/result.json")
        for food in foodCategroy:
            iter = food.replace("/", "_")
            restaurant_list = restaurant_list_data['중구'][food]
            restaurant_list = [r['name'] for r in restaurant_list['non_franchise']['top_rank'][:50]] + [r['name'] for r in restaurant_list['franchise']['top_rank'][:50]]
            # print(user_list)
            posts = []
            for restaurant in tqdm(restaurant_list):
                try:
                    # setting 2
                    # username = user_info
                    # print(restaurant)
                    self.browser.get("https://www.instagram.com/explore/tags/"+restaurant)
                    sleep(2)
                    post = self.start_fetching2(restaurant)
                    posts.append(post)
                except:
                    sleep(0.1)
                    save_json(f"postdata/{iter}_posts", posts)
                    continue
            save_json(f"postdata/{iter}_posts", posts)

    def start_fetching2(self, restaurant):
        # 모든 포스트 선택
        browser = self.browser
        # browser.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # sleep(2)
        ele_posts = browser.find(".v1Nh3 a")
        posts = []
        # print("hello")
        for ele in tqdm(ele_posts):
            # 포스트 URL 선택
            key = ele.get_attribute("href")
            dict_post = { "key": key }
            # 이미지 정보 선택
            ele_img = browser.find_one(".KL4Bh img", ele)
            hover = ActionChains(browser.driver).move_to_element(ele_img)
            hover.perform()
            dict_post['restaurant'] = restaurant
            dict_post["caption"] = ele_img.get_attribute("alt")
            dict_post["img_url"] = ele_img.get_attribute("src")
            # 이미지가 음식이 아닐 경우 제외
            img_type = ''
            try:
                img_type = parseFeedImageCaption(dict_post['caption'], dict_post)
            except:
                continue
            if not img_type or "음식" not in img_type:
                continue
            # 좋아요, 댓글수 파싱
            sleep(0.1)
            soup = BeautifulSoup(browser.driver.page_source, 'html.parser')
            if soup.find('div', {'class':'qn-0x'}) is None:
                continue
            child_qn = list(soup.find('div', {'class':'qn-0x'}).children)[0]
            like_reply = [el.text for el in child_qn.children]
            dict_post["like_reply"] = like_reply
            ele.click()
            sleep(1.7)
            # 페이지 파싱
            soup = BeautifulSoup(browser.driver.page_source, 'html.parser')
            # caption, hashtag, time
            origin_caption = soup.find('div', {'class':'C4VMK'}).find('span', recursive=False)
            hashtags = [hashtag.text for hashtag in origin_caption.find_all('a', {'class':'xil3i'})]
            # time = origin_caption.time['title']
            dict_post['origin_caption'] = origin_caption.text
            dict_post['hashtags'] = hashtags
            # dict_post['time'] = time
            # reply(중복제거)
            # def interesting_tags(tag):
            #     if tag.name == "a":
            #         classes = tag.get("class", [])
            #         return "sqdOP" in classes and "yWX7d" in classes and "_8A5w5" in classes and "ZIAjV" in classes
            # replys = [reply.text for reply in soup.find_all(interesting_tags)]
            # replys = list(filter(lambda x : x != user['name'], replys))
            # print(replys)
            # dict_post['replys'] = replys
            # 닫기 버튼 선택
            exit_button = browser.find_one(".wpO6b")
            ac = ActionChains(browser.driver)
            ac.move_to_element(exit_button).move_by_offset(0, -50).click().perform()
            sleep(0.3)
            posts.append(dict_post)
        return posts
