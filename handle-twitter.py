# pip install DiscordWebhook
# https://github.com/S-PScripts/chromebook-utilities/blob/700fb88ca6f14959a1b57e39942ac0013dc78575/Alternatives/Twitter%20(X)%20Altenative%20Links.txt#L22
# https://twiiit.com/
from bs4 import BeautifulSoup
import requests
import xml.etree.ElementTree as ET

from utils.logger_settings import api_logger
from datetime import datetime, timedelta
import json
import schedule
import time
import feedparser
from db_manager import DBManager
from utils.openaiUtil import ask_is_crypto_related_from_openai



# 初始化 DBManager 实例
db_manager = DBManager()

class AiTwitter:
    # twitter 内容
    content: str
    # twitter id
    twitterId: str
    # 作者名
    creatorName: str
    # 发布时间
    pubDate: datetime


# TWITTER = "http://twiiit.com"  # picks a random, online-only nitter instance
TWITTER = "https://rss.xcancel.com/"
# https://rss.xcancel.com/TingHu888/rss

TWITTER_INSTANCES = [
    "https://rss.xcancel.com/",
    "https://nitter.tiekoetter.com/",
    
    "https://nitter.privacydev.net/",
    # "https://nitter.poast.org/",
    # "https://nitter.space/",
    # "https://lightbrd.com/",
    # "https://nitter.lucabased.xyz/",
    
]

TWITTER_NAME = "TingHu888"
DQX_TWITTER = f"{TWITTER}/{TWITTER_NAME}"
RSS_FEED = DQX_TWITTER + "/rss"
TWEET_STATUS = DQX_TWITTER + "/status"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 RSSFeedReader/1.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15 RSSFeedReader/2.0",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Mobile Safari/537.36 RSSFeedReader/3.0"
]

import random

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def parse_tweet_from_url(tweetUrl: str):
    headers = {
        "User-Agent": get_random_user_agent()
    }
    response = requests.get(url=tweetUrl, headers=headers)
    if response.status_code != 200:
        api_logger.info(f"Could not get nitter data.")
        # sys.exit(1)
        return None

    rss_data = ET.fromstring(response.text)
    twitterList = []
    for row in rss_data[0].iter("item"):
        twitterItem: AiTwitter = AiTwitter()
        # get tweet id to see if we've seen it before.
        link = row.find("link").text

        nitter_instance = link.split("/")[2]
        tweetId = link.split("/")[-1].rstrip("#m")

        api_logger.debug(f"URL: {nitter_instance}")
        api_logger.debug(f"新twitter: {tweetId}")
        twitterItem.twitterId = tweetId

        # get the tweet image first (if it exists)
        tweet_description = row.find("description").text

        namespace = {"dc": "http://purl.org/dc/elements/1.1/"}
        creator = row.find("dc:creator", namespaces=namespace).text
        creator = creator.replace("@", "")
        twitterItem.creatorName = creator

        pubDateStr = row.find("pubDate").text
        dt = datetime.strptime(pubDateStr, "%a, %d %b %Y %H:%M:%S %Z")
        twitterItem.pubDate = dt
        # soup = BeautifulSoup(tweet_description, "html.parser")

        # image = soup.find("img")
        # if image:
        #     # "x" (twitter) images link from this domain. will be more reliable than nitter.
        #     image = "https://pbs.twimg.com/media/" + image["src"].split('%2F')[-1] + "?format=jpg"
        #     api_logger.info(f"Tweet has image: {image}")

        # get the tweet text
        tweet_text = row.find("title").text
        twitterItem.content = tweet_text
        api_logger.debug(f"tweet_text:{tweet_text}")
        twitterList.append(twitterItem)

    return twitterList

def read_rss_feed(feed_url):
    """
    读取并解析 RSS 源。

    :param feed_url: RSS 源的 URL
    :return: 包含 RSS 条目信息的列表，如果出错则返回空列表
    """
    try:
        # 使用 feedparser 解析 RSS 源
        feed = feedparser.parse(feed_url)
        if feed.bozo:
            api_logger.error(f"解析 RSS 源 {feed_url} 时出错: {feed.bozo_exception}")
            return []
        entries = []
        for entry in feed.entries:
            url = entry.get('id')
            parts = url.split("/")
            tweet_id = parts[-1].rstrip("#m")

            published_str = entry.get('published', '无发布时间')
            try:
                # 将发布时间字符串转换为 datetime 对象
                published_dt = datetime.strptime(published_str, "%a, %d %b %Y %H:%M:%S %Z")
            except ValueError:
                api_logger.warning(f"无法解析发布时间: {published_str}")
                published_dt = None

            entry_info = {
                'title': entry.get('title', '无标题'),
                'link': entry.get('link', '无链接'),
                'description': entry.get('description', '无描述'),
                'published': published_dt,
                'tweet_id': tweet_id,
                'author': entry.get('author', '无作者')
            }
            entries.append(entry_info)
        return entries
    except Exception as e:
        api_logger.error(f"读取 RSS 源 {feed_url} 时出错: {e}")
        return []
    
    


def get_tweet_fromName(name: str):
    for instance in TWITTER_INSTANCES:
        rssUrl = f"{instance}{name}/rss"
        try:
            # twitterList = parse_tweet_from_url(rssUrl)
            twitterList = read_rss_feed(rssUrl)
            if twitterList and len(twitterList) > 0:
                new_twitter_list = []
                for entry in twitterList:
                    if not db_manager.is_tweet_id_exists(entry['tweet_id']):
                        api_logger.info(f"新推特: {entry['tweet_id']} content:{entry['title']} 没在数据库中，判断是否币圈相关")
                        is_crypto_related = ask_is_crypto_related_from_openai(entry['title'])
                        entry['isCryptoRelated'] = is_crypto_related
                        new_twitter_list.append(entry)
                if new_twitter_list:
                    db_manager.insert_twitter_entries(new_twitter_list)
                api_logger.info(f"解析 {rssUrl} 成功")
                return twitterList
            else:
                api_logger.info(f"解析 {rssUrl} 失败, 未获取到内容")
        except Exception as e:
            api_logger.info(f"解析 {rssUrl} 失败: {e}")
            continue

def parese_tweet_from_json():
    api_logger.info("打开 twitter.json 文件并读取内容")
    with open("twitter.json", "r", encoding="utf-8") as file:
        # 解析 JSON 数据
        data = json.load(file)

    # 打印解析后的数据
    for account in data:
        twitterName = account.get("twitterAccoutn")
        api_logger.info(f"Twitter 账号: {twitterName}")
        twitterList = get_tweet_fromName("TingHu888")
        if twitterList and len(twitterList) > 0:
            api_logger.info(f"Twitter 账号: {twitterName} 共抓取到 {len(twitterList)} 条推特")
        else:
            api_logger.info(f"Twitter 账号: {twitterName} 没抓到内容")


if __name__ == "__main__":
    parese_tweet_from_json()
    # api_logger.info("done")
    # 每小时执行一次 parese_tweet_from_json 函数
    schedule.every(4).hours.do(parese_tweet_from_json)

    while True:
        schedule.run_pending()
        time.sleep(1)
