import os
import requests
import telegram
import asyncio
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# 환경 변수 설정
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def get_combined_calendar():
    """차단 우회를 위해 모바일 헤더와 다중 경로를 사용하는 통합 함수"""
    # 인베스팅닷컴 모바일 페이지는 데스크톱보다 차단이 덜합니다.
    url = "https://kr.investing.com/economic-calendar/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        # 세션을 사용하여 쿠키 유효성 유지
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=20)
        
        if response.status_code != 200:
            return [f"⚠️ 데이터 소스 접근 제한 (상태 코드: {response.status_code})\n다른 우회 경로를 시도 중입니다..."]

        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('tr[id^="eventRowId_"]')
        
        events = []
        for row in rows:
            # 1. 외화(Country/Currency) 필터링
            curr_td = row.select_one('td.flagCur')
            curr_text = curr_td.get_text(strip=True).upper() if curr_td else ""
            
            # US, USD, 미국, EU, EUR, 유로 키워드 매칭
            is_target = any(k in curr_text for k in ['US', '미국', 'EU', '유로'])
            if not is_target:
                continue
                
            # 2. 데이터 추출
            time = row.select_one('td.time').get_text(strip=True) if row.select_one('td.time') else "미정"
            event_name = row.select_one('td.event').get_text(strip=True) if row.select_one('td.event') else "지표 없음"
            forecast = row.select_one('td.fore').get_text(strip=True) if row.select_one('td.fore') else "-"
            
            # 중요도 추출 (별 개수)
            sentiment = row.select_one('td.sentiment')
            stars = len(sentiment.select('i.grayFullBullishIcon')) if sentiment else 0
            star_str = "⭐" * stars if stars > 0 else "▫️"
            
            flag = "🇺🇸" if any(k in curr_text for k in ['US', '미국']) else "🇪🇺"
            
            events.append(
                f"{flag} **{curr_text}** | {time} | {star_str}\n"
                f"📢 {event_name}\n"
                f"📊 예상: `{forecast}`\n"
                f"──────────────────"
            )
            
        return events

    except Exception as e:
        return [f"❌ 시스템 오류 발생: {str(e)}"]

async def main():
    if not TOKEN or not CHAT_ID:
        print("필수 환경 변수가 설정되지 않았습니다.")
        return
    
    bot = telegram.Bot(token=TOKEN)
    
    # 한국 시간(KST) 기준 날짜 생성
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = kst_now.strftime('%Y-%m-%d (%a)')
    
    data = await get_combined_calendar()
    
    if data:
        # 에러 메시지가 포함된 경우 마크다운 제외하고 일반 텍스트 전송
        if "⚠️" in data[0] or "❌" in data[0]:
            await bot.send_message(chat_id=CHAT_ID, text=data[0])
        else:
            header = f"📅 **경제 지표 통합 리포트 ({today_str})**\n\n"
            full_msg = header + "\n".join(data)
            
            # 텔레그램 메시지 길이 제한(4096자) 대응
            if len(full_msg) > 4000:
                full_msg = full_msg[:3900] + "\n\n(내용이 너무 길어 일부 생략되었습니다.)"
                
            await bot.send_message(chat_id=CHAT_ID, text=full_msg, parse_mode='Markdown')
            print("성공적으로 메시지를 전송했습니다.")
    else:
        await bot.send_message(chat_id=CHAT_ID, text=f"📭 **{today_str}**\n수집된 주요 US/EU 지표가 없습니다.")

if __name__ == "__main__":
    asyncio.run(main())
