import base64

import httpx
from fastapi import UploadFile, Request

from core.config import settings
from middleware.exception import BusinessException
from models import File
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
                is_certified=user.identity
            )
        )

    async def uploader_ocr(self, request: Request, side: str, file: UploadFile) -> OCRResponse:
        """
        上传文件并进行 OCR 识别
        :param side: 身份证正反面 (front/back)
        :param request: 请求对象
        :param file: 上传的文件对象
        :return: OCR 识别结果
        """
        file_content = await file.read()

        # 1. 内部调用 MinIO 上传逻辑 (避免 HTTP 回环调用)
        # 获取当前用户ID (需要从 request.state 中获取，由中间件设置)
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            raise BusinessException(message="用户未登录", code=401)

        file_type = file.filename.split('.')[-1]

        # 导入 MinIO Service
        from services.minio_service import minio_service
        from models.schemas.file import FileUploadDTO

        # 构造 DTO
        dto = FileUploadDTO(module=1)  # 1 代表 OCR 模块

        try:
            # 直接调用 Service 方法
            file_vo = await minio_service.upload_file_and_record(
                dto=dto,
                user_id=user_id,
                source_file_type=file_type,
                source_file_size=len(file_content),
                source_file_name=file.filename,
                data=file_content
            )
        except Exception as e:
            raise BusinessException(message=f"文件上传失败: {str(e)}", code=400)

        # 2. 调用百度 OCR (全异步实现)
        async with httpx.AsyncClient() as client:
            # 2.1 获取 Access Token
            baidu_access_key_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={settings.baidu_ocr_app_key}&client_secret={settings.baidu_ocr_secret_key}"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            token_response = await client.post(baidu_access_key_url, headers=headers)
            token_data = token_response.json()
            baidu_access_token = token_data.get("access_token")

            if not baidu_access_token:
                raise BusinessException(message="百度 access_token 获取失败", code=400)

            # 2.2 调用身份证识别接口
            request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/idcard"
            img = base64.b64encode(file_content).decode('utf-8')  # 需要 decode 为 string

            params = {"id_card_side": side, "image": img}
            request_url = f"{request_url}?access_token={baidu_access_token}"
            headers = {'content-type': 'application/x-www-form-urlencoded'}

            ocr_response = await client.post(request_url, data=params, headers=headers)
            response_data = ocr_response.json()

            # 3. 处理 OCR 响应
            # 错误处理
            if response_data.get('error_code'):
                raise BusinessException(message=f"OCR识别错误: {response_data.get('error_msg')}", code=400)

            if side == 'front':
                # 身份证正面校验
                idcard_number_type = response_data.get('idcard_number_type')
                # -1: 身份证正面所有字段全为空
                # 0: 身份证证号不合法
                # 1: 身份证证号和性别、出生信息一致
                if idcard_number_type != 1:
                    msg_map = {
                        -1: "身份证正面所有字段全为空",
                        0: "身份证证号不合法",
                        2: "身份证证号和性别、出生信息都不一致",
                        3: "身份证证号和出生信息不一致",
                        4: "身份证证号和性别信息不一致"
                    }
                    raise BusinessException(message=msg_map.get(idcard_number_type, "身份证信息校验失败"), code=400)

            # 图像状态校验
            image_status = response_data.get('image_status')
            if image_status and image_status != 'normal':
                status_map = {
                    'reversed_side': "身份证正反面颠倒",
                    'non_idcard': "上传的图片中不包含身份证",
                    'blurred': "身份证模糊",
                    'other_type_card': "其他类型证照",
                    'over_exposure': "身份证关键字段反光或过曝",
                    'over_dark': "身份证欠曝（亮度过低）",
                    'unknown': "未知状态"
                }
                raise BusinessException(message=status_map.get(image_status, "身份证状态异常"), code=400)

            # 4. 构造返回数据
            words_result = response_data.get('words_result', {})
            user = await User.get_or_none(id=user_id)
            if side == 'front':
                name = words_result.get('姓名', {}).get('words', '')
                id_card = words_result.get('公民身份号码', {}).get('words', '')
                data = OCRVo(name=name, id_card=id_card, file_id=file_vo.id)
                user.id_card_front_id = file_vo.id
                user.identity_card = id_card
            else:
                # 反面识别结果处理 (通常包含签发机关、有效期限等，目前 VO只定义了 name/id_card)
                # 根据需求，反面可能不需要 name/id_card，这里留空
                data = OCRVo(name='', id_card='', file_id=file_vo.id)
                user.id_card_back_id = file_vo.id
            await user.save()

            return OCRResponse(
                code=200,
                message='成功',
                data=data
            )

    async def certification(self, user_id: int):
        """
        用户认证接口
        """
        user = await User.get_or_none(id=user_id)
        if not user:
            raise BusinessException(message="用户不存在", code=404)
        if user.identity:
            raise BusinessException(message="用户已认证", code=400)
        front_file = await File.get_or_none(id=user.id_card_front_id)
        if not front_file:
            raise BusinessException(message="正面文件不存在", code=404)
        back_file = await File.get_or_none(id=user.id_card_back_id)
        if not back_file:
            raise BusinessException(message="反面文件不存在", code=404)
        user.identity = True
        await user.save()
        # async with httpx.AsyncClient() as client:
        #     # host = f'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={settings.baidu_ocr_app_key}&client_secret={settings.baidu_ocr_secret_key}'
        #     host = f'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=I7pQrwb08r1JLTAhIJ8VnHV2&client_secret=iWC7yz12tQgKh2aEZLBIlabxZPlHV56X'
        #     headers = {
        #         'Content-Type': 'application/json',
        #         'Accept': 'application/json'
        #     }
        #
        #     token_response = await client.post(host, headers=headers)
        #     token_data = token_response.json()
        #     baidu_access_token = token_data.get("access_token")
        #     if not baidu_access_token:
        #         raise BusinessException(message="百度 access_token 获取失败", code=400)
        #
        #     idmatch_url = f'https://aip.baidubce.com/rest/2.0/face/v3/person/idmatch?access_token={baidu_access_token}'
        #     response = await client.post(idmatch_url, headers=headers, json={
        #         'id_card_number': user.identity_card,
        #         'name':  user.username,
        #     })
        #     response =  response.json()
        #     print(response)

        return UserInfo(id=user.id, username=user.username, phone=user.phone, is_active=user.user_status)


user_service = UserService()
