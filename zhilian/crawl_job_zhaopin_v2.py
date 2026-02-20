# 智联招聘岗位爬虫 V2
# 改进版：使用搜索框输入关键词，支持任意关键词（包括中文公司名等）
import json
import os
import random
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def get_UA():
    """获取随机 User-Agent（macOS Chrome）"""
    UA_list = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    ]
    return random.choice(UA_list)


def init_driver(headless: bool = False, use_existing: bool = False, debug_port: int = 9222) -> webdriver.Chrome:
    """初始化浏览器驱动

    Args:
        headless: 是否使用无头模式，默认 False（显示浏览器窗口更不容易被检测）
        use_existing: 是否使用已打开的浏览器，默认 False
        debug_port: 远程调试端口，默认 9222

    Returns:
        webdriver.Chrome: Chrome 浏览器驱动实例
    """
    options = Options()

    if use_existing:
        # 连接到已有的 Chrome 浏览器
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
        print(f"🔗 连接到已有浏览器（端口：{debug_port}）")
    else:
        # 🛡️ 反爬虫对策 - 隐藏自动化特征
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        # 可选：无头模式（建议关闭以避免被检测）
        if headless:
            options.add_argument('--headless=new')

        # 基础配置
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')  # 重要：隐藏自动化标识
        options.add_argument('--disable-gpu')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-notifications')

        # 使用真实的用户代理
        ua = get_UA()
        options.add_argument(f'user-agent={ua}')

        # 窗口配置
        options.add_argument('--start-maximized')
        options.add_argument('--window-size=1920,1080')

    # 创建 Chrome driver
    driver = webdriver.Chrome(options=options)

    if not use_existing:
        # 执行 CDP 命令隐藏 webdriver 属性（仅在新浏览器时）
        try:
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                '''
            })
        except:
            pass

    return driver


def save_cookies_to_file(driver, filepath: str = "zhaopin_cookies.json"):
    """保存当前浏览器的 Cookie 到文件

    Args:
        driver: 浏览器驱动
        filepath: Cookie 保存路径
    """
    cookies = driver.get_cookies()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump({"cookies": cookies}, f, indent=2, ensure_ascii=False)
    print(f"✅ Cookie 已保存到 {filepath}")


def load_cookies_from_file(driver, filepath: str = "zhaopin_cookies.json") -> bool:
    """从文件加载 Cookie 到浏览器

    Args:
        driver: 浏览器驱动
        filepath: Cookie 文件路径

    Returns:
        bool: 是否成功加载
    """
    if not os.path.exists(filepath):
        print(f"⚠️  Cookie 文件不存在: {filepath}")
        return False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            cookies = data.get("cookies", [])

        if not cookies:
            print("⚠️  Cookie 文件为空")
            return False

        # 先访问网站首页，建立域
        driver.get("https://www.zhaopin.com/")
        time.sleep(1)

        # 添加所有 Cookie
        for cookie in cookies:
            try:
                # 移除可能导致问题的字段
                cookie.pop('sameSite', None)
                cookie.pop('expiry', None)
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"⚠️  添加 Cookie 失败: {cookie.get('name', 'unknown')} - {e}")
                continue

        print(f"✅ 成功加载 {len(cookies)} 个 Cookie")
        driver.refresh()
        time.sleep(2)
        return True
    except Exception as e:
        print(f"❌ 加载 Cookie 失败: {e}")
        return False


def get_city_code(city_name: str) -> str:
    """获取智联招聘城市代码

    Args:
        city_name: 城市名称

    Returns:
        str: 城市代码
    """
    city_map = {
        "北京": "530",
        "上海": "538",
        "深圳": "765",
        "广州": "763",
        "杭州": "653",
        "成都": "801",
        "南京": "635",
        "武汉": "736",
        "西安": "854",
        "全国": ""
    }
    return city_map.get(city_name, "530")


def listjob_by_keyword(keyword: str, city: str = "北京", limit: int = None, use_existing_browser: bool = False, use_cookies: bool = False) -> str:
    """根据关键词爬取智联招聘岗位信息

    Args:
        keyword: 搜索关键词（可以是职位名、公司名等任意关键词）
        city: 城市名称
        limit: 限制爬取数量，None 表示爬取第一页所有岗位
        use_existing_browser: 是否使用已打开的浏览器
        use_cookies: 是否使用 Cookie 自动登录

    Returns:
        str: 格式化的岗位信息字符串
    """
    print("🚀 开始初始化浏览器...")
    driver = init_driver(headless=False, use_existing=use_existing_browser)

    if driver is None:
        raise Exception("❌ 创建浏览器失败")
    print("✅ 浏览器创建成功\n")

    try:
        # Step 1: 加载 Cookie（如果启用）
        if use_cookies:
            print("🔑 正在加载 Cookie...")
            cookie_loaded = load_cookies_from_file(driver)
            if not cookie_loaded:
                print("⚠️  Cookie 加载失败，将以访客模式继续")
        else:
            # 不使用 Cookie，先访问首页建立会话
            print("📍 正在访问智联招聘首页...")
            driver.get("https://www.zhaopin.com/")
            time.sleep(2)

        # Step 2: 访问智联招聘并使用搜索框
        city_code = get_city_code(city)
        print(f"📍 正在访问职位搜索页...")
        print(f"   城市: {city} (代码: {city_code})")
        print(f"   关键词: {keyword}")

        # 访问智联招聘首页
        print("🔍 正在访问智联招聘首页...")
        driver.get("https://www.zhaopin.com/")
        time.sleep(3)

        # 使用首页搜索框输入关键词
        print(f"🔍 正在搜索框输入关键词: {keyword}...")
        try:
            # 查找搜索输入框（智联招聘首页的搜索框选择器）
            search_selectors = [
                "#search-input-1",  # 首页主搜索框ID
                "input[placeholder*='请输入职位']",
                "input[placeholder*='搜索职位']",
                "input.search__input",
                ".search-box input[type='text']",
                "input.search-input"
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if search_input and search_input.is_displayed():
                        print(f"   ✓ 找到搜索框: {selector}")
                        break
                except:
                    continue

            if search_input:
                # 清空并输入关键词
                search_input.clear()
                search_input.send_keys(keyword)
                print(f"   ✓ 已输入关键词: {keyword}")
                time.sleep(1)

                # 查找并点击搜索按钮
                search_btn_selectors = [
                    "button.search__btn",  # 首页搜索按钮
                    ".search-box button",
                    "button[type='submit']",
                    ".search-btn",
                    "button.btn-search"
                ]

                search_btn = None
                for btn_selector in search_btn_selectors:
                    try:
                        search_btn = driver.find_element(By.CSS_SELECTOR, btn_selector)
                        if search_btn and search_btn.is_displayed():
                            print(f"   ✓ 找到搜索按钮: {btn_selector}")
                            search_btn.click()
                            print("✅ 已提交搜索")
                            break
                    except:
                        continue

                if not search_btn:
                    # 如果没有找到按钮，尝试按回车键提交
                    print("   ⚠️  未找到搜索按钮，尝试按Enter键提交...")
                    from selenium.webdriver.common.keys import Keys
                    search_input.send_keys(Keys.RETURN)
                    print("✅ 已按Enter键提交搜索")

                time.sleep(5)  # 等待搜索结果加载
            else:
                # 如果找不到搜索框，尝试直接构造 URL（使用 URL 编码）
                print("⚠️  未找到搜索框，尝试直接访问搜索结果页...")
                from urllib.parse import quote
                encoded_keyword = quote(keyword)
                url = f"https://www.zhaopin.com/sou/jl{city_code}/kw{encoded_keyword}"
                print(f"   URL: {url}")
                driver.get(url)
                time.sleep(4)

        except Exception as e:
            print(f"⚠️  搜索过程出错: {e}")
            print("   尝试直接访问搜索结果页...")
            from urllib.parse import quote
            encoded_keyword = quote(keyword)
            url = f"https://www.zhaopin.com/sou/jl{city_code}/kw{encoded_keyword}"
            print(f"   URL: {url}")
            driver.get(url)
            time.sleep(4)

        print(f"📄 页面标题: {driver.title}")
        driver.save_screenshot("zhaopin_page_screenshot.png")
        print("📸 已保存页面截图到 zhaopin_page_screenshot.png\n")

        # Step 3: 等待页面加载
        print("⏳ 等待职位列表加载...")
        try:
            # 智联招聘的职位列表项（注意是 .joblist-box__item 不是 .joblist-box）
            WebDriverWait(driver, 30, 0.5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.joblist-box__item'))
            )
            print("✅ 页面加载成功，找到职位列表\n")
        except Exception as e:
            print(f"❌ 等待页面元素超时: {e}")
            driver.save_screenshot("zhaopin_error_screenshot.png")
            print("📸 已保存错误截图到 zhaopin_error_screenshot.png\n")

            print("=" * 60)
            print("⚠️  可能遇到以下情况：")
            print("   1. 安全验证 - 请在浏览器窗口中手动完成验证")
            print("   2. 需要登录 - 可以手动登录")
            print("   3. 页面结构变化 - CSS选择器可能需要更新")
            print("=" * 60)
            print(f"\n⏰ 等待 30 秒，你可以手动操作浏览器完成验证...\n")
            time.sleep(40)

            # 再次尝试
            try:
                WebDriverWait(driver, 10, 0.5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.joblist-box__item'))
                )
                print("✅ 验证通过，继续爬取\n")
            except:
                driver.quit()
                raise Exception("页面加载失败，可能需要登录或遇到反爬虫验证")

        # Step 4: 提取职位信息
        # 智联招聘的职位卡片选择器
        job_cards = driver.find_elements(By.CSS_SELECTOR, ".joblist-box__item")
        print(f"🔍 找到 {len(job_cards)} 个职位元素")

        # 如果指定了 limit，只处理前 limit 个岗位
        if limit and limit > 0:
            job_cards = job_cards[:limit]
            print(f"📌 限制爬取前 {limit} 个岗位\n")

        jobs = []
        print("🔄 开始提取职位信息...")
        for idx, card in enumerate(job_cards, 1):
            try:
                job = {}

                # 岗位名称
                job_name_elem = card.find_elements(By.CSS_SELECTOR, ".jobinfo__top a")
                if not job_name_elem:
                    continue
                job["job_name"] = job_name_elem[0].text.strip()

                # 薪资
                salary_elem = card.find_elements(By.CSS_SELECTOR, ".jobinfo__salary")
                job["job_salary"] = salary_elem[0].text.strip() if salary_elem else "面议"

                # 岗位标签（经验、学历等）
                tag_elems = card.find_elements(By.CSS_SELECTOR, ".joblist-box__item-tag span")
                job["job_tags"] = [tag.text.strip() for tag in tag_elems if tag.text.strip()]

                # 公司名称
                company_elem = card.find_elements(By.CSS_SELECTOR, ".companyinfo__top a")
                if not company_elem:
                    continue
                job["com_name"] = company_elem[0].text.strip()

                # 公司标签（行业、规模等）
                company_tags = card.find_elements(By.CSS_SELECTOR, ".companyinfo__tag span")
                job["com_tags"] = [tag.text.strip() for tag in company_tags if tag.text.strip()]

                # 工作地点
                location_elem = card.find_elements(By.CSS_SELECTOR, ".jobinfo__other-info-item")
                job["location"] = location_elem[0].text.strip() if location_elem else city

                # 福利标签
                welfare_elems = card.find_elements(By.CSS_SELECTOR, ".joblist-box__item-welfare span")
                job["welfare"] = [w.text.strip() for w in welfare_elems if w.text.strip()]

                jobs.append(job)
                print(f"   ✓ [{idx}/{len(job_cards)}] {job['job_name']} - {job['com_name']}")
            except Exception as e:
                print(f"   ✗ [{idx}/{len(job_cards)}] 提取失败: {e}")
                continue

        print(f"\n✅ 成功提取 {len(jobs)} 个岗位信息")

        # 暂停，让用户可以查看浏览器状态
        print("\n💡 提示：浏览器窗口将保持打开")
        print("   - 可以查看页面状态")

        # 如果没有使用 Cookie 且不是已有浏览器，询问是否保存 Cookie
        if not use_cookies and not use_existing_browser:
            save_cookie = input("\n是否保存当前登录状态的 Cookie？(y/n，默认 y): ").strip().lower()
            if save_cookie != 'n':
                try:
                    save_cookies_to_file(driver)
                    print("💡 下次可以选择选项 1 使用 Cookie 自动登录")
                except Exception as e:
                    print(f"⚠️  保存 Cookie 失败: {e}")

        print("\n   按 Enter 键关闭浏览器并继续...")
        input()

    finally:
        driver.quit()
        print("✅ 浏览器已关闭\n")

    # 格式化输出
    if not jobs:
        raise Exception("没有找到任何岗位信息")

    job_tpl = """
{}. 岗位名称: {}
   公司名称: {}
   工作地点: {}
   岗位要求: {}
   公司信息: {}
   福利待遇: {}
   薪资待遇: {}
"""
    ret = ""
    for i, job in enumerate(jobs, 1):
        job_desc = job_tpl.format(
            i,
            job["job_name"],
            job["com_name"],
            job.get("location", "未知"),
            ", ".join(job["job_tags"]) if job["job_tags"] else "无",
            ", ".join(job["com_tags"]) if job["com_tags"] else "无",
            ", ".join(job.get("welfare", [])) if job.get("welfare") else "无",
            job["job_salary"]
        )
        ret += job_desc

    return ret


def main():
    """主程序入口"""
    print("=" * 60)
    print("    🔍 智联招聘 岗位爬虫工具 V2")
    print("    ✨ 支持任意关键词搜索（职位/公司名等）")
    print("=" * 60)

    # 选择登录方式
    print("\n请选择登录方式：")
    print("  1. 使用 Cookie 文件自动登录（推荐）")
    print("  2. 手动登录（打开新浏览器）")
    print("  3. 使用已打开的浏览器")
    print("  4. 访客模式（不登录）")
    login_choice = input("\n请输入选项（1-4，默认为 2）: ").strip()

    use_existing = False
    use_cookies = False

    if login_choice == "1":
        use_cookies = True
        if not os.path.exists("../zhaopin_cookies.json"):
            print("\n" + "=" * 60)
            print("⚠️  Cookie 文件不存在！")
            print("=" * 60)
            print("\n📝 如何获取 Cookie：")
            print("1. 在浏览器中登录智联招聘")
            print("2. 按 F12 打开开发者工具")
            print("3. 选择 Application/应用 -> Cookies")
            print("4. 复制所有 Cookie")
            print("\n或者选择选项 2 先手动登录，程序会自动保存 Cookie")
            print("=" * 60)
            save_now = input("\n是否现在手动登录并保存 Cookie？(y/n): ").strip().lower()
            if save_now == 'y':
                use_cookies = False
                print("\n💡 请在打开的浏览器中登录，登录后程序会自动保存 Cookie")
                input("准备好后按 Enter 继续...")
            else:
                print("❌ 已取消")
                return
    elif login_choice == "3":
        use_existing = True
        print("\n" + "=" * 60)
        print("⚠️  使用已有浏览器需要先启动 Chrome 的远程调试模式")
        print("=" * 60)
        print("\n请按以下步骤操作：")
        print("1. 完全关闭所有 Chrome 窗口")
        print("2. 打开终端，运行以下命令：")
        print("\n   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222\n")
        print("3. Chrome 会自动打开，在其中登录智联招聘")
        print("4. 然后回到这里按 Enter 继续...")
        input()
    elif login_choice == "4":
        print("\n⚠️  访客模式可能遇到限制，建议使用 Cookie 登录")

    # 输入关键词
    print("\n💡 提示：关键词可以是职位名称、公司名称等任意内容")
    print("   例如：AI应用开发、Python工程师、北京山水众和企业管理有限公司")
    keyword = input("\n请输入要搜索的关键词（默认：AI应用开发）: ").strip()
    if not keyword:
        keyword = "AI应用开发"

    # 选择城市
    print("\n常用城市：")
    print("  北京、上海、深圳、广州、杭州")
    print("  成都、南京、武汉、西安、全国")
    city = input("请输入城市名称（默认：北京）: ").strip()
    if not city:
        city = "北京"

    # 选择爬取模式
    print("\n请选择爬取模式：")
    print("  1. 指定爬取前 N 个岗位")
    print("  2. 爬取第一页所有岗位（默认）")
    choice = input("\n请输入选项（1 或 2，默认为 2）: ").strip()

    limit = None
    if choice == "1":
        while True:
            try:
                num = input("请输入要爬取的岗位数量: ").strip()
                limit = int(num)
                if limit <= 0:
                    print("❌ 数量必须大于 0，请重新输入")
                    continue
                break
            except ValueError:
                print("❌ 请输入有效的数字")

    # 开始爬取
    print("\n" + "=" * 60)
    print(f"🎯 搜索关键词: {keyword}")
    print(f"📍 城市: {city}")
    print(f"🔑 登录方式: {'Cookie 自动登录' if use_cookies else ('使用已有浏览器' if use_existing else '手动登录/访客')}")
    if limit:
        print(f"📊 爬取模式: 前 {limit} 个岗位")
    else:
        print(f"📊 爬取模式: 第一页所有岗位")
    print("=" * 60 + "\n")

    try:
        ret = listjob_by_keyword(keyword, city=city, limit=limit, use_existing_browser=use_existing, use_cookies=use_cookies)
        print("=" * 60)
        print("         📋 爬取结果")
        print("=" * 60)
        print(ret)

        # 保存到文件
        output_file = f"zhaopin_jobs_{keyword}_{city}_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(ret)
        print(f"💾 结果已保存到: {output_file}")

    except Exception as e:
        print(f"\n❌ 爬取失败: {e}")
        print("💡 建议：")
        print("   1. 查看 zhaopin_error_screenshot.png 了解错误原因")
        print("   2. 尝试手动登录后再爬取")
        print("   3. 检查网络连接")


if __name__ == "__main__":
    main()

