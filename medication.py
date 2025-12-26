import random
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class MedliveSpider:
    def __init__(self, cookie_str):
        self.session = requests.Session()
        self.base_url = 'https://drugs.medlive.cn'
        self.index_url = "https://drugs.medlive.cn/v2/drugref/drugTree/index"

        # 1. 解析你提供的 Cookie 字符串为字典
        cookies = {}
        for item in cookie_str.split(';'):
            item = item.strip()
            if '=' in item:
                k, v = item.split('=', 1)
                cookies[k] = v

        # 2. 将 Cookie 设置到 Session 中
        self.session.cookies.update(cookies)

        # 3. 设置能够通过校验的 Headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            # 初始 Referer 设置为首页
            'Referer': 'https://drugs.medlive.cn/'
        })

        self.one_drug_data = []
        self.two_drug_data = []
        self.three_drug_data = []
        self.detail_data = []

    def get_directory(self):
        """步骤一：获取目录页"""
        print(f"[-] 正在获取目录: {self.index_url}")
        try:
            resp = self.session.get(self.index_url)
            if resp.status_code != 200:
                print(f"❌ 目录请求失败: {resp.status_code}")
                return

            soup = BeautifulSoup(resp.text, 'html.parser')

            # 简单验证一下登录状态 (虽然目录页公开，但头部会有用户信息)
            if "退出" in resp.text or "user-center" in resp.text:
                print("✅ Cookie 有效，检测到登录状态")
            else:
                print("⚠️  警告：页面未显示登录状态（可能Cookie过期或目录页本身缓存），尝试继续抓取...")

            drug_titles = soup.find_all('div', class_='drug_title')

            for title in drug_titles:
                cate_name = title.get_text(strip=True)  # 如：西药
                table = title.find_next_sibling('table')
                if not table: continue

                a_tags = table.find_all('a', href=True)
                for a in a_tags:
                    drug_name = a.get_text(strip=True)  # 如：消化道及代谢类药物
                    href = a['href'].strip()

                    if not drug_name or href == '#': continue

                    # 补全 URL
                    full_link = urljoin(self.base_url, href)

                    self.one_drug_data.append({
                        '大类': cate_name,
                        '药物类别': drug_name,
                        '链接': full_link
                    })

            print(f"[-] 已解析 {len(self.one_drug_data)} 条分类数据")

        except Exception as e:
            print(f"❌ 解析目录出错: {e}")

    def get_two_directory(self):
        """步骤二：访问二级分类"""
        if not self.one_drug_data:
            print("[-] 没有数据可抓取")
            return

        print("\n[-] 开始尝试访问详情页 (取前 3 条测试)...")

        # 为了演示，只抓取前 1 个，避免刷屏
        for item in self.one_drug_data[:1]:
            target_url = item['链接']
            print(f"[-]正在请求: {item['药物类别']} -> {target_url}")

            # 【关键】每次请求前，更新 Referer 为目录页
            # 告诉服务器：我是从目录页点进来的
            headers = {
                'Referer': self.index_url
            }

            try:
                # 随机休眠，防止请求过快被封
                time.sleep(random.uniform(1, 2))

                resp = self.session.get(target_url, headers=headers)

                # 检查是否被重定向回登录页
                if "auth/login" in resp.url or "会员登录" in resp.text:
                    print(f"❌ 失败: Cookie 失效或被拦截，跳转回了登录页")
                    break  # 如果失效了，后面的通常也会失效，直接退出

                soup = BeautifulSoup(resp.text, 'html.parser')
                drug_titles = soup.find_all('div', class_='drug_title')
                for title in drug_titles:
                    cate_name = title.get_text(strip=True)  # 如：口腔病药物
                    table = title.find_next_sibling('div', class_='drug_list')
                    a_tags = table.find_all('a', href=True)
                    for a in a_tags:
                        drug_name = a.get_text(strip=True)
                        href = a['href'].strip()
                        title = a.get('title')
                        if not drug_name or href == '#':
                            continue
                        self.two_drug_data.append({
                            '大类': cate_name,
                            '药物类别': drug_name,
                            '链接': href,
                            '标题': title
                        })
                    if not table:
                        continue

            except Exception as e:
                print(f"❌ 请求出错: {e}")

    def get_three_directory(self):
        """步骤三：访问三级分类"""
        if not self.two_drug_data:
            print("[-] 没有数据可抓取")
            return

        print("\n[-] 尝试访问详情页 (取前 3 条测试)...")

        # 遍历上一级抓取到的数据
        for item in self.two_drug_data[:1]:  # 测试时只取1个
            target_url = self.base_url + item['链接']
            print(f"[-]正在请求: {item['药物类别']} -> {target_url}")

            try:
                # 随机休眠
                time.sleep(random.uniform(1, 2))

                # 发送请求
                resp = self.session.get(target_url)  # target_url 已经是完整链接了(假设上一级处理过)
                # 如果不是，请用 urljoin(self.base_url, target_url)

                # 检查是否被重定向回登录页
                if "auth/login" in resp.url or "会员登录" in resp.text:
                    print(f"❌ 失败: Cookie 失效或被拦截，跳转回了登录页")
                    break

                soup = BeautifulSoup(resp.text, 'html.parser')

                # 1. 找到所有药物的容器 (class="box1")
                # 注意：这里修正了 class_ 写法
                box_list = soup.find_all('div', class_='box1')

                if not box_list:
                    print("   [-] 未找到药物列表")
                    continue

                print(f"   [-] 本页找到 {len(box_list)} 个药物")

                for box in box_list:
                    # 2. 【关键修正】使用 find 在 box 内部查找
                    sub_box = box.find('div', class_='medince-name')
                    if not sub_box:
                        print("未找到medince-name")
                        continue
                    a_tag = sub_box.find('a')

                    if not a_tag:
                        print("未找到a标签")
                        continue

                    href = a_tag.get('href', '').strip()
                    text = a_tag.get_text(strip=True)

                    # 拼接完整链接
                    full_link = urljoin(self.base_url, href)
                    # print(f"   [-] 当前页:{page} 获取链接: {text} -> {full_link}")
                    self.three_drug_data.append({
                        '大类': item.get('大类', '未知'),
                        '药物类别': item.get('药物类别', '未知'),
                        '链接': full_link,
                        '标题': text
                    })
            except Exception as e:
                print(f"❌ 访问出错: {e}")

    def get_detail(self):
        """步骤四：访问详情页"""
        if not self.three_drug_data:
            print("[-] 没有数据可抓取")
            return

        print("\n[-] 尝试访问详情页 (取前 3 条测试)...")
        # 遍历上一级抓取到的数据
        for item in self.three_drug_data[:3]:  # 测试时只取3个
            target_url = item['链接']
            print(f"[-]正在请求: {item['药物类别']} -> {target_url}")
            try:
                # 随机休眠
                time.sleep(random.uniform(1, 2))
                # 发送请求
                resp = self.session.get(target_url)  # target_url 已经是完整链接了(假设上一级处理过)
                # 如果不是，请用 urljoin(self.base_url, target_url)
                # 检查是否被重定向回登录页
                if "auth/login" in resp.url or "会员登录" in resp.text:
                    print(f"❌ 失败: Cookie 失效或被拦截，跳转回了登录页")
                    break
                # 解析 HTML
                soup = BeautifulSoup(resp.text, 'html.parser')
                # 提取详情信息
                detail_box = soup.find('div', class_='detail-box')
                if not detail_box:
                    print("未找到详情信息")
                    continue
                # 提取所有段落
                paragraphs = detail_box.find_all('p')
                for p in paragraphs:
                    print(p.get_text(strip=True))
                    self.detail_data.append({
                        '大类': item.get('大类', '未知'),
                        '药物类别': item.get('药物类别', '未知'),
                        '标题': item.get('标题', '未知'),
                        '详情': p.get_text(strip=True)
                    })
                    # save_to_json(self.detail_data)

            except Exception as e:
                print(f"❌ 访问出错: {e}")
                

# --- 主程序入口 ---
if __name__ == "__main__":
    # 这里填入你之前代码里提取到的真实 Cookie
    MY_COOKIE = 'ymt_pk_id=e58e7dbb8311834e; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219b43bbe9cf9a6-0f28744e6157dc8-26061a51-2073600-19b43bbe9d012a2%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTliNDNiYmU5Y2Y5YTYtMGYyODc0NGU2MTU3ZGM4LTI2MDYxYTUxLTIwNzM2MDAtMTliNDNiYmU5ZDAxMmEyIn0%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219b43bbe9cf9a6-0f28744e6157dc8-26061a51-2073600-19b43bbe9d012a2%22%7D; JSESSIONID=9B74979BB1C194E051708D34830319F3; ymtinfo=eyJ1aWQiOiI2ODk4NDUwIiwicmVzb3VyY2UiOiIiLCJleHRfdmVyc2lvbiI6IjEiLCJhcHBfbmFtZSI6IiJ9; Hm_lvt_62d92d99f7c1e7a31a11759de376479f=1766651114,1766658742; HMACCOUNT=AD37163F391F5FB4; _pk_ref.3.a971=%5B%22%22%2C%22%22%2C1766658742%2C%22https%3A%2F%2Fwww.google.com%2F%22%5D; _pk_ses.3.a971=*; Hm_lpvt_62d92d99f7c1e7a31a11759de376479f=1766658743; _pk_id.3.a971=e58e7dbb8311834e.1766318358.7.1766660569.1766654398.'

    bot = MedliveSpider(MY_COOKIE)

    # 1. 获取目录
    bot.get_directory()

    # 2. 获取二级分类
    bot.get_two_directory()

    # 3. 获取三级分类
    bot.get_three_directory()

    bot.get_detail()
    for detail in bot.detail_data:
        print(detail)
