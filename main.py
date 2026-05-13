import os
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
from datetime import datetime, timedelta

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def get_economic_calendar():
    # 한국어 페이지로 접속하여 한국어 명칭 대응
    url = "https://kr.investing.com/economic-calendar/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 모든 경제 지표 행을 가져옴
        rows = soup.select('tr[id^="eventRowId_"]')
        
        events = []
        for row in rows:
            # 1. 국가/통화 텍스트 확인
            curr_td = row.select_one('td.flagCur')
            curr_text = curr_td.get_text(strip=True) if curr_td else ""
            
            # US, USD, 미국, EU, EUR, 유로 중 하나라도 포함되면 수집
            is_target = any(keyword in curr_text.upper() for keyword in ['US', '미국', 'EU', '유로'])
            
            if not is_target:
                continue
            
            # 2. 상세 데이터 추출
            time = row.select_one('td.time').get_text(strip=True) if row.select_one('td.time') else "미정"
            event_td = row.select_one('td.event')
            name = event_td.get_text(strip=True) if event_td else "지표명 없음"
            forecast = row.select_one('td.fore').get_text(strip=True) if row.select_one('td.fore') else "-"
            
            # 국기 이모지 결정
            flag = "🇺🇸" if any(k in curr_text.upper() for k in ['US', '미국']) else "🇪🇺"
            
            events.append(f"{flag} **{curr_text}** | {time}\n📢 {name}\n📊 예상: `{forecast}`\n" + "─"*15)
        
        return events

    except Exception as e:
        print(f"오류 발생: {e}")
        return []

async def main():
    if not TOKEN or not CHAT_ID: return
    
    bot = telegram.Bot(token=TOKEN)
    data = await get_economic_calendar()
    
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = kst_now.strftime('%Y-%m-%d (%a)')
    
    if data:
        msg = f"📅 **오늘의 주요 지표 ({today_str})**\n\n" + "\n".join(data)
    else:
        # 실패 시에도 디버깅을 위해 메시지 전송
        msg = f"📭 **{today_str}**\nUSD/EUR 지표를 수집하지 못했습니다.\n서버 접속 상태나 사이트 언어 설정을 다시 확인해야 합니다."

    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(main())
