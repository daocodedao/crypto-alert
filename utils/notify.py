

from utils.curl import Curl
from utils.util import Util


class NotifyUtil:
    @staticmethod
    def notifyFeishu(msg:str):
        notifyUrl = "https://open.feishu.cn/open-apis/bot/v2/hook/5550de0e-bf8e-423c-9495-9fbf929d457c"
        para = {
            "msg_type":"text",
            "content":{
                "text":msg
            }
        }
        codeResponse = Curl.Request(notifyUrl, Util.JsonEncode(para), 'POST', {})




