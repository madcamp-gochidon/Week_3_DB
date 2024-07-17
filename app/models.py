from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class CountryInfo(db.Model):
    __tablename__ = 'CountryInfo'
    country_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    country_name = db.Column(db.String(255), nullable=False)
    country_code = db.Column(db.String(10), nullable=False)  # 국가 코드 추가
    font_info = db.Column(db.Text, nullable=False)

class DailyKeywords(db.Model):
    __tablename__ = 'DailyKeywords'
    keyword_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    word = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('CountryInfo.country_id', ondelete='CASCADE'), nullable=False)
    country = db.relationship('CountryInfo', backref=db.backref('daily_keywords', cascade='all, delete-orphan', lazy=True))

class NewsData(db.Model):
    __tablename__ = 'NewsData'
    news_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text, nullable=False)
    link = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text)  # summary 필드 추가
    keyword_id = db.Column(db.Integer, db.ForeignKey('DailyKeywords.keyword_id', ondelete='CASCADE'), nullable=False)
    keyword = db.relationship('DailyKeywords', backref=db.backref('news_data', cascade='all, delete-orphan', lazy=True))

class VideoLinks(db.Model):
    __tablename__ = 'VideoLinks'
    video_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    country_id = db.Column(db.Integer, db.ForeignKey('CountryInfo.country_id'), nullable=False)  # ON DELETE CASCADE 제거
    video_url = db.Column(db.Text, nullable=False)
    country = db.relationship('CountryInfo', backref=db.backref('video_links', lazy=True))
