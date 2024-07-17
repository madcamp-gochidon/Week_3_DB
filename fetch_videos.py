import os
from googleapiclient.discovery import build
from flask import Flask
from app import create_app
from app.models import db, CountryInfo, VideoLinks

app = create_app()

YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
if not YOUTUBE_API_KEY:
    print("YOUTUBE_API_KEY is not set.")
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def fetch_videos(country_code):
    print(f"Fetching videos for country code: {country_code}")
    request = youtube.videos().list(
        part='snippet',
        chart='mostPopular',
        regionCode=country_code,
        maxResults=40
    )
    response = request.execute()

    videos = []
    for item in response['items']:
        video_id = item['id']
        videos.append(video_id)
    
    return videos

def save_videos_to_db(country_code, videos):
    print(f"Saving videos for country code: {country_code}")
    country = CountryInfo.query.filter_by(country_code=country_code).first()
    if not country:
        print(f"Country with code {country_code} not found in database.")
        return
    
    # Delete all existing video links for the country
    VideoLinks.query.filter_by(country_id=country.country_id).delete()

    # Add new video links
    for video_id in videos:
        video_link = VideoLinks(country_id=country.country_id, video_url=video_id)
        db.session.add(video_link)
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        countries = CountryInfo.query.all()
        if not countries:
            print("No countries found in CountryInfo table.")
        for country in countries:
            print(f"Processing country: {country.country_name} ({country.country_code})")
            videos = fetch_videos(country.country_code)
            save_videos_to_db(country.country_code, videos)
        print("Completed fetching and saving videos.")
