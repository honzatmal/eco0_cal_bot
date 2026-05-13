import os
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
from datetime import datetime, timedelta

# 환경 변수 (Secrets와 명칭 통일)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def get_economic_calendar():
    """인베스팅닷컴에서 USD, EUR 지표 데이터를 가져옵니다."""
    url = "https://www.investing.com/economic-calendar/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('tr.event_drp')
        
        events = []
        for row in rows:
            curr_tag = row.select_one('td.left.flagCur')
            curr = curr_tag.get_text(strip=True) if curr_tag else ""
            
            if curr in ['USD', 'EUR']:
                time = row.select_one('td.first.left.time').get_text(strip=True)
                name = row.select_one('td.left.event').get_text(strip=True)
                forecast = row.select_one('td.fore').get_text(strip=True)
                
                events.append(f"🕒 {time} | {curr}\n📢 {name}\n📊 예상: {forecast if forecast else '-'}\n" + "─"*15)
        
        return "\n".join(events) if events else "📭 오늘 예정된 주요 USD/EUR 지표가 없습니다."

    except Exception as e:
        return f"❌ 데이터 수집 중 에러 발생: {str(e)}"

async def send_daily_msg():
    """매일 아침 07:05 지표 일정 전송"""
    if not TOKEN or not CHAT_ID: return

    data = await get_economic_calendar()
    bot = telegram.Bot(token=TOKEN)
    
    now_kst = (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d')
    header = f"📅 [오늘의 지표 일정 - {now_kst}]\n"
    header += "대상: USD, EUR 모든 지표\n"
    header += "━" * 15 + "\n"

    try:
        await bot.send_message(chat_id=CHAT_ID, text=header + data)
        print("데일리 지표 전송 완료")
    except Exception as e:
        print(f"전송 실패: {e}")

if __name__ == "__main__":
    # 실적 확인 모드 제거, 데일리 알림만 수행
    asyncio.run(send_daily_msg())
