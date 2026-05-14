import os
import requests
import telegram
import asyncio
from datetime import datetime, timedelta

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 깔끔한 번역 사전
TRANSLATION_MAP = {
    "Initial Jobless Claims": "신규 실업수당 청구",
    "Continuing Jobless Claims": "연속 실업수당 청구",
    "Retail Sales MoM": "소매판매 (전월비)",
    "Retail Sales YoY": "소매판매 (전년비)",
    "ECB President Lagarde Speech": "라가르드 ECB 총재 연설",
    "Fed Williams Speech": "윌리엄스 연준 위원 연설",
    "EIA Natural Gas Stocks Change": "천연가스 재고변화"
}

async def get_data():
    kst_now = datetime.utcnow() + timedelta(hours=9)
    date_str = kst_now.strftime('%Y-%m-%d')
    url = "https://economic-calendar.tradingview.com/events"
    params = {"from": f"{date_str}T00:00:00.000Z", "to": f"{date_str}T23:59:59.999Z", "countries": "US,EU"}
    headers = {"User-Agent": "Mozilla/5.0", "Origin": "https://www.tradingview.com"}
    
    try:
        res = requests.get(url, params=params, headers=headers)
        events = res.json().get('result', [])
        events.sort(key=lambda x: x['date']) # 시간순 정렬
        return events
    except: return []

async def main():
    if not TOKEN or not CHAT_ID: return
    bot = telegram.Bot(token=TOKEN)
    
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_title = kst_now.strftime('📅 %m월 %d일 (%a) 경제 지표')
    
    events = await get_data()
    
    if not events:
        await bot.send_message(chat_id=CHAT_ID, text=f"{today_title}\n\n예정된 주요 지표가 없습니다.")
        return

    # 메시지 구성
    message = f"✨ **{today_title}**\n"
    message += "━━━━━━━━━━━━━━━━━━\n\n"
    
    for e in events:
        # 시간 및 국가 설정
        t = (datetime.fromisoformat(e['date'].replace('Z', '+00:00')) + timedelta(hours=9)).strftime('%H:%M')
        flag = "🇺🇸" if e['country'] == "US" else "🇪🇺"
        
        # 지표명 번역 및 중요도 이모지
        title = TRANSLATION_MAP.get(e['title'], e['title'])
        importance = "🔴" if e['importance'] == 2 else "🟠" if e['importance'] == 1 else "⚪"
        
        # 수치 정보 (값이 있을 때만 표시)
        forecast = e.get('forecast')
        previous = e.get('previous')
        val_info = f"\n   `예측 {forecast if forecast else '-'}` | `이전 {previous if previous else '-'}`" if forecast or previous else ""

        # 한 줄의 깔끔한 카드 스타일 구성
        message += f"{importance} `{t}` {flag} **{title}**{val_info}\n\n"

    message += "━━━━━━━━━━━━━━━━━━"
    
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(main())
