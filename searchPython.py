# https://search.inetol.net/


import requests

url = "https://searx.rhscz.eu/"
params = {
    "q": "GitHub",
    "format": "json",
    "category": "general",
    "language": "zh-CN",
    "safesearch": 1
}

response = requests.get(url, params=params)
data = response.json()

# 打印搜索结果
for result in data.get("results", []):
    print(f"标题: {result['title']}")
    print(f"链接: {result['url']}")
    print(f"摘要: {result['content'][:50]}...")
    print("-" * 50)