import os
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
from datetime import datetime

# 텔레그램 변수 설정 (이름 통일: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def fetch_economic_data():
    """인베스팅닷컴 등에서 USD, EUR 지표를 모두 긁어오는 함수"""
    url = "https://www.investing.com/economic-calendar/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 실제 환경에서는 requests로 페이지를 가져와 BeautifulSoup으로 파싱합니다.
    # 여기서는 USD, EUR 모든 지표를 처리하는 로직을 담고 있습니다.
    
    target_currencies = ['USD', 'EUR']
    events = [] # 긁어온 지표들이 담길 리스트
    
    # (예시 데이터 구조: 실제 파싱 시 이 형식으로 리스트를 만듭니다)
    sample_data = [
        {"time": "16:00", "curr": "EUR", "name": "독일 소비자물가지수(CPI)", "actual": "2.4%", "forecast": "2.3%"},
        {"time": "21:30", "curr": "USD", "name": "근원 소비자물가지수", "actual": "0.3%", "forecast": "0.3%"},
        {"time": "21:30", "curr": "USD", "name": "실업수당청구건수", "actual": "212K", "forecast": "215K"}
    ]
    
    return [e for e in sample_data if e['curr'] in target_currencies]

async def send_message():
    if not TOKEN or not CHAT_ID:
        return

    bot = telegram.Bot(token=TOKEN)
    data = await fetch_economic_data()
    
    # 현재 시간에 따라 메시지 헤더 변경
    current_hour = datetime.now().hour
    if 5 <= current_hour <= 8:
        header = "📅 [오늘의 모든 USD/EUR 일정]\n"
    else:
        header = "📢 [USD/EUR 지표 실적 업데이트]\n"

    msg = header + "="*25 + "\n"
    
    for item in data:
        msg += f"[{item['time']}] {item['curr']} - {item['name']}\n"
        # 결과값(Actual)이 있는 경우에만 실적 정보 추가
        if item['actual']:
            msg += f"👉 실제: {item['actual']} (예상: {item['forecast']})\n"
        msg += "-"*20 + "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(send_message())
