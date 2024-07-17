from pytrends.request import TrendReq
import pandas as pd
from datetime import datetime, timedelta
from app import create_app, db
from app.models import CountryInfo, DailyKeywords, NewsData
import requests
import feedparser
from bs4 import BeautifulSoup
import re

def get_trending_searches(country_code):
    pytrends = TrendReq(hl='en-US', tz=360)
    trending_searches_df = pytrends.trending_searches(pn=country_code)
    return trending_searches_df.head(30)

def fetch_news_for_keyword(country_code, keyword):
    URL = f'https://news.google.com/rss/search?q={keyword}+when:1d'
    URL += f'&hl={country_code}&gl={country_code.upper()}&ceid={country_code.upper()}'

    try:
        res = requests.get(URL, timeout=10)
        if res.status_code == 200:
            datas = feedparser.parse(res.text).entries
            if datas:
                return datas[0]  # 가장 첫 번째 결과만 반환
        else:
            print('Google 검색 에러')
    except requests.exceptions.RequestException as err:
        print(f'Error Requests: {err}')
    return None

def clean_text(text):
    # a : b 형식의 텍스트 제거
    text = re.sub(r'\b\w+\s*:\s*\w+\b', '', text)
    # 괄호 안에 포함된 내용 제거
    text = re.sub(r'\(.*?\)', '', text)
    return text.strip()

def fetch_article_content(url, title):
    try:
        res = requests.get(url)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, 'html.parser')

            # 1. 메타 태그에서 description 내용을 추출
            meta_description = soup.find('meta', attrs={'name': 'description'})
            if meta_description:
                description = clean_text(meta_description.get('content'))
                if description == title:
                    return "Summary not supported for this article. More in the link."
                return description

            # 2. <article> 태그에서 내용을 추출
            articles = soup.find_all('article')
            if articles:
                content = ' '.join([clean_text(tag.get_text(separator=' ', strip=True)) for tag in articles if len(tag.get_text()) > 20])
                if content and content != title:
                    return content

            # 3. <section> 태그에서 내용을 추출
            sections = soup.find_all('section')
            if sections:
                content = ' '.join([clean_text(tag.get_text(separator=' ', strip=True)) for tag in sections if len(tag.get_text()) > 20])
                if content and content != title:
                    return content

            # 4. <div> 태그에서 내용을 추출
            divs = soup.find_all('div')
            if divs:
                content = ' '.join([clean_text(tag.get_text(separator=' ', strip=True)) for tag in divs if len(tag.get_text()) > 20])
                if content and content != title:
                    return content
            
            # 유효한 기사 내용을 찾지 못했을 경우 기본 문구 반환
            return "Summary not supported for this article. More in the link."
    except requests.exceptions.RequestException as err:
        print(f'Error fetching article content: {err}')
    return "Summary not supported for this article. More in the link."

def truncate_summary(summary, max_length):
    if len(summary) > max_length:
        return summary[:max_length] + '...'
    return summary

def clean_summary(summary):
    if summary:
        cleaned_summary = re.sub(r'<a href="[^"]+"[^>]*>[^<]+</a>', '', summary)
        return cleaned_summary.strip()
    return summary

def remove_invalid_characters(text):
    # 유니코드 문자 중에서 데이터베이스에 문제가 될 수 있는 특정 문자를 제거
    return re.sub(r'[\U00010000-\U0010ffff]', '', text)

def is_poor_summary(summary, title):
    # 중복된 단어 확인
    if re.search(r'(\b\w+\b)(\s+\1\b)+', summary):
        return True
    # 공백이 비정상적으로 많은 경우
    if len(re.findall(r'\s', summary)) / len(summary) > 0.5:
        return True
    # 요약의 단어 수 확인
    if len(summary.split()) < 5:
        return True
    # 요약의 길이 확인
    if len(summary) <= 40:
        return True
    # 제목과 요약이 포함 관계인 경우
    if title.strip() in summary.strip() or summary.strip() in title.strip():
        return True
    return False

def fetch_and_store_trends(max_summary_length=500):
    app = create_app()
    with app.app_context():
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)

        DailyKeywords.query.filter(DailyKeywords.date == yesterday).delete()
        db.session.commit()
        print(f"Deleted trends for date: {yesterday}")

        countries = CountryInfo.query.all()

        for country in countries:
            country_code = country.country_code.lower()
            trending_searches_df = get_trending_searches(country.country_name)
            trending_searches_df.columns = ['word']
            trending_searches_df['word'] = trending_searches_df['word']

            for index, row in trending_searches_df.iterrows():
                word = row['word']
                value = (30 - index) ** 2 * 1
                keyword = DailyKeywords.query.filter_by(word=word, date=today, country_id=country.country_id).first()

                if not keyword:
                    keyword = DailyKeywords(word=word, value=value, country_id=country.country_id, date=today)
                    db.session.add(keyword)
                    db.session.flush()

                news_item = fetch_news_for_keyword(country_code, word)
                if news_item:
                    title = news_item.title
                    link = news_item.link
                    summary = fetch_article_content(link, title)
                    if summary:
                        summary = clean_summary(summary)
                        summary = truncate_summary(summary, max_summary_length)
                        summary = remove_invalid_characters(summary)

                    # 요약이 부실한 경우 처리
                    if not summary or is_poor_summary(summary, title):
                        summary = "Summary not supported for this article. More in the link."

                    existing_news = NewsData.query.filter_by(keyword_id=keyword.keyword_id).first()

                    if existing_news:
                        existing_news.title = title
                        existing_news.link = link
                        existing_news.summary = summary
                        print(f"News for keyword '{word}' updated in database.")
                    else:
                        news_data = NewsData(title=title, link=link, summary=summary, keyword_id=keyword.keyword_id)
                        db.session.add(news_data)
                        print(f"News for keyword '{word}' stored in database.")
            
            db.session.commit()
            print(f"Trends and news for {country.country_name} stored in database.")

if __name__ == "__main__":
    app = create_app()
    fetch_and_store_trends()
