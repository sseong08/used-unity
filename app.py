from flask import Flask, request, render_template
import requests
import json
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service as ChromeService

app = Flask(__name__)

customheader = {
    'refer': "https://m.bunjang.co.kr/",
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
} 

baseurl_bun = 'https://api.bunjang.co.kr/api/1/find_v2.json?q='
lasturl_bun = '&order=score&page=0&request_id=20221204202700&f_category_id=&stat_device=w&n=100&stat_category_required=1&req_ref=search&version=4'

baseurl_car = "https://www.daangn.com/search/"
baseurl_jun = "https://web.joongna.com/search/"
junjun = "https://web.joongna.com/"

def junggo(plusurl):
    jun_url = baseurl_jun + urllib.parse.quote_plus(plusurl)
    options = Options()
    options.add_experimental_option("detach", True)  # 브라우저 바로 닫힘 방지
    options.add_experimental_option("excludeSwitches", ["enable-logging"])  # 불필요한 메시지 제거
    options.add_argument("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")  # 헤더 값 입력
    # options.add_argument('headless')
    
    service = ChromeService(executable_path=ChromeDriverManager().install())  # 자동으로 최신 크롬드라이버 다운로드

    driver = webdriver.Chrome(service=service, options=options)  # 크롬 실행
    driver.get(jun_url)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    
    results = []
    titles = soup.find_all(class_="line-clamp-2 text-sm md:text-base text-heading")
    prices = soup.find_all(class_="font-semibold space-s-2 mt-0.5 text-heading lg:text-lg lg:mt-1.5")
    links = soup.find_all(class_="group box-border overflow-hidden flex rounded-md cursor-pointer pe-0 pb-2 lg:pb-3 flex-col items-start transition duration-200 ease-in-out transform bg-white")
    images = soup.find_all("img", class_="bg-gray-300 object-cover h-full group-hover:scale-105 w-full transition duration-200 ease-in rounded-md")

    if len(titles) == len(prices) == len(links):
        for title, price, link, image in zip(titles, prices, links, images):
            result = {
                "title": title.get_text(strip=True),
                "price": price.get_text(strip=True),
                "url": junjun + link['href'].replace("//", "/"),
                "img": image['src']
            }
            results.append(result)
    else:
        results.append({"error": "The number of titles, prices, and links do not match."})
    
    return results

def lightning(plusurl):
    bun_url = baseurl_bun + urllib.parse.quote_plus(plusurl) + lasturl_bun
    req = requests.get(bun_url, headers=customheader)

    results = []
    if req.status_code == requests.codes.ok:
        stock_data = json.loads(req.text)
        for i, thing in enumerate(stock_data["list"], 1):
            if "삽니다" not in thing['name']:
                result = {
                    "title": thing['name'],
                    "price": f'{int(thing["price"]):,} 원',
                    "url": 'https://m.bunjang.co.kr/products/' + thing["pid"] + '?q=' + plusurl + '&ref=' + urllib.parse.quote_plus("검색결과"),
                    "image": thing['product_image']
                }
                results.append(result)
    else:
        results.append({"error": "Request failed with status code " + str(req.status_code)})
    
    return results

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        query = request.form['query']
        jun_results = junggo(query)
        bun_results = lightning(query)
        return render_template('index.html', query=query, jun_results=jun_results, bun_results=bun_results)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
