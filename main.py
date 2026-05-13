import os
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
from datetime import datetime, timedelta

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def get_economic_calendar():
    url = "https://www.investing.com/economic-calendar/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 행 선택자 보강
        rows = soup.select('tr[id^="eventRowId_"]')
        
        events = []
        for row in rows:
            # 외화 텍스트 추출 (US, USD, EU, EUR 모두 대응)
            curr_td = row.select_one('td.flagCur')
            curr = curr_td.get_text(strip=True).upper() if curr_td else ""
            
            # US/USD 또는 EU/EUR 인지 확인
            is_us = "US" in curr
            is_eu = "EU" in curr
            
            if not (is_us or is_eu):
                continue
            
            time = row.select_one('td.time').get_text(strip=True) if row.select_one('td.time') else "시간미정"
            name = row.select_one('td.event').get_text(strip=True) if row.select_one('td.event') else "지표명 없음"
            forecast = row.select_one('td.fore').get_text(strip=True) if row.select_one('td.fore') else "-"
            
            flag = "🇺🇸" if is_us else "🇪🇺"
            events.append(f"{flag} **{curr}** | {time}\n📢 {name}\n📊 예상: `{forecast}`\n" + "─"*15)
        
        return events

    except Exception as e:
        print(f"오류: {e}")
        return []

async def main():
    if not TOKEN or not CHAT_ID: return
    
    bot = telegram.Bot(token=TOKEN)
    data = await get_economic_calendar()
    
    # 한국 시간 기준 날짜
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = kst_now.strftime('%Y-%m-%d (%a)')
    
    if data:
        msg = f"📅 **오늘의 주요 지표 ({today_str})**\n\n" + "\n".join(data)
    else:
        # 데이터가 없을 때의 피드백 메시지 강화
        msg = f"📭 **{today_str}**\n필터링된 USD/EUR 지표를 찾지 못했습니다.\n(사이트 구조나 통화 명칭 확인 필요)"

    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(main())
