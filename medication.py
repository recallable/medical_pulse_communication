import csv
import os
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class MedliveSpider:
    def __init__(self, cookie_str):
        self.session = requests.Session()
        self.base_url = 'https://drugs.medlive.cn'
        self.index_url = "https://drugs.medlive.cn/v2/drugref/drugTree/index"

        # --- 新增：定义记录进度的文件路径 ---
        self.history_file = "crawled_urls.txt"
        # --- 新增：启动时加载已爬取的 URL 集合 ---
        self.crawled_set = self._load_history()

        # Cookie 和 Header 设置保持不变
        cookies = {}
        for item in cookie_str.split(';'):
            item = item.strip()
            if '=' in item:
                k, v = item.split('=', 1)
                cookies[k] = v

        self.session.cookies.update(cookies)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://drugs.medlive.cn/'
        })

        self.one_drug_data = []
        self.two_drug_data = []
        self.three_drug_data = []
        self.detail_data = []

    # ==========================================
    # 核心修改 1: 加载历史记录
    # ==========================================
    def _load_history(self):
        """启动时读取 txt 文件，返回已爬取的 URL 集合"""
        crawled = set()
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r', encoding='utf-8') as f:
                for line in f:
                    crawled.add(line.strip())
            print(f"📖 [断点续传] 已加载 {len(crawled)} 条历史记录，将跳过这些页面。")
        else:
            print("📖 [断点续传] 未发现历史记录，将从头开始。")
        return crawled

    # ==========================================
    # 核心修改 2: 记录历史记录
    # ==========================================
    def _record_history(self, url_list):
        """将成功保存的 URL 写入 txt 文件"""
        try:
            with open(self.history_file, 'a', encoding='utf-8') as f:
                for url in url_list:
                    f.write(url + '\n')
                    self.crawled_set.add(url)  # 同时更新内存中的集合
        except Exception as e:
            print(f"⚠️ 记录进度失败: {e}")

    def save_to_csv(self, data_batch, filename="medlive_drugs.csv"):
        """分批将数据写入 CSV 文件，并记录进度"""
        if not data_batch:
            return

        headers = [
            '大类', '药物类别', '通用名', '来源链接',
            '成分', '性状', '适应症', '规格', '用法用量',
            '不良反应', '禁忌', '注意事项',
            '孕妇及哺乳期妇女用药', '儿童用药', '老年用药',
            '药物相互作用', '药物过量', '药理毒理', '药代动力学',
            '贮藏', '包装', '有效期', '执行标准', '批准文号', '生产企业'
        ]

        file_exists = os.path.isfile(filename)

        try:
            with open(filename, mode='a', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
                if not file_exists:
                    writer.writeheader()
                writer.writerows(data_batch)
                print(f"   💾 [系统] 已自动保存 {len(data_batch)} 条数据到 CSV")

            # ==========================================
            # 核心修改 3: CSV 写入成功后，立即记录进度
            # ==========================================
            saved_urls = [item['来源链接'] for item in data_batch]
            self._record_history(saved_urls)

        except Exception as e:
            print(f"❌ 保存 CSV 出错: {e}")

    def get_directory(self):
        """步骤一：获取目录页"""
        # ... (保持原代码不变) ...
        print(f"[-] 正在获取目录: {self.index_url}")
        try:
            resp = self.session.get(self.index_url)
            if resp.status_code != 200: return
            soup = BeautifulSoup(resp.text, 'html.parser')
            drug_titles = soup.find_all('div', class_='drug_title')
            for title in drug_titles:
                cate_name = title.get_text(strip=True)
                table = title.find_next_sibling('table')
                if not table: continue
                a_tags = table.find_all('a', href=True)
                for a in a_tags:
                    drug_name = a.get_text(strip=True)
                    href = a['href'].strip()
                    if not drug_name or href == '#': continue
                    self.one_drug_data.append({
                        '大类': cate_name,
                        '药物类别': drug_name,
                        '链接': urljoin(self.base_url, href)
                    })
            print(f"[-] 已解析 {len(self.one_drug_data)} 条分类数据")
        except Exception as e:
            print(f"❌ 解析目录出错: {e}")

    def get_two_directory(self):
        """步骤二：访问二级分类"""
        # ... (保持原代码不变) ...
        if not self.one_drug_data: return
        print("\n[-] 开始获取二级列表...")
        for item in self.one_drug_data:  # 全量跑
            target_url = item['链接']
            try:
                time.sleep(5)
                resp = self.session.get(target_url)
                soup = BeautifulSoup(resp.text, 'html.parser')
                drug_titles = soup.find_all('div', class_='drug_title')
                for title in drug_titles:
                    cate_name = title.get_text(strip=True)
                    table = title.find_next_sibling('div', class_='drug_list')
                    if not table: continue
                    a_tags = table.find_all('a', href=True)
                    for a in a_tags:
                        self.two_drug_data.append({
                            '大类': cate_name,
                            '药物类别': a.get_text(strip=True),
                            '链接': a['href'].strip(),
                            '标题': a.get('title')
                        })
            except Exception as e:
                print(f"❌ 请求出错: {e}")

    def get_three_directory(self):
        """步骤三：访问三级分类"""
        # ... (保持原代码不变) ...
        if not self.two_drug_data: return
        print("\n[-] 开始获取三级列表...")
        for item in self.two_drug_data:
            target_url = urljoin(self.base_url, item['链接'])
            try:
                time.sleep(5)
                resp = self.session.get(target_url)
                soup = BeautifulSoup(resp.text, 'html.parser')
                box_list = soup.find_all('div', class_='box1')
                for box in box_list:
                    sub_box = box.find('div', class_='medince-name')
                    if sub_box and sub_box.find('a'):
                        a = sub_box.find('a')
                        self.three_drug_data.append({
                            '大类': item.get('大类'),
                            '药物类别': item.get('药物类别'),
                            '链接': urljoin(self.base_url, a['href']),
                            '标题': a.get_text(strip=True)
                        })
            except Exception as e:
                print(f"❌ 访问出错: {e}")
        print(f"[-] 三级列表获取完成，共 {len(self.three_drug_data)} 条")

    def get_detail(self):
        """步骤四：通用详情页解析（含断点续传）"""
        if not self.three_drug_data:
            print("[-] 没有数据可抓取")
            return

        total_count = len(self.three_drug_data)
        print(f"\n[-] 准备抓取详情页，任务队列总数: {total_count}")

        batch_buffer = []
        BATCH_SIZE = 5

        # 统计跳过数量
        skip_count = 0

        for i, item in enumerate(self.three_drug_data):
            target_url = item['链接']

            # ==========================================
            # 核心修改 4: 检查是否已爬取
            # ==========================================
            if target_url in self.crawled_set:
                skip_count += 1
                # 每跳过 100 个打印一次日志，避免刷屏
                if skip_count % 100 == 0:
                    print(f"⏩ 已跳过 {skip_count} 条已存在的记录...")
                continue

            # 打印当前进度
            print(f"[-] [{i + 1}/{total_count}] 正在请求: {item['标题']}")

            try:
                time.sleep(5)
                resp = self.session.get(target_url)

                if "auth/login" in resp.url or "会员登录" in resp.text:
                    print(f"❌ 失败: Cookie 失效")
                    self.save_to_csv(batch_buffer)  # 退出前保存已有数据
                    break

                soup = BeautifulSoup(resp.text, 'html.parser')

                one_drug_record = {
                    '大类': item.get('大类', ''),
                    '药物类别': item.get('药物类别', ''),
                    '通用名': item.get('标题', ''),
                    '来源链接': target_url
                }

                title_divs = soup.find_all('div', class_='inner_title clearfix')
                for title_div in title_divs:
                    key = title_div.get_text(strip=True)
                    content_parts = []
                    curr = title_div.next_sibling
                    while curr:
                        if curr.name == 'div' and 'inner_title' in curr.get('class', []):
                            break
                        if curr.name:
                            text = curr.get_text(separator='\n', strip=True)
                            if text: content_parts.append(text)
                        curr = curr.next_sibling

                    full_content = "\n".join(content_parts)
                    if full_content:
                        one_drug_record[key] = full_content

                batch_buffer.append(one_drug_record)
                print(f"   ✅ 解析成功")

                if len(batch_buffer) >= BATCH_SIZE:
                    # save_to_csv 内部会自动记录这些 URL 到 crawled_urls.txt
                    self.save_to_csv(batch_buffer)
                    batch_buffer = []

            except Exception as e:
                print(f"❌ 访问出错: {e}")

        # 最后保存剩余的数据
        if batch_buffer:
            self.save_to_csv(batch_buffer)

        print(f"\n[+] 所有工作完成！共跳过 {skip_count} 条历史数据。")


# --- 主程序入口 ---
if __name__ == "__main__":
    # 请填入最新的 Cookie
    MY_COOKIE = 'ymt_pk_id=e58e7dbb8311834e; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219b43bbe9cf9a6-0f28744e6157dc8-26061a51-2073600-19b43bbe9d012a2%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTliNDNiYmU5Y2Y5YTYtMGYyODc0NGU2MTU3ZGM4LTI2MDYxYTUxLTIwNzM2MDAtMTliNDNiYmU5ZDAxMmEyIn0%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219b43bbe9cf9a6-0f28744e6157dc8-26061a51-2073600-19b43bbe9d012a2%22%7D; Hm_lvt_62d92d99f7c1e7a31a11759de376479f=1766651114,1766658742; ymtinfo=eyJ1aWQiOiI2ODk4NDUwIiwicmVzb3VyY2UiOiIiLCJleHRfdmVyc2lvbiI6IjEiLCJhcHBfbmFtZSI6IiJ9; _pk_ref.3.a971=%5B%22%22%2C%22%22%2C1766716943%2C%22https%3A%2F%2Fwww.google.com%2F%22%5D; _pk_ses.3.a971=*; JSESSIONID=8296E6EFB4F50E7FB063166CEA85D8C3; _pk_id.3.a971=e58e7dbb8311834e.1766318358.9.1766716975.1766667254.'

    bot = MedliveSpider(MY_COOKIE)

    # 爬取流程
    # 注意：前三个步骤还是需要运行的，因为我们需要生成任务列表
    # 但是因为有了断点续传，即使任务列表生成了，get_detail 也会飞快地跳过已经做过的
    bot.get_directory()
    bot.get_two_directory()
    bot.get_three_directory()

    # 这里开始才是真正的耗时操作，会支持断点续传
    bot.get_detail()