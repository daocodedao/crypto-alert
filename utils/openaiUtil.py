
from openai import OpenAI
from typing import List, Dict, Tuple
# 处理可能的JSON格式问题
import json
import re

import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.logger_settings import api_logger



openAiClient = OpenAI(base_url="http://39.105.194.16:6691/v1", api_key="key")

def ask_is_crypto_related_from_openai(content: str) -> Dict:

    try:
        prompt = f"""
        推文信息: {content}
        
        请仅返回JSON格式数据，不要有其他文字说明，格式如下:
        {{
            "isRelated": false,
        }}
        """
        
        response = openAiClient.chat.completions.create(
            model="Qwen/Qwen3-8B",
            messages=[
                {"role": "system", "content": "你是一个内容分析师，判断内容是否和以下主题相关：1. 虚拟货币\n2.加密货币\n3.投资相关 "},
                {"role": "user", "content": prompt}
            ]
        )
        
        # 提取返回的JSON内容
        content = response.choices[0].message.content.strip()
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

        # 尝试提取JSON部分
        json_match = re.search(r'({.*})', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        dic_info = json.loads(content)
        isRelated = dic_info["isRelated"]
        # 确保返回所有必要字段
        return isRelated
    
    except Exception as e:
        api_logger.error(f"从OpenAI获取大学信息失败: {e}")
        # 返回空信息
        return False


def ask_analysis_from_openai(content: str):
    try:
        prompt = f"""
以下内容是 twitter 用户的发言，从发言中判断 crypto 币圈
1.目前是否见顶
2.看好哪些币
3.预计什么时候到顶
4.对后市的看法

推文信息: {content}

请仅返回 JSON 格式数据，不要有其他文字说明，格式如下:
{{
    "目前是否见顶": false,
    "看好的币": [],
    "预计什么时候到顶": null,
    "后市看法": ""
}}
"""
        response = openAiClient.chat.completions.create(
            model="Qwen/Qwen3-8B",
            messages=[
                {"role": "system", "content": "你是一个专业的加密货币分析师。"},
                {"role": "user", "content": prompt}
            ]
        )
        # 提取返回的 JSON 内容
        content = response.choices[0].message.content.strip()
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

        # 尝试提取 JSON 部分
        json_match = re.search(r'({.*})', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        dic_info = json.loads(content)
        return dic_info
    except Exception as e:
        api_logger.error(f"从 OpenAI 获取分析信息失败: {e}")
        return {}
    
if __name__ == "__main__":   
    content="为什么我以前讲过让大家记录自己的情绪与对应的市场状态和价格呢？就是制定适合自己的情绪投资体系，因为每一个人对市场的情绪感知以及自己在不同时候的情绪感知都是不一样的。每一个人忍不住想买的那种参照基准是不一样的，这种程度需要自己去体会。比如，同样被骂傻逼，有人气急败坏，有人云淡风轻。"
    isRelated = ask_is_crypto_related_from_openai(content)
    api_logger.info(f"返回结果：{isRelated}")
