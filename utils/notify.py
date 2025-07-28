

from utils.curl import Curl
from utils.util import Util


class NotifyUtil:
    @staticmethod
    def notifyFeishu(msg:str):
        notifyUrl = "https://open.feishu.cn/open-apis/bot/v2/hook/6a98b9a1-650c-4b80-95d9-314fed9113efc"
        para = {
            "msg_type":"text",
            "content":{
                "text":msg
            }
        }
        codeResponse = Curl.Request(notifyUrl, Util.JsonEncode(para), 'POST', {})




