from apscheduler.schedulers.blocking import BlockingScheduler
from utils.notify import NotifyUtil
from db_manager import DBManager
from utils.openaiUtil import ask_analysis_from_openai
from utils.logger_settings import api_logger
from datetime import datetime
import os


CURSOR_FILE = 'tweet_cursor.txt'

def get_last_cursor():
    """
    从本地文件中获取上次存储的游标（最新推文的发布时间）。
    如果文件不存在或读取失败，返回 None。
    """
    if os.path.exists(CURSOR_FILE):
        try:
            with open(CURSOR_FILE, 'r') as f:
                cursor_str = f.read().strip()
                if cursor_str:
                    return datetime.fromisoformat(cursor_str)
        except Exception as e:
            api_logger.error(f"读取游标文件出错: {e}")
    return None

def save_cursor(cursor):
    """
    将最新推文的发布时间作为游标存储到本地文件中。
    """
    try:
        with open(CURSOR_FILE, 'w') as f:
            f.write(cursor.isoformat())
    except Exception as e:
        api_logger.error(f"保存游标文件出错: {e}")

def getDailyReport():
    db_manager = DBManager()
    # 从数据库获取最新 10 条 isCryptoRelated 为 True 的推文
    tweets = db_manager.get_latest_crypto_related_tweets(20)
    if tweets:
        api_logger.info(f"获取到 {len(tweets)} 条推文")
        # 收集所有推文标题
        tweet_contents = [tweet.get('title') for tweet in tweets]
        combined_content = "\n".join(tweet_contents)
        try:
            # 使用 OpenAI 一次性分析所有推文
            analysis_result = ask_analysis_from_openai(combined_content)
            analysis_result_str = "\n".join([f"{key}: {value}" for key, value in analysis_result.items()])

            api_logger.info(f"推文内容: {combined_content}\n分析结果: {analysis_result_str}")  
            NotifyUtil.notifyFeishu(f"分析结果: \n{analysis_result_str}")
        except Exception as e:
            print(f"分析推文出错: {e}")
            NotifyUtil.notifyFeishu(f"分析推文出错: {e}")


def getDailyNewTweets():
    db_manager = DBManager()
    # 从数据库获取最新 10 条 isCryptoRelated 为 True 的推文
    tweets = db_manager.get_latest_crypto_related_tweets_since(get_last_cursor(), 20)
    if tweets:
        api_logger.info(f"获取到 {len(tweets)} 条新推文")
        # 收集所有推文标题
        tweet_contents = [tweet.get('title') for tweet in tweets]
        combined_content = "\n\n\n".join(tweet_contents)

        api_logger.info(f"推文内容: \n{combined_content}")  
        NotifyUtil.notifyFeishu(f"推文内容: \n{combined_content}")

        # 更新游标为最新推文的发布时间
        latest_published = max(tweet.get('published') for tweet in tweets)
        save_cursor(latest_published)
    else:
        api_logger.info("未获取到新的相关推文")
        
        
def daily_task():
    getDailyReport()
    getDailyNewTweets()

if __name__ == "__main__":
    daily_task()
    scheduler = BlockingScheduler()
    # 每天早上 8 点执行任务
    scheduler.add_job(daily_task, 'cron', hour=8)
    print("定时任务已启动，每天早上 8 点执行")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
