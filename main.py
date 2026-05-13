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
    # 헤더를 더 실제 브라우저와 비슷하게 강화
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            return [f"❌ 사이트 접속 실패 (코드: {response.status_code})"]

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 더 유연한 행 선택자 사용
        rows = soup.select('tr[id^="eventRowId_"]') 
        if not rows:
            # 다른 패턴 시도
            rows = soup.find_all('tr', {'class': 'event_drp'})

        events = []
        for row in rows:
            # 통화 필터링
            curr_td = row.select_one('td.flagCur')
            curr = curr_td.get_text(strip=True) if curr_td else ""
            
            if curr not in ['USD', 'EUR']:
                continue
            
            time = row.select_one('td.time').get_text(strip=True) if row.select_one('td.time') else "알수없음"
            event_td = row.select_one('td.event')
            name = event_td.get_text(strip=True) if event_td else "지표명 없음"
            
            # 중요도(별) 확인 (필요시 추가 필터링 가능)
            # star_count = len(row.select('td.sentiment i.grayFullBullishIcon'))
            
            flag = "🇺🇸" if curr == "USD" else "🇪🇺"
            events.append(f"{flag} **{curr}** | {time}\n📢 {name}\n" + "─"*15)
        
        return events

    except Exception as e:
        return [f"❌ 에러 발생: {str(e)}"]

async def main():
    if not TOKEN or not CHAT_ID:
        print("설정 오류: Secrets 확인 필요")
        return

    bot = telegram.Bot(token=TOKEN)
    data = await get_economic_calendar()
    
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = kst_now.strftime('%Y-%m-%d (%a)')
    
    # 메시지 전송 로직
    if data:
        if "❌" in data[0]: # 에러 발생 시
            msg = data[0]
        else:
            msg = f"📅 **오늘의 주요 지표 ({today_str})**\n\n" + "\n".join(data)
    else:
        msg = f"📭 **{today_str}**\n오늘은 예정된 주요 USD/EUR 지표가 없습니다."

    try:
        # 메시지 분할 전송 (너무 길 경우 에러 방지)
        if len(msg) > 4000:
            await bot.send_message(chat_id=CHAT_ID, text=msg[:4000], parse_mode='Markdown')
        else:
            await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
        print("전송 시도 완료")
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")

if __name__ == "__main__":
    asyncio.run(main())
