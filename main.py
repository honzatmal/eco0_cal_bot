import os
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
from datetime import datetime

# 1. 환경 변수 설정 (이름 통일)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def get_economic_calendar():
    """인베스팅닷컴에서 USD, EUR 지표 데이터를 추출합니다."""
    url = "https://www.investing.com/economic-calendar/"
    
    # 보안 차단을 방지하기 위한 헤더 설정
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 경제 지표 테이블 행 가져오기
        table = soup.find('table', id='economicCalendarData')
        rows = table.find_all('tr', class_='event_drp') if table else []
        
        events = []
        for row in rows:
            # 통화(Currency) 추출
            curr_tag = row.find('td', class_='left flagCur')
            curr = curr_tag.get_text(strip=True) if curr_tag else ""
            
            if curr not in ['USD', 'EUR']:
                continue
            
            # 시간, 지표명, 실제치, 예측치 추출
            time = row.find('td', class_='first left time').get_text(strip=True)
            name = row.find('td', class_='left event').get_text(strip=True)
            actual = row.find('td', class_='bold').get_text(strip=True)
            forecast = row.find('td', class_='fore').get_text(strip=True)
            
            events.append({
                'time': time,
                'curr': curr,
                'name': name,
                'actual': actual if actual else "발표 전",
                'forecast': forecast if forecast else "-"
            })
        return events
    except Exception as e:
        print(f"데이터 수집 중 오류 발생: {e}")
        return []

async def send_telegram_msg():
    if not TOKEN or not CHAT_ID:
        print("토큰 또는 채팅 ID가 설정되지 않았습니다.")
        return

    data = await get_economic_calendar()
    if not data:
        print("전송할 데이터가 없습니다.")
        return

    bot = telegram.Bot(token=TOKEN)
    
    # 메시지 상단 구성
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    msg = f"📊 [경제 지표 리포트 - {now}]\n"
    msg += "대상: USD, EUR 모든 지표\n"
    msg += "━" * 15 + "\n"
    
    for item in data:
        msg += f"🕒 {item['time']} | {item['curr']}\n"
        msg += f"📢 {item['name']}\n"
        msg += f"✅ 실적: {item['actual']} (예상: {item['forecast']})\n"
        msg += "─" * 15 + "\n"

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(send_telegram_msg())
