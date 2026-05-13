import os
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
from datetime import datetime

# 변수 설정
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def get_economic_data():
    """모든 USD, EUR 지표와 실적 값을 가져오는 함수"""
    url = "https://www.investing.com/economic-calendar/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    events = []
    rows = soup.select('tr.event_drp') # 경제 지표 행 선택
    
    for row in rows:
        curr = row.select_one('td.left.flagCur').text.strip()
        if curr not in ['USD', 'EUR']:
            continue
            
        time = row.select_one('td.first.left.time').text.strip()
        name = row.select_one('td.left.event').text.strip()
        actual = row.select_one('td.bold').text.strip() # 실적 값
        forecast = row.select_one('td.fore').text.strip() # 예상 값
        
        events.append({
            'time': time,
            'curr': curr,
            'name': name,
            'actual': actual if actual else "발표 전",
            'forecast': forecast if forecast else "-"
        })
    return events

async def main():
    if not TOKEN or not CHAT_ID:
        print("설정 오류: 토큰 또는 아이디를 확인하세요.")
        return

    bot = telegram.Bot(token=TOKEN)
    data = await get_economic_data()
    
    if not data:
        return

    # 메시지 구성
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    msg = f"📊 [USD/EUR 경제 지표 리포트]\n기준: {current_time}\n"
    msg += "="*25 + "\n"
    
    for item in data:
        msg += f"🕒 {item['time']} | {item['curr']}\n"
        msg += f"📢 {item['name']}\n"
        msg += f"✅ 실적: {item['actual']} (예상: {item['forecast']})\n"
        msg += "-"*20 + "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
