import base64

import httpx
import requests
from fastapi import UploadFile, Request

from core.config import settings
from middleware.exception import BusinessException
from models.entity.user import User
from models.schemas.file import OCRResponse, OCRVo
from models.schemas.user import UserLoginRequest, UserLoginResponse, UserInfo, TokenData
from services.base import BaseService
from services.strategy.user_login_strategy import LoginStrategyFactory
from utils.jwt_utils import JWTUtil


class UserService(BaseService[User]):
    model = User

    async def login(self, login_data: UserLoginRequest) -> UserLoginResponse:
        """
        验证用户登录并返回 Token 和用户信息 (兼容旧接口命名)
        """
        return await self.authenticate(login_data)

    async def authenticate(self, login_data: UserLoginRequest) -> UserLoginResponse:
        """
        验证用户登录并返回 Token 和用户信息
        """
        # 1. 获取登录策略并执行登录
        strategy = LoginStrategyFactory.get_strategy(login_data.login_type)
        user: User = await strategy.execute(login_data)

        # 2. 检查激活状态
        if user.user_status == 0:
            raise BusinessException(message="该账号已被禁用", code=400)

        # 3. 生成 Token
        # JWTUtil.create_token 接受一个 dict 作为数据
        token_payload = {
            "sub": str(user.id),
            "username": user.username,
            "scope": "user"
        }
        access_token = JWTUtil.create_token(data=token_payload)

        # 4. 构造响应
        return UserLoginResponse(
            token=TokenData(access_token=access_token),
            user=UserInfo(
                id=user.id,
                username=user.username,
                phone=user.phone,
                is_active=user.user_status == 1,
            )
        )

    async def uploader_ocr(self, request: Request, side: str, file: UploadFile):
        """
        上传文件并进行 OCR 识别
        :param side: 身份证正反面
        :param request: 请求对象，用于获取 headers 中的 Authorization 信息
        :param file: 上传的文件对象
        :return: OCR 识别结果
        """
        file_content = await file.read()
        async with httpx.AsyncClient() as client:
            # 注意：
            # 1. 使用 await client.post (异步)
            # 2. 不要透传所有 headers，尤其是 Content-Type，httpx 会自动处理 multipart
            # 3. 如果需要鉴权 token，只取 Authorization 头
            headers = {}
            if "authorization" in request.headers:
                headers["authorization"] = request.headers["authorization"]

            files = {'file': (file.filename, file_content, file.content_type)}

            uploader_file_response = await client.post(
                'http://127.0.0.1:8000/api/v1/minio/upload?module=1',
                headers=headers,
                files=files
            )
            uploader_file_response = uploader_file_response.json()
            if not uploader_file_response.get('code') == 200:
                raise BusinessException(message="上传文件失败", code=400)

            baidu_access_key_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={settings.baidu_ocr_app_key}&client_secret={settings.baidu_ocr_secret_key}"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            baidu_access_token_response = requests.request("POST", baidu_access_key_url, headers=headers)

            baidu_access_token = baidu_access_token_response.json().get("access_token")
            if not baidu_access_token:
                raise BusinessException(message="百度 access_token 获取失败", code=400)

            request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/idcard"

            img = base64.b64encode(file_content)

            params = {"id_card_side": side, "image": img}
            request_url = request_url + "?access_token=" + baidu_access_token
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            response = requests.post(request_url, data=params, headers=headers)

            # idcard_number_type	是	int	用于校验身份证号码、性别、出生是否一致，输出结果及其对应关系如下：
            # -1： 身份证正面所有字段全为空
            # 0： 身份证证号不合法，此情况下不返回身份证证号
            # 1： 身份证证号和性别、出生信息一致
            # 2： 身份证证号和性别、出生信息都不一致
            # 3： 身份证证号和出生信息不一致
            # 4： 身份证证号和性别信息不一致
            response = response.json()
            if side == 'front':
                idcard_number_type = response.get('idcard_number_type')
                if not idcard_number_type:
                    raise BusinessException(message="身份证证号不合法", code=400)
                if idcard_number_type != 1:
                    raise BusinessException(message="身份证证号和性别、出生信息不一致", code=400)

            #  image_status	是	string
            # normal-识别正常
            # reversed_side-身份证正反面颠倒
            # non_idcard-上传的图片中不包含身份证
            # blurred-身份证模糊
            # other_type_card-其他类型证照
            # over_exposure-身份证关键字段反光或过曝
            # over_dark-身份证欠曝（亮度过低）
            # unknown-未知状态
            if not response.get('image_status'):
                raise BusinessException(message="身份证状态异常", code=400)
            if response.get('image_status') == 'reversed_side':
                raise BusinessException(message="身份证正反面颠倒", code=400)
            if response.get('image_status') == 'non_idcard':
                raise BusinessException(message="身份证正反面颠倒", code=400)
            if response.get('image_status') == 'blurred':
                raise BusinessException(message="身份证模糊", code=400)
            if response.get('image_status') == 'other_type_card':
                raise BusinessException(message="其他类型证照", code=400)
            if response.get('image_status') == 'over_exposure':
                raise BusinessException(message="身份证关键字段反光或过曝", code=400)
            if response.get('image_status') == 'over_dark':
                raise BusinessException(message="身份证欠曝（亮度过低）", code=400)
            if response.get('image_status') == 'unknown':
                raise BusinessException(message="未知错误", code=400)

            words_result = response.get('words_result')
            if side == 'front':
                name = words_result.get('姓名').get('words')
                id_card = words_result.get('公民身份号码').get('words')
                data = OCRVo(name=name, id_card=id_card, file_id=uploader_file_response.get('data').get('id'))
            else:
                data = OCRVo(file_id=uploader_file_response.get('data').get('id'), name='', id_card='')
            result = OCRResponse(
                code=200,
                message='成功',
                data=data
            )

        return result


user_service = UserService()
