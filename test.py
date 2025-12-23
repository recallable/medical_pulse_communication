import json
import os
import time
from datetime import datetime

import psycopg2
import requests
from psycopg2 import extras

# --- 配置区 ---
STATE_FILE = "spider_checkpoint.json"  # 用于存储进度的文件
BATCH_SIZE = 1000  # 多少条存一次库

# --- 数据库连接 ---
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="postgres",
    user="postgres",
    password="121518"
)
conn.autocommit = False
cursor = conn.cursor()


# --- 辅助函数：读取和保存进度 ---
def load_checkpoint():
    """读取上次爬到的页码"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                last_page = state.get('page', 1)
                last_id = state.get('last_id', 'None')
                print(f"📖 发现进度存档：上次爬到了第 {last_page} 页 (最后ID: {last_id})")
                return last_page + 1  # 从下一页开始
        except Exception:
            print("⚠️ 存档文件损坏，重新开始...")
    return 1


def save_checkpoint(page, last_content_id):
    """保存当前页码和ID到文件"""
    with open(STATE_FILE, 'w') as f:
        json.dump({
            'page': page,
            'last_id': last_content_id,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }, f)


# --- 主程序 ---

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'cookie': 'ymt_pk_id=e58e7dbb8311834e; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219b43bbe9cf9a6-0f28744e6157dc8-26061a51-2073600-19b43bbe9d012a2%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTliNDNiYmU5Y2Y5YTYtMGYyODc0NGU2MTU3ZGM4LTI2MDYxYTUxLTIwNzM2MDAtMTliNDNiYmU5ZDAxMmEyIn0%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219b43bbe9cf9a6-0f28744e6157dc8-26061a51-2073600-19b43bbe9d012a2%22%7D; ymtinfo=eyJ1aWQiOiI2ODk4NDUwIiwicmVzb3VyY2UiOiIiLCJleHRfdmVyc2lvbiI6IjEiLCJhcHBfbmFtZSI6IiJ9; PHPSESSID=6132694637cc59f3a797deacf26f6ffbfe2ba1d94d1535d813143fe6b36317da; _pk_ref.3.a971=%5B%22%22%2C%22%22%2C1766456346%2C%22https%3A%2F%2Fwww.google.com%2F%22%5D; _pk_ses.3.a971=*; _pk_id.3.a971=e58e7dbb8311834e.1766318358.4.1766459173.1766370834.; XSRF-TOKEN=eyJpdiI6IlhNN01vMkZvNUpFQWNyOTBkZ3g4NXc9PSIsInZhbHVlIjoiSFYrSWpSblNVb3N1RWZ3SkM4VmRjVncvdnRhNWtDSGZ3djhNdCtoR3BMRUIvRStFclFRclJmdWNYdDRyR0I2MW9DZmRSZWFnRzVhdVhnZXRFSlozazJzRXhoRkFxa05xckw5TUFkeXpLd1Ztc0F1V2lPaWpsV2xwQ2xJRzZCZVQiLCJtYWMiOiI3YmRhMTIxOWViZDcyODZhNDIyMDMwYTY0ZGQ5NTZiMWE4OTlmYzcxYzZlOWU4Y2YxZWE2ZjllYmY3YjUyNmRjIn0%3D; web_www_session=eyJpdiI6IitrUVRGN1oydTN5alFaVFk2b3d0RFE9PSIsInZhbHVlIjoicFIyL1o2cXhiZmg4TFNGZnRnRGRWRGYzVWs2MnpVOVk0MGdIcEZFZmVkUndyT0RXS0VXcVdiRGpVR3VOTzA4aWVacVVKNjFyR3VzdEhteTM2SExibjIzL3hoZmZXN0taS2JOUVRqYTNnKy9XRkE1Um5NMDNDQmFCUmRjcjJHTzUiLCJtYWMiOiJjNTdkMDY5ZDgxMmViNDNjY2I3ZjllNDZkODg0NzRhNDdlYTljNzVlNzNmNDQzYzUxYjM0NTdhMmYxYWJkMjkxIn0%3D',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
}

# 1. 恢复进度
start_page = load_checkpoint()
page = start_page
data_buffer: list = []

print(f"🚀 开始爬取，从第 {page} 页开始...")

try:
    while True:
        try:
            # 发送请求
            response = requests.post('https://www.medlive.cn/new/articlelist', data={
                'branch': 0,
                'page': page,
                'size': 10,
                '_token': 'CcNkkST8nqdZljLhxoqrWFgFjgvUjlDxCgrgT4fA'
            }, headers=headers, timeout=10)

            res_json = response.json()
            current_data = res_json.get('data').get('data')
            # 【诊断步骤 1】如果当前页数据不是列表，打印出来看看是什么鬼
            if not isinstance(current_data, list):
                print(f"⚠️ 异常！第 {page} 页返回的数据不是列表，可能是被封了。")
                print(f"👉 服务器返回内容: {res_json}")
                # 这里可以选择 break 停止，或者 time.sleep(60) 暂停一会
                break

                # 如果是空列表，说明爬完了
            if not current_data:
                print(f"🏁 第 {page} 页无数据，爬取结束。")
                break

            # 打印进度条效果
            print(f"-> 正在处理第 {page} 页 (当前缓冲池: {len(data_buffer)}/{BATCH_SIZE})")

            # 加入缓冲池
            for datum in current_data:
                raw_time = datum.get('inputtime')  # 获取原始时间戳，例如 1766397600
                final_time = None

                if raw_time:
                    try:
                        # 1. 先转成 int (防止有时候接口给的是字符串 '1766...')
                        # 2. 再转成 datetime 对象
                        final_time = datetime.fromtimestamp(int(raw_time))
                    except Exception:
                        # 如果转换失败（比如数据为空），就保持 None
                        final_time = None
                # -----------------------
                row = (
                    # datum.get('contentid'),
                    datum.get('title'),
                    datum.get('url'),
                    datum.get('thumb'),
                    datum.get('description'),
                    datum.get('type'),
                    final_time,
                    datum.get('comment_count'),
                    # datum.get('format_time'),
                    datum.get('content')
                )
                data_buffer.append(row)

            # --- 触发批量写入条件 ---
            if len(data_buffer) >= BATCH_SIZE:
                print(f"💾 缓冲池已满，正在写入数据库...")

                insert_sql = """
                             INSERT INTO medical_pulse_communication.article
                             (title, url, thumb, description, type, input_time, comment_count, content)
                             VALUES %s; \
                             """

                extras.execute_values(cursor, insert_sql, data_buffer, page_size=BATCH_SIZE)
                conn.commit()

                # 【关键】写入成功后，立即保存进度
                # 我们记录的是当前这批数据里最后一个数据的ID，以及当前页码
                last_item_id = data_buffer[-1][0]
                save_checkpoint(page, last_item_id)

                print(f"✅ 写入成功！进度已保存：第 {page} 页")
                data_buffer.clear()

            page += 1
            time.sleep(0.5)  # 稍微快一点，0.5秒

        except Exception as e:
            print(f"❌ 第 {page} 页出错: {e}")
            time.sleep(5)  # 出错多睡一会

    # --- 循环结束后，处理剩余数据 ---
    if data_buffer:
        print(f"🧹 正在写入剩余的 {len(data_buffer)} 条数据...")
        insert_sql = "INSERT INTO medical_pulse_communication.article (title,url,thumb,description,type,input_time,comment_count,content) VALUES %s;"
        extras.execute_values(cursor, insert_sql, data_buffer)
        conn.commit()
        save_checkpoint(page, "End")
        print("✅ 全部完成！")

finally:
    if cursor: cursor.close()
    if conn: conn.close()
