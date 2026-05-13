import os
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
from datetime import datetime, timedelta

# 1. 환경 변수 설정
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def get_economic_calendar(mode):
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
                actual = row.select_one('td.bold').get_text(strip=True)
                forecast = row.select_one('td.fore').get_text(strip=True)
                
                # 모드별 메시지 구성
                if mode == "MORNING":
                    # 오전: 일정 위주 (실적 제외)
                    events.append(f"🕒 {time} | {curr}\n📢 {name}\n📊 예상: {forecast if forecast else '-'}")
                else:
                    # 저녁: 실적 위주 (실적 값이 있는 것 강조)
                    status = f"✅ 실적: {actual}" if actual else "⏳ 발표 대기 중"
                    events.append(f"🕒 {time} | {curr}\n📢 {name}\n{status} (예상: {forecast})")
        
        if not events:
            return None
            
        title = "📅 [오늘의 경제 일정]" if mode == "MORNING" else "📢 [주요 지표 실적 리포트]"
        return f"{title}\n" + "━"*15 + "\n" + "\n\n".join(events)

    except Exception as e:
        return f"❌ 데이터 수집 중 에러 발생: {str(e)}"

async def send_telegram_msg():
    if not TOKEN or not CHAT_ID:
        print("설정 오류: Secrets를 확인하세요.")
        return

    # 한국 시간(KST) 기준으로 모드 결정 (UTC+9 반영)
    now_utc = datetime.utcnow()
    now_kst = now_utc + timedelta(hours=9)
    hour = now_kst.hour
    
    # 오전 5~9시 사이 실행 시 아침 모드, 그 외엔 실적 모드
    mode = "MORNING" if 5 <= hour <= 9 else "RESULT"
    
    text = await get_economic_calendar(mode)
    
    if text:
        bot = telegram.Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=text)
        print(f"{mode} 메시지 전송 완료")
    else:
        print("전송할 지표 데이터가 없습니다.")

if __name__ == "__main__":
    asyncio.run(send_telegram_msg())
