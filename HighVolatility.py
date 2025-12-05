import requests

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

# 执行并打印结果
if __name__ == "__main__":
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