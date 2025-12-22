from core.config import settings
from middleware.logging import logger
from ronglian_sms_sdk import SmsSDK

class SmsUtil:
    _instance = None
    _acc_id = settings.rong_lian_acc_id
    _app_id = settings.rong_lian_app_id
    _acc_token = settings.rong_lian_acc_token
    _sdk = SmsSDK(_acc_id, _acc_token, _app_id)

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls.instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    async def send_sms(cls, phone: str, code: str):
        """
        发送短信
        :param phone: 手机号
        :param code: 验证码
        :return:
        """

        tid = '1'
        mobile = phone
        datas = (code,)
        try:
            cls._sdk.sendMessage(tid, mobile, datas)
        except Exception as e:
           logger.error(e)
