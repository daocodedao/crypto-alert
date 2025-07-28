from apscheduler.schedulers.blocking import BlockingScheduler
from utils.notify import NotifyUtil
from db_manager import DBManager
from utils.openaiUtil import ask_analysis_from_openai
from utils.logger_settings import api_logger


def daily_task():
    db_manager = DBManager()
    # 从数据库获取最新 10 条 isCryptoRelated 为 True 的推文
    tweets = db_manager.get_latest_crypto_related_tweets(10)
    if tweets:
        for tweet in tweets:
            tweet_content = tweet.get('title')
            try:
                # 使用 OpenAI 分析推文
                analysis_result = ask_analysis_from_openai(tweet_content)
                api_logger.info(f"推文内容: {tweet_content}\n分析结果: {analysis_result}")  
                NotifyUtil.notifyFeishu(f"分析结果: {analysis_result}")
            except Exception as e:
                print(f"分析推文出错: {e}")


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
