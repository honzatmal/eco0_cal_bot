import os
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
from datetime import datetime

# 1. 환경 변수 명칭 확인 (반드시 GitHub Secrets와 일치해야 함)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def get_economic_calendar():
    url = "https://www.investing.com/economic-calendar/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return f"⚠️ 사이트 접속 실패 (상태 코드: {response.status_code})"

        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('tr.event_drp')
        
        events = []
        for row in rows:
            curr_tag = row.select_one('td.left.flagCur')
            curr = curr_tag.get_text(strip=True) if curr_tag else ""
            
            if curr in ['USD', 'EUR']:
                time = row.select_one('td.first.left.time').get_text(strip=True)
                name = row.select_one('td.left.event').get_text(strip=True)
                actual = row.select_one('td.bold').get_text(strip=True)
                forecast = row.select_one('td.fore').get_text(strip=True)
                
                events.append(f"🕒 {time} | {curr}\n📢 {name}\n✅ 실적: {actual if actual else '발표 전'} (예상: {forecast})\n" + "─"*15)
        
        if not events:
            return "📭 현재 표시할 USD/EUR 지표가 없습니다."
            
        return "📊 [경제 지표 리포트]\n\n" + "\n".join(events)

    except Exception as e:
        return f"❌ 스크립트 에러 발생: {str(e)}"

async def send_telegram_msg():
    # 변수 로드 확인용 로그 (GitHub Actions 콘솔에서 확인 가능)
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN is missing!")
    if not CHAT_ID:
        print("Error: TELEGRAM_CHAT_ID is missing!")
        
    if not TOKEN or not CHAT_ID:
        return

    text = await get_economic_calendar()
    bot = telegram.Bot(token=TOKEN)
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text)
        print("메시지 전송 성공!")
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")

if __name__ == "__main__":
    asyncio.run(send_telegram_msg())
