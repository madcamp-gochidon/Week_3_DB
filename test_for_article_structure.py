import requests
import feedparser
from bs4 import BeautifulSoup

def fetch_rss_data(url):
    try:
        res = requests.get(url)
        if res.status_code == 200:
            feed = feedparser.parse(res.text)
            return feed
        else:
            print('RSS 요청 오류:', res.status_code)
    except requests.exceptions.RequestException as err:
        print(f'RSS 요청 오류: {err}')
    return None

def fetch_html_data(url):
    try:
        res = requests.get(url)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, 'html.parser')
            return soup
        else:
            print('HTML 요청 오류:', res.status_code)
    except requests.exceptions.RequestException as err:
        print(f'HTML 요청 오류: {err}')
    return None

def main():
    rss_url = 'https://news.google.com/rss/articles/CBMiQGh0dHBzOi8vd3d3Lmh1ZmZpbmd0b25wb3N0LmtyL25ld3MvYXJ0aWNsZVZpZXcuaHRtbD9pZHhubz0yMjUyMjTSAQA?oc=5'  # 예시 RSS URL
    article_url = rss_url  # 예시 기사 URL

    # RSS 데이터 가져오기
    rss_data = fetch_rss_data(rss_url)
    if rss_data:
        print('RSS 데이터:')
        for entry in rss_data.entries:
            print(entry)
            print()

    # HTML 데이터 가져오기
    html_data = fetch_html_data(article_url)
    if html_data:
        print('HTML 데이터:')
        print(html_data.prettify())

if __name__ == "__main__":
    main()
