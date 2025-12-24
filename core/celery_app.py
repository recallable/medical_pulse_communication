import os
import sys

# --- 核心修复代码 START ---
# 获取当前文件 (celery_app.py) 的绝对路径
current_file_path = os.path.abspath(__file__)
# 获取当前文件所在目录 (/project/core)
current_dir = os.path.dirname(current_file_path)
# 获取项目根目录 (/project) - 即上一级目录
project_root = os.path.dirname(current_dir)

# 将项目根目录添加到 Python 搜索路径的最前面
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- 核心修复代码 END ---

import time
import asyncio
from celery import Celery
from fastapi import UploadFile
from tortoise import Tortoise

celery_app = Celery(
    "medical_worker",  # 给 Worker 起个名字
    broker='amqp://admin:121518@localhost:5672//',
    backend='redis://127.0.0.1:6379/1',
)

# 2. 配置更新
celery_app.conf.update(
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_routes={
        'tasks.baidu_ocr_task': {'queue': 'baidu_ocr_queue'},
    },
    # 建议加上序列化配置
    task_serializer='pickle',
    result_serializer='pickle',
    accept_content=['pickle', 'json']
)


# --- 任务定义 (直接定义函数，去掉 staticmethod，去掉 class) ---
@celery_app.task(name='tasks.baidu_ocr_task', rate_limit='2/s')
def baidu_ocr_task(user_id: int, side: str, file: UploadFile):
    start_time = time.time()
    print(f"🚀 [Worker] 开始处理用户 {user_id} 的 OCR...")
    import sys
    # --- 调试代码 START ---
    print(f"当前 Python 搜索路径: {sys.path}")
    try:
        import models
        print("✅ 成功导入 models 模块！路径为:", models.__file__)
    except ImportError as e:
        print(f"❌ 无法导入 models 模块，原因: {e}")
        # 如果这里报错，说明 sys.path 还没配好，或者目录结构不对
        return {"error": f"Import models failed: {e}"}

    # --- 调试代码 END ---
    async def run_async_logic():
        # 1. 初始化数据库 (因为 Worker 是独立进程，FastAPI 的启动事件没管到这里)
        # 如果你的 user_service 不涉及查库/改库，可以把这步去掉
        from core.config import settings
        await Tortoise.init(config=settings.tortoise_config)

        try:
            from services.user import user_service
            # 2. 真正执行异步业务逻辑 (await)
            # 注意：确保 user_service.uploader_ocr 能接收 bytes
            res = await user_service.uploader_ocr(user_id, side, file)
            return res
        finally:
            # 3. 关闭数据库连接
            await Tortoise.close_connections()

    try:
        print(f"收到文件大小: {file.size} 字节")
        # 模拟业务逻辑
        # from services.user import user_service
        result = asyncio.run(run_async_logic())
        # time.sleep(0.5) # 模拟耗时
        # result = {"code": 200, "msg": "Success"}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}

    print(f"✅ [执行结束] 耗时: {time.time() - start_time:.4f}s")
    return result
