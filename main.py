import os
import requests
import telegram
import asyncio
from datetime import datetime, timedelta

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def get_economic_calendar():
    """인베스팅닷컴의 모바일 앱용 엔드포인트를 직접 공략합니다. (웹보다 차단이 덜함)"""
    url = "https://ca-api.investing.com/api/v1/economic-calendar/events"
    
    # 오늘 날짜 (KST -> UTC 변환)
    now_kst = datetime.utcnow() + timedelta(hours=9)
    date_str = now_kst.strftime('%Y-%m-%d')
    
    # 앱 접속인 것처럼 위장하는 헤더
    headers = {
        "User-Agent": "InvestingApp/10.0.0 (Android 11; Scale/2.0)",
        "Content-Type": "application/json",
        "X-Meta-App-Id": "com.investing.app",
        "Referer": "https://www.investing.com/"
    }
    
    # 5=미국, 72=유로존 / 중요도 2,3만 필터링 (가독성 위해)
    params = {
        "from": date_str,
        "to": date_str,
        "countries": "5,72",
        "importance": "2,3",
        "time_zone": "8" # 한국 시간대
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        # 만약 이것도 403이 뜨면, 아예 다른 공용 소스를 시도합니다.
        if response.status_code != 200:
            return [f"⚠️ 외부 소스 접근 제한 (코드: {response.status_code})"]

        data = response.json()
        events = data.get('data', [])
        
        if not events:
            return []

        formatted_events = []
        for event in events:
            time = event.get('time', '미정')
            name = event.get('name', '지표명 없음')
            currency = event.get('currency', '')
            forecast = event.get('forecast', '-')
            importance = int(event.get('importance', 0))
            
            flag = "🇺🇸" if currency == "USD" else "🇪🇺"
            stars = "⭐" * importance
            
            formatted_events.append(
                f"{flag} **{currency}** | {time} | {stars}\n"
                f"📢 {name}\n"
                f"📊 예상: `{forecast}`\n"
                f"──────────────────"
            )
        return formatted_events

    except Exception as e:
        print(f"오류: {e}")
        return [f"❌ 데이터 수집 오류 발생"]

async def main():
    if not TOKEN or not CHAT_ID: return
    bot = telegram.Bot(token=TOKEN)
    
    now_kst = datetime.utcnow() + timedelta(hours=9)
    today_str = now_kst.strftime('%Y-%m-%d (%a)')

    data = await get_economic_calendar()
    
    if data:
        # 에러 메시지인 경우 일반 텍스트 전송
        if "⚠️" in data[0] or "❌" in data[0]:
            await bot.send_message(chat_id=CHAT_ID, text=data[0])
        else:
            header = f"📅 **경제 지표 통합 리포트 ({today_str})**\n\n"
            await bot.send_message(chat_id=CHAT_ID, text=header + "\n".join(data), parse_mode='Markdown')
    else:
        # 데이터가 아예 없는 경우 (주말 등)
        await bot.send_message(chat_id=CHAT_ID, text=f"📭 **{today_str}**\n현재 예정된 주요 US/EU 지표가 없습니다.")

if __name__ == "__main__":
    asyncio.run(main())
