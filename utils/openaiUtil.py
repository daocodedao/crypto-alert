
from openai import OpenAI
from typing import List, Dict, Tuple

from utils.logger_settings import api_logger



openAiClient = OpenAI(base_url="http://39.105.194.16:6691/v1", api_key="key")

def ask_is_crypto_related_from_openai(content: str) -> Dict:

    try:
        prompt = f"""请判断以下内容是否和虚拟货币相关，返回格式为JSON:
        
        推文信息: {content}
        
        请仅返回JSON格式数据，不要有其他文字说明，格式如下:
        {{
            "isRelated": false,
        }}
        """
        
        response = openAiClient.chat.completions.create(
            model="Qwen/Qwen3-8B",
            messages=[
                {"role": "system", "content": "你是一个专业的中国大学信息助手，请提供准确的大学信息。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        # 提取返回的JSON内容
        content = response.choices[0].message.content.strip()
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        # 处理可能的JSON格式问题
        import json
        import re
        
        # 尝试提取JSON部分
        json_match = re.search(r'({.*})', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        university_info = json.loads(content)
        
        # 确保返回所有必要字段
        return {
            "name_en": university_info.get("name_en", ""),
            "website": university_info.get("website", ""),
            "city": university_info.get("city", "")
        }
        
    except Exception as e:
        api_logger.error(f"从OpenAI获取大学信息失败: {e}")
        # 返回空信息
        return {
            "name_en": "",
            "website": "",
            "city": ""
        }