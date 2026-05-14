import os
import yfinance as yf
import telegram
import asyncio
from datetime import datetime, timedelta

# 환경 변수 설정
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def get_stable_calendar():
    """yfinance 라이브러리를 통해 차단 없이 경제 지표를 가져오는 방식"""
    try:
        # 야후 파이낸스 API는 직접적인 캘린더 리스트를 제한할 수 있으므로
        # 가장 안정적인 인베스팅닷컴의 'RSS 피드' 또는 '대체 JSON 경로'를 사용합니다.
        # 아래 경로는 차단 방역이 상대적으로 약한 API용 경로입니다.
        url = "https://common-api.investing.com/economic-calendar/v1/events"
        
        # 오늘 날짜 설정 (UTC 기준)
        today = datetime.utcnow().strftime('%Y-%m-%d')
        params = {
            'from': today,
            'to': today,
            'importance': '1,2,3', # 모든 중요도 포함
            'countries': '5,72'    # 5=미국, 72=유로존
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Referer': 'https://www.investing.com/'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return ["⚠️ 서비스 접속이 원활하지 않습니다. 잠시 후 다시 시도해 주세요."]
            
        data = response.json()
        events_list = data.get('data', [])
        
        if not events_list:
            return []

        formatted_events = []
        for event in events_list:
            # 시간 처리
            time_str = event.get('time', '미정')
            name = event.get('name', '지표명 없음')
            currency = event.get('currency', '')
            forecast = event.get('forecast', '-')
            importance = int(event.get('importance', 0))
            
            flag = "🇺🇸" if currency == "USD" else "🇪🇺"
            stars = "⭐" * importance
            
            formatted_events.append(
                f"{flag} **{currency}** | {time_str} | {stars}\n"
                f"📢 {name}\n"
                f"📊 예상: `{forecast}`\n"
                f"──────────────────"
            )
        
        return formatted_events

    except Exception as e:
        print(f"오류: {e}")
        return []

# 위 방식이 실패할 경우를 대비한 '직접 크롤링 보강' 함수
import requests
from bs4 import BeautifulSoup

async def get_fallback_data():
    """기존 방식에 '언어 우회'를 추가한 보조 함수"""
    url = "https://www.investing.com/economic-calendar/"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1'}
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select('tr[id^="eventRowId_"]')
        
        results = []
        for row in rows:
            curr = row.select_one('.flagCur').text.strip()
            if curr in ['USD', 'EUR']:
                time = row.select_one('.time').text.strip()
                event = row.select_one('.event').text.strip()
                flag = "🇺🇸" if curr == "USD" else "🇪🇺"
                results.append(f"{flag} **{curr}** | {time}\n📢 {event}\n" + "─"*15)
        return results
    except:
        return []

async def main():
    if not TOKEN or not CHAT_ID: return
    bot = telegram.Bot(token=TOKEN)
    
    # 1순위: 안정적인 API 시도
    data = await get_stable_calendar()
    
    # 2순위: 실패 시 보조 크롤링 시도
    if not data:
        data = await get_fallback_data()
    
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = kst_now.strftime('%Y-%m-%d (%a)')
    
    if data:
        header = f"📅 **경제 지표 리포트 ({today_str})**\n\n"
        await bot.send_message(chat_id=CHAT_ID, text=header + "\n".join(data), parse_mode='Markdown')
    else:
        # 정말 데이터가 없을 경우
        await bot.send_message(chat_id=CHAT_ID, text=f"📭 **{today_str}**\n현재 예정된 주요 US/EU 지표가 없습니다.")

if __name__ == "__main__":
    asyncio.run(main())
