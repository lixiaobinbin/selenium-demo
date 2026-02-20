# 默认 只取上海  代码以后再改
import random
import time
from urllib.parse import urlencode

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

listurl = "https://www.zhipin.com/web/geek/job?{}"


def get_UA():
    UA_list = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4651.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36'
    ]
    randnum = random.randint(0, len(UA_list) - 1)
    UA = UA_list[randnum]
    return UA


def set_cookies(browser):  # 在已登录后的网站页面中获取Cookie信息
    cookie_string = "ab_guid=d2ef3a90-ff18-4646-9ec0-408b44394ab4; lastCity=101120100; __zp_seo_uuid__=365bccd9-aa81-4fdc-a90b-5718a5e6432c; __g=-; Hm_lvt_194df3105ad7148dcf2b98a91b5e727a=1739522069,1741359607; HMACCOUNT=8174E1A21EC21A07; __l=r=https%3A%2F%2Fcn.bing.com%2F&l=%2Fwww.zhipin.com%2Fweb%2Fgeek%2Fjob&s=1&s=3&friend_source=0; SERVERID=669c12b6205dadc4b25f7f10ddc9cc19|1741441738|1741440644; Hm_lpvt_194df3105ad7148dcf2b98a91b5e727a=1741522802; wt2=DTn-yz7ad4E6Vgodv0yEAo5A0cWVJEQxQ5m979XmRzTmXuYowAvPcrj4w3uksnkLLfhbjWOPYO9ZaeZ5yUljXDQ~~; wbg=0; zp_at=tlWmkvZ1jjJ6fIfQJO34KzTKmdr4VP--3SX8Th56fKI~; __c=1741359607; __a=76416774.1739522068.1739522068.1741359607.29.2.27.29; __zp_stoken__=6ee4fw4sKw5kXPBZoZxcWeUxuemR2UVdLTGfDhWLCtnPCr8KGwprCrcK%2FwqvCkcKtwql5UUvDiMOIV8Ktw73CssSGTcKbUMK2wr%2FCjk3DrVHCnsSaw7HEusWFeMOHwr7CpkE0GRcYExYWGBcUGX%2FCgRMYFRAOEQoPEA4RCg89MsSBwpgsOzxGOjFZV1gMVWhlUWlRDltQTT88ChJkFDw4QTo%2FQMOJQcOAwqfDhz7Cu8Kiw4hAwrzDsTpHQD7Cu1AqRDwNwrrDqAxMDcK6w68MPEHDimbDr8KzIcOBdzQ8O8K6xL5HPR9EPDtHOkFHOz0vQTTDkGfDrsK3H8K7UCo6HEM9Okg6Oz06RjxJMTpJwokxPUEqSBMLDBAKKkjCvcKswr%2FDqD06"  # 拆分cookie字符串为键值对列表
    cookie_pairs = cookie_string.split("; ")  # 添加cookie
    for pair in cookie_pairs:
        key, value = pair.strip().split("=", 1)  # cookie字典
        cookie = {
            'domain': '.zhipin.com',
            'name': key,
            'value': value,
            'path': '/'
        }
        browser.add_cookie(cookie)
        time.sleep(3)  # 刷新页面
        browser.refresh()
        return browser


def init_driver(headless: bool = False) -> webdriver.Chrome:
    """初始化浏览器驱动 - macOS 版本

    Args:
        headless: 是否使用无头模式，默认 False（显示浏览器窗口）
    """
    options = Options()

    # 反爬虫对策 - 隐藏自动化特征
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    # 无头模式配置（建议关闭以避免被检测）
    if headless:
        options.add_argument('--headless=new')

    # 基础配置
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')  # 重要：隐藏自动化标识
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-notifications')

    # 使用真实的用户代理（macOS Chrome）
    ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    options.add_argument(f'user-agent={ua}')

    # 窗口配置
    options.add_argument('--start-maximized')
    options.add_argument('--window-size=1920,1080')

    # 创建 Chrome driver - Selenium 4.x 会自动下载管理 ChromeDriver
    driver = webdriver.Chrome(options=options)

    # 执行 CDP 命令隐藏 webdriver 属性
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


def listjob_by_keyword(keyword: str, page: int = 1, size: int = 30) -> str:
    print("listjob")
    url = listurl.format(urlencode({
        "query": keyword,
        "city": "101020100"
    }))
    print("url: ", url)
    driver = init_driver()
    if driver is None:
        raise Exception("创建无头浏览器失败")
    print("创建无头浏览器成功")
    # driver.maximize_window()

    driver.get(url)
    print("title: ", driver.title)
    # print(driver.get_cookies())
    # driver = set_cookies(driver)
    # all_cookies = driver.get_cookies()
    # for cookie in all_cookies:
    #    print(cookie)
    driver.save_screenshot("page_screenshot.png")
    print("title: ", driver.title)

    # 等待页面加载，最多等待 40 秒
    try:
        WebDriverWait(driver, 40, 0.5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.job-list-box'))
        )
        print("✅ 页面加载成功，找到职位列表")
    except Exception as e:
        print(f"❌ 等待页面元素超时: {e}")
        driver.save_screenshot("error_screenshot.png")
        print("📸 已保存错误截图到 error_screenshot.png")
        print("\n" + "=" * 60)
        print("⚠️  可能遇到以下情况：")
        print("   1. 安全验证 - 请在浏览器窗口中手动完成验证")
        print("   2. 需要登录 - 可以手动登录")
        print("   3. 页面结构变化 - CSS选择器可能需要更新")
        print("=" * 60)
        print(f"\n⏰ 等待 30 秒，你可以手动操作浏览器完成验证...\n")
        time.sleep(50)

        # 再次尝试
        try:
            WebDriverWait(driver, 10, 0.5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.job-list-box'))
            )
            print("✅ 验证通过，继续爬取")
        except:
            driver.quit()
            raise Exception("页面加载失败，可能需要登录或遇到反爬虫验证")

    li_list = driver.find_elements(By.CSS_SELECTOR,
                                   ".job-list-box li.job-card-wrapper")
    jobs = []
    for li in li_list:
        job_name_list = li.find_elements(By.CSS_SELECTOR, ".job-name")
        if len(job_name_list) == 0:
            continue
        job = {}
        job["job_name"] = job_name_list[0].text
        job_salary_list = li.find_elements(By.CSS_SELECTOR, ".job-info .salary")
        if job_salary_list and len(job_salary_list) > 0:
            job["job_salary"] = job_salary_list[0].text
        else:
            job["job_salary"] = "暂无"
        job_tags_list = li.find_elements(By.CSS_SELECTOR, ".job-info .tag-list li")
        if job_tags_list and len(job_tags_list) > 0:
            job["job_tags"] = [tag.text for tag in job_tags_list]
        else:
            job["job_tags"] = []
        com_name = li.find_element(By.CSS_SELECTOR, ".company-name")
        if com_name:
            job["com_name"] = com_name.text
        else:
            continue  #
        com_tags_list = li.find_elements(By.CSS_SELECTOR, ".company-tag-list li")
        if com_tags_list and len(com_tags_list) > 0:
            job["com_tags"] = [tag.text for tag in com_tags_list]
        else:
            job["com_tags"] = []
        job_tags_list_footer = li.find_elements(By.CSS_SELECTOR, ".job-card-footer  li")
        if job_tags_list_footer and len(job_tags_list_footer) > 0:
            job["job_tags_footer"] = [tag.text for tag in job_tags_list_footer]
        else:
            job["job_tags_footer"] = []
        jobs.append(job)
    driver.close()
    job_tpl = """
{}. 岗位名称: {}
公司名称: {}
岗位要求: {}
技能要求: {}
薪资待遇: {}
     """
    ret = ""
    if len(jobs) > 0:
        for i, job in enumerate(jobs):
            job_desc = job_tpl.format(str(i + 1), job["job_name"],
                                      job["com_name"],
                                      ",".join(job["job_tags"]),
                                      ",".join(job["job_tags_footer"]),
                                      job["job_salary"])
            ret += job_desc + "\n"
        print("完成直聘网分析")
        return ret
    else:
        raise Exception("没有找到任何岗位列表")


if __name__ == "__main__":
    print("listjob")
    ret = listjob_by_keyword("AI应用开发")
    print(ret)