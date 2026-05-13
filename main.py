import os
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
from datetime import datetime, timedelta

# GitHub Secrets와 명칭 통일
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def get_economic_calendar():
    """USD와 EUR 지표만 필터링하여 가져옵니다."""
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
            # 통화(Currency) 태그 추출
            curr_tag = row.select_one('td.left.flagCur')
            curr = curr_tag.get_text(strip=True) if curr_tag else ""
            
            # USD와 EUR만 필터링 (대문자 기준)
            if curr not in ['USD', 'EUR']:
                continue
            
            # 세부 정보 추출
            time = row.select_one('td.first.left.time').get_text(strip=True)
            name = row.select_one('td.left.event').get_text(strip=True)
            forecast = row.select_one('td.fore').get_text(strip=True)
            
            # 이모지 설정
            flag = "🇺🇸" if curr == "USD" else "🇪🇺"
            
            event_str = (
                f"{flag} **{curr}** | {time}\n"
                f"📢 {name}\n"
                f"📊 예상: `{forecast if forecast else '-'}`\n"
                f"──────────────────"
            )
            events.append(event_str)
        
        return events

    except Exception as e:
        print(f"데이터 수집 에러: {e}")
        return []

async def main():
    if not TOKEN or not CHAT_ID:
        print("설정 오류: Secrets 변수를 확인하세요.")
        return

    data = await get_economic_calendar()
    bot = telegram.Bot(token=TOKEN)
    
    # 한국 시간 기준 날짜
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = kst_now.strftime('%Y-%m-%d (%a)')
    
    if data:
        header = f"📅 **오늘의 주요 지표 ({today_str})**\n"
        header += "대상: USD, EUR 전용\n\n"
        full_message = header + "\n".join(data)
        
        try:
            await bot.send_message(chat_id=CHAT_ID, text=full_message, parse_mode='Markdown')
            print("전송 성공")
        except Exception as e:
            await bot.send_message(chat_id=CHAT_ID, text=full_message)
            print(f"일반 텍스트로 전송됨: {e}")
    else:
        print("표시할 지표가 없습니다.")

if __name__ == "__main__":
    asyncio.run(main())
