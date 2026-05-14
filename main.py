import os
import requests
import telegram
import asyncio
from datetime import datetime, timedelta

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 세련된 번역 사전 (가장 많이 쓰이는 지표 위주)
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
    "Retail Sales Ex Gas/Autos MoM": "소매판매 (가스/차 제외)"
}

async def get_data():
    kst_now = datetime.utcnow() + timedelta(hours=9)
    date_str = kst_now.strftime('%Y-%m-%d')
    url = "https://economic-calendar.tradingview.com/events"
    params = {"from": f"{date_str}T00:00:00.000Z", "to": f"{date_str}T23:59:59.999Z", "countries": "US,EU"}
    headers = {"User-Agent": "Mozilla/5.0", "Origin": "https://www.tradingview.com"}
    try:
        res = requests.get(url, params=params, headers=headers)
        return res.json().get('result', [])
    except: return []

async def main():
    if not TOKEN or not CHAT_ID: return
    bot = telegram.Bot(token=TOKEN)
    
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_title = kst_now.strftime('📅 %m월 %d일 (%a) 지표 브리핑')
    
    events = await get_data()
    if not events: return

    # 데이터 분류 (EU / US)
    eu_events = [e for e in events if e['country'] == 'EU']
    us_events = [e for e in events if e['country'] == 'US']
    
    def format_section(title, flag, event_list):
        if not event_list: return ""
        section = f"{flag} **{title}**\n"
        section += "───\n"
        for e in sorted(event_list, key=lambda x: x['date']):
            t = (datetime.fromisoformat(e['date'].replace('Z', '+00:00')) + timedelta(hours=9)).strftime('%H:%M')
            label = TRANSLATION_MAP.get(e['title'], e['title'])
            
            # 중요도 별점 (⭐ 적용)
            stars = "⭐" * (e['importance'] + 1)
            
            # 수치 정보 요약
            f, p = e.get('forecast', '-'), e.get('previous', '-')
            val = f" | `{f}` (`{p}`)" if f != '-' or p != '-' else ""
            
            section += f"`{t}` {stars} {label}{val}\n"
        return section + "\n"

    # 전체 메시지 조립
    message = f"✨ **{today_title}**\n\n"
    message += format_section("EUROZONE", "🇪🇺", eu_events)
    message += format_section("UNITED STATES", "🇺🇸", us_events)
    
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(main())
