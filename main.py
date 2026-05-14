import os
import requests
import telegram
import asyncio
from datetime import datetime, timedelta

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 세련된 번역 사전
TRANSLATION_MAP = {
    "Initial Jobless Claims": "신규 실업수당 청구",
    "Continuing Jobless Claims": "연속 실업수당 청구",
    "Jobless Claims 4-week Average": "실업수당 4주 평균",
    "Retail Sales MoM": "소매판매 (전월비)",
    "Retail Sales YoY": "소매판매 (전년비)",
    "Retail Sales Ex Autos MoM": "소매판매 (자동차 제외)",
    "Export Prices MoM": "수출물가지수 (전월비)",
    "Import Prices MoM": "수입물가지수 (전월비)",
    "ECB President Lagarde Speech": "라가르드 ECB 총재 연설",
    "Fed Williams Speech": "윌리엄스 연준 위원 연설",
    "Retail Sales Ex Gas/Autos MoM": "소매판매 (가스/자동차 제외)"
}

async def get_data():
    kst_now = datetime.utcnow() + timedelta(hours=9)
    date_str = kst_now.strftime('%Y-%m-%d')
    url = "https://economic-calendar.tradingview.com/events"
    params = {"from": f"{date_str}T00:00:00.000Z", "to": f"{date_str}T23:59:59.999Z", "countries": "US,EU"}
    headers = {"User-Agent": "Mozilla/5.0", "Origin": "https://www.tradingview.com"}
    try:
        res = requests.get(url, params=params, headers=headers)
        data = res.json().get('result', [])
        data.sort(key=lambda x: x['date'])
        return data
    except: return []

async def main():
    if not TOKEN or not CHAT_ID: return
    bot = telegram.Bot(token=TOKEN)
    
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_title = kst_now.strftime('📅 %m월 %d일 (%a) 경제 지표')
    
    events = await get_data()
    if not events: return

    # 헤더 구성
    message = f"✨ **{today_title}**\n"
    message += "───\n\n"
    
    for e in events:
        # 시간 및 국가
        t = (datetime.fromisoformat(e['date'].replace('Z', '+00:00')) + timedelta(hours=9)).strftime('%H:%M')
        flag = "🇺🇸" if e['country'] == "US" else "🇪🇺"
        
        # 제목 및 별점 (중요성)
        title = TRANSLATION_MAP.get(e['title'], e['title'])
        # 0:★☆☆, 1:★★☆, 2:★★★
        stars = "★" * (e['importance'] + 1) + "☆" * (2 - e['importance'])
        
        # 수치 레이아웃 개선
        forecast = str(e.get('forecast', '-'))
        previous = str(e.get('previous', '-'))
        
        # 한 줄로 요약된 간결하고 세련된 카드 스타일
        message += f"`{t}` {flag} **{title}**\n"
        message += f"└ {stars}  `예상 {forecast}`  `이전 {previous}`\n\n"

    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(main())
