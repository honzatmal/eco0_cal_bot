import os
import requests
import telegram
import asyncio
from datetime import datetime, timedelta

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def get_tradingview_calendar():
    # 트레이딩뷰 경제 캘린더 데이터 서버 (인베스팅닷컴 우회 경로)
    url = "https://economic-calendar.tradingview.com/events?from={date}T00:00:00Z&to={date}T23:59:59Z&countries=US,EU"
    
    # 오늘 날짜 (KST 기준)
    kst_now = datetime.utcnow() + timedelta(hours=9)
    date_str = kst_now.strftime('%Y-%m-%d')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': 'https://www.tradingview.com/'
    }
    
    try:
        # URL에 날짜 삽입
        target_url = url.format(date=date_str)
        response = requests.get(target_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return [f"❌ 데이터 소스 접근 실패 (코드: {response.status_code})"]
            
        data = response.json()
        events = data.get('result', [])
        
        if not events:
            return []

        formatted_events = []
        for event in events:
            # 시간 파싱 (ISO 8601 -> KST)
            utc_time = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
            kst_time = utc_time + timedelta(hours=9)
            time_str = kst_time.strftime('%H:%M')
            
            country = event.get('country', '')
            name = event.get('title', '지표명 없음')
            # 트레이딩뷰는 중요도를 0, 1, 2 등으로 표시
            importance = event.get('importance', 0)
            importance_star = "⭐" * (importance + 1)
            
            flag = "🇺🇸" if country == "US" else "🇪🇺"
            
            formatted_events.append(
                f"{flag} **{country}** | {time_str} | {importance_star}\n"
                f"📢 {name}\n"
                f"──────────────────"
            )
        
        return formatted_events

    except Exception as e:
        print(f"오류: {e}")
        return [f"❌ 시스템 오류: {str(e)}"]

async def main():
    if not TOKEN or not CHAT_ID: return
    
    bot = telegram.Bot(token=TOKEN)
    data = await get_tradingview_calendar()
    
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = kst_now.strftime('%Y-%m-%d (%a)')
    
    if data:
        if "❌" in data[0]:
            msg = data[0]
        else:
            msg = f"📊 **경제 지표 알림 ({today_str})**\n\n" + "\n".join(data)
    else:
        msg = f"📭 **{today_str}**\n오늘 예정된 주요 US/EU 지표가 없습니다."

    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(main())
