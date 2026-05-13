import requests
from bs4 import BeautifulSoup
import datetime
import telegram
import asyncio

# 텔레그램 설정
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
CHAT_ID = 'YOUR_CHAT_ID'

async def get_economic_calendar():
    # 실제 구현 시 인베스팅닷컴 또는 국내 경제 뉴스레터 URL 활용
    url = "https://www.investing.com/economic-calendar/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 데이터 추출 로직 (오늘의 주요 일정 필터링)
    # ... (BeautifulSoup 활용 상세 파싱) ...
    
    msg = "📅 오늘의 주요 경제 일정 (6:30 AM 기준)\n\n"
    msg += "1. 미국 소비자물가지수(CPI) 발표 - 21:30\n"
    msg += "2. 연준 의장 연설 - 23:00\n"
    return msg

async def send_message():
    bot = telegram.Bot(token=TOKEN)
    text = await get_economic_calendar()
    await bot.send_message(chat_id=CHAT_ID, text=text)

if __name__ == "__main__":
    asyncio.run(send_message())
