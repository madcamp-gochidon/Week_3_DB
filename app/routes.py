from app.models import *
import logging
import requests
from flask import Flask, Blueprint, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from newspaper import Article
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 모든 도메인에서 오는 요청 허용


bp = Blueprint('api', __name__)
CORS(bp)  # Blueprint에 대해 CORS 설정 적용

def get_redirected_url(url):
    try:
        response = requests.get(url, allow_redirects=True)
        return response.url
    except requests.RequestException as e:
        logging.error(f"Error fetching the URL: {e}")
        return None

def summarize_article(url, sentences_count=3):
    redirected_url = get_redirected_url(url)
    if not redirected_url:
        return "Failed to retrieve the article"

    article = Article(redirected_url)
    article.download()
    article.parse()
    parser = PlaintextParser.from_string(article.text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentences_count)
    return ' '.join([str(sentence) for sentence in summary])

@bp.route('/get_keyword_and_news/<country_code>', methods=['GET'])
def get_keywords_by_country_code(country_code):
    country = CountryInfo.query.filter_by(country_code=country_code.upper()).first()
    if not country:
        return jsonify({'error': 'Country not found'}), 404
    
    keywords = DailyKeywords.query.filter_by(country_id=country.country_id).all()
    keywords_list = [[k.word, k.value] for k in keywords]
    return jsonify(keywords_list)

@bp.route('/get_news_summary/<country_code>', methods=['GET'])
def get_news_summary_by_country_code(country_code):
    today = datetime.now().date()
    country = CountryInfo.query.filter_by(country_code=country_code.lower()).first()
    
    if not country:
        return jsonify({"error": "Country not found"}), 404
    
    keywords = DailyKeywords.query.filter_by(country_id=country.country_id, date=today).all()
    
    news_summaries = []
    
    for keyword in keywords:
        news_data = NewsData.query.filter_by(keyword_id=keyword.keyword_id).first()
        if news_data:
            news_summaries.append({
                "title": news_data.title,
                "link": news_data.link,
                "summary": news_data.summary,
                "keyword": keyword.word,
                "value": keyword.value
            })
    
    if not news_summaries:
        return jsonify({"error": "No news summaries found for today"}), 404
    
    return jsonify(news_summaries), 200

@bp.route('/get_video_ids/<country_code>', methods=['GET'])
def get_video_ids_by_country_code(country_code):
    country = CountryInfo.query.filter_by(country_code=country_code.upper()).first()
    if not country:
        return jsonify({'error': 'Country not found'}), 404
    
    video_links = VideoLinks.query.filter_by(country_id=country.country_id).all()
    video_ids_list = [v.video_url for v in video_links]  # video_url 필드에 비디오 ID가 저장되어 있음
    return jsonify(video_ids_list)