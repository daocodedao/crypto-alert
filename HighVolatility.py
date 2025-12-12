import requests
from binance.client import Client

from binance.exceptions import BinanceAPIException
from datetime import datetime
import time
from utils.util import Util
import os


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
    


def get_contract_top100_volume_pairs():
    """
    获取币安合约市场过去24小时成交金额排名前100的交易对
    :return: 按成交金额降序排列的前100合约对列表（含symbol、成交金额等）
    """
    # 币安合约24小时价格变动接口（永续+交割合约通用）
    # https://developers.binance.com/docs/zh-CN/derivatives/usds-margined-futures/market-data/rest-api/24hr-Ticker-Price-Change-Statistics
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    
    # 请求参数（可选：filterType=PERPETUAL 仅筛选永续合约，默认返回所有合约）
    params = {
        # "filterType": "PERPETUAL"  # 如需仅看永续合约，取消注释
    }
    excludeParis = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT", "UNIUSDT", "SUIUSDT"]
    
    try:
        # 发送请求（合约公开接口，无需鉴权）
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()  # 抛出HTTP错误（如403、500）
        data = response.json()
        
        # 过滤有效合约对（排除暂停交易、已下架的）
        valid_contracts = [
            contract for contract in data
            if "USDT" in contract.get("symbol")   # 仅保留正常交易的合约
            and contract["symbol"] not in excludeParis
            and float(contract.get("quoteVolume", 0)) > 0  # 排除成交金额为0的
        ]
        
        # 按24h成交金额（quoteVolume）降序排序（转换为float比较）
        sorted_contracts = sorted(
            valid_contracts,
            key=lambda x: float(x["quoteVolume"]),
            reverse=True
        )
        
        # 取前10名，提取关键信息（排名、交易对、成交金额、涨跌幅）
        top10 = [
            {
                "rank": i + 1,
                "symbol": contract["symbol"],
                "24h_volume_usdt": round(float(contract["quoteVolume"]), 2),
                "24h_change": f"{float(contract['priceChangePercent']):.2f}%",
                "24h_trades": int(contract.get("count", 0))  # 24h成交笔数（可选）
            }
            for i, contract in enumerate(sorted_contracts[:10])
        ]
        
        return top10
    
    except requests.exceptions.RequestException as e:
        print(f"请求失败：{e}")
        # 若主域名失败，尝试备用域名（api1/api2）
        url_backup = "https://fapi1.binance.com/fapi/v1/ticker/24hr"
        try:
            response = requests.get(url_backup, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            # 重复过滤和排序逻辑（简化，与上方一致）
            valid_contracts = [c for c in data if c.get("status") == "TRADING" and float(c.get("quoteVolume", 0)) > 0]
            sorted_contracts = sorted(valid_contracts, key=lambda x: float(x["quoteVolume"]), reverse=True)
            top100 = [{"rank": i+1, "symbol": c["symbol"], "24h_volume_usdt": round(float(c["quoteVolume"]),2), "24h_change": f"{float(c['priceChangePercent']):.2f}%"} for i,c in enumerate(sorted_contracts[:100])]
            return top100
        except Exception as e2:
            print(f"备用域名请求也失败：{e2}")
            return None

def startGetContractTop100():
    top_contracts = get_contract_top100_volume_pairs()
    if top_contracts:
        # 打印前15名示例（合约市场头部更集中，前15名占比极高）
        print("币安合约市场24h成交金额前100交易对（前15名）：")
        print("-" * 80)
        print(f"{'排名':<4} {'交易对':<12} {'24h成交金额(USDT)':<22} {'24h涨跌幅':<10}")
        print("-" * 80)
        for contract in top_contracts[:15]:
            print(
                f"{contract['rank']:<4} "
                f"{contract['symbol']:<12} "
                f"{contract['24h_volume_usdt']:<22,.2f} "
                f"{contract['24h_change']:<10}"
            )
        
        # 保存完整前100名到CSV（可选）
        import csv
        with open("binance_contract_top100_volume.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=top_contracts[0].keys())
            writer.writeheader()
            writer.writerows(top_contracts)
        print("\n完整前100名已保存到 binance_contract_top100_volume.csv")


def get_funding_rate_history(symbol="BTCUSDT", limit=100):
    """
    获取指定交易对的历史资金费率
    
    :param symbol: 交易对名称，默认为BTCUSDT
    :param limit: 获取记录的数量，默认为100条
    :return: 包含历史资金费率的列表
    """
    # 初始化Binance客户端（无需API密钥，因为只需要访问公共数据）
    client = getBinanceClient()
    
    try:
        # 获取历史资金费率
        # API文档: https://binance-docs.github.io/apidocs/futures/en/#get-funding-rate-history
        funding_rates = client.futures_funding_rate(symbol=symbol, limit=limit)
        
        # 格式化数据
        formatted_rates = []
        for rate in funding_rates:
            formatted_rates.append({
                "symbol": rate['symbol'],
                "fundingTime": datetime.fromtimestamp(rate['fundingTime'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                "fundingRate": float(rate['fundingRate']) * 100  # 转换为百分比
            })
        
        return formatted_rates
    
    except BinanceAPIException as e:
        print(f"获取资金费率历史失败：{e}")
        return None


def startGetFundingRateHistory():
    # 获取资金费率历史示例
    print("\n" + "="*50)
    print("币安合约市场资金费率历史示例（BTCUSDT）：")
    print("-" * 50)
    funding_rates = get_funding_rate_history()
    if funding_rates:
        print(f"{'时间':<20} {'交易对':<12} {'资金费率':<10}")
        print("-" * 50)
        for rate in funding_rates[:10]:  # 显示最近10条记录
            print(f"{rate['fundingTime']:<20} {rate['symbol']:<12} {rate['fundingRate']:.4f}%")


def get_latest_mark_price_and_funding_rate(symbol="BTCUSDT"):
    """
    获取指定交易对的最新标记价格和资金费率
    
    :param symbol: 交易对名称，默认为BTCUSDT
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
            "indexPrice": float(mark_price['indexPrice']),
            "estimatedSettlePrice": float(mark_price['estimatedSettlePrice']),
            "lastFundingRate": float(funding_rate[0]['fundingRate']) * 100 if funding_rate else None,  # 转换为百分比
            "nextFundingTime": datetime.fromtimestamp(int(mark_price['nextFundingTime']) / 1000).strftime('%Y-%m-%d %H:%M:%S') if mark_price['nextFundingTime'] else None
        }
        
        return result
    
    except BinanceAPIException as e:
        print(f"获取标记价格和资金费率失败：{e}")
        return None


def startGetLatestMarkPriceAndFundingRate():
    # 获取最新标记价格和资金费率示例
    
    print("\n" + "="*60)
    symbol = "LUNA2USDT"
    # PIPPINUSDT
    print("币安合约市场最新标记价格和资金费率示例：")
    print("-" * 60)
    data = get_latest_mark_price_and_funding_rate(symbol)
    if data:
        print(f"{'交易对':<12} {'标记价格':<15} {'指数价格':<15} {'预估结算价':<15} {'资金费率':<10} {'下次资金费用时间':<20}")
        print("-" * 60)
        print(f"{data['symbol']:<12} "
              f"{data['markPrice']:<15.2f} "
              f"{data['indexPrice']:<15.2f} "
              f"{data['estimatedSettlePrice']:<15.2f} "
              f"{data['lastFundingRate']:<10.4f}% " if data['lastFundingRate'] else f"{'N/A':<10} "
              f"{data['nextFundingTime']:<20}")




# 执行并打印结果
if __name__ == "__main__":
    
    startGetLatestMarkPriceAndFundingRate()
