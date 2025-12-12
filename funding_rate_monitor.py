import schedule
import time
from binance.client import Client
from binance.exceptions import BinanceAPIException
from datetime import datetime
import os

from utils.notify import NotifyUtil
from utils.util import Util

def getBinanceClient():
    # 获取代理设置
    proxy = Util.getProxy()
    
    # 如果有代理设置，则配置环境变量
    if proxy:
        os.environ['HTTP_PROXY'] = f'http://{proxy}'
        os.environ['HTTPS_PROXY'] = f'https://{proxy}'
    
    # 初始化Binance客户端（无需API密钥，因为只需要访问公共数据）
    client = Client()
    
    return client

def get_latest_mark_price_and_funding_rate(symbol):
    """
    获取指定交易对的最新标记价格和资金费率
    
    :param symbol: 交易对名称
    :return: 包含标记价格和资金费率的字典
    """
    # 初始化Binance客户端（无需API密钥，因为只需要访问公共数据）
    client = getBinanceClient()
    
    try:
        # 获取标记价格
        mark_price = client.futures_mark_price(symbol=symbol)
        
        # 获取当前资金费率
        funding_rate = client.futures_funding_rate(symbol=symbol, limit=1)
        
        # 格式化数据
        result = {
            "symbol": mark_price['symbol'],
            "markPrice": float(mark_price['markPrice']),
            "lastFundingRate": float(funding_rate[0]['fundingRate']) * 100 if funding_rate else None,  # 转换为百分比
            "nextFundingTime": datetime.fromtimestamp(int(mark_price['nextFundingTime']) / 1000).strftime('%Y-%m-%d %H:%M:%S') if mark_price['nextFundingTime'] else None
        }
        
        return result
    
    except BinanceAPIException as e:
        print(f"获取{symbol}标记价格和资金费率失败：{e}")
        return None

def check_funding_rate_threshold(symbol, threshold=0.1):
    """
    检查资金费率是否超出阈值
    
    :param symbol: 交易对名称
    :param threshold: 阈值（默认0.1%）
    :return: None
    """
    data = get_latest_mark_price_and_funding_rate(symbol)
    if data and data['lastFundingRate'] is not None:
        funding_rate = data['lastFundingRate']
        if abs(funding_rate) > threshold:
            # 打印通知（后续可以替换为其他通知方式）
            analysis_result_str = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 警告：{symbol} 资金费率异常！\n"
            analysis_result_str = analysis_result_str + f"  标记价格: {data['markPrice']:.4f}\n"
            analysis_result_str = analysis_result_str + f"  资金费率: {funding_rate:.4f}%\n"
            analysis_result_str = analysis_result_str + f"\n  下次结算时间: {data['nextFundingTime']}\n"
            analysis_result_str = analysis_result_str + "-" * 50
            
            NotifyUtil.notifyFeishu(analysis_result_str)


def monitor_funding_rates():
    """
    监控指定交易对的资金费率
    """
    symbols = ["LUNA2USDT", "PIPPINUSDT"]
    threshold = 0.1  # 0.1% 阈值
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始监控资金费率...")
    
    for symbol in symbols:
        check_funding_rate_threshold(symbol, threshold)

def start_monitoring():
    """
    启动定时监控任务
    """
    # 每小时的55分执行一次监控
    schedule.every().hour.at(":55").do(monitor_funding_rates)
    
    print("资金费率监控已启动，将在每小时55分检查LUNA2USDT和PIPPINUSDT的资金费率...")
    print("按Ctrl+C退出程序")
    
    # 初始执行一次
    monitor_funding_rates()
    
    # 持续运行调度器
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    start_monitoring()
    # monitor_funding_rates()