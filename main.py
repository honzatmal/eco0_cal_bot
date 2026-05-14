import os
import requests
import telegram
import asyncio
from datetime import datetime, timedelta

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 한글 번역 사전
TRANSLATION_MAP = {
    "Initial Jobless Claims": "신규 실업수당청구건수",
    "Continuing Jobless Claims": "연속 실업수당청구건수",
    "Jobless Claims 4-week Average": "실업수당청구 4주 평균",
    "Retail Sales MoM": "소매판매 (전월대비)",
    "Retail Sales YoY": "소매판매 (전년대비)",
    "Retail Sales Ex Autos MoM": "자동차 제외 소매판매 (전월대비)",
    "Export Prices MoM": "수출물가지수 (전월대비)",
    "Export Prices YoY": "수출물가지수 (전년대비)",
    "Import Prices MoM": "수입물가지수 (전월대비)",
    "Import Prices YoY": "수입물가지수 (전년대비)",
    "ECB President Lagarde Speech": "라가르드 ECB 총재 연설",
    "ECB Machado Speech": "마차도 ECB 위원 연설",
    "Retail Sales Ex Gas/Autos MoM": "가스/자동차 제외 소매판매 (전월대비)"
}

async def get_tradingview_calendar():
    kst_now = datetime.utcnow() + timedelta(hours=9)
    date_str = kst_now.strftime('%Y-%m-%d')
    
    url = "https://economic-calendar.tradingview.com/events"
    params = {
        "from": f"{date_str}T00:00:00.000Z",
        "to": f"{date_str}T23:59:59.999Z",
        "countries": "US,EU"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Origin": "https://www.tradingview.com",
        "Referer": "https://www.tradingview.com/"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code != 200:
            return [f"⚠️ 데이터 소스 응답 에러 (코드: {response.status_code})"]

        data = response.json()
        events = data.get('result', [])
        
        if not events:
            return []

        formatted_events = []
        for event in events:
            event_date = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
            kst_time = event_date + timedelta(hours=9)
            time_str = kst_time.strftime('%H:%M')
            
            title = event.get('title', '지표명 없음')
            # 번역 사전에 있으면 한글로 교체, 없으면 원래 영어 제목 사용
            ko_title = TRANSLATION_MAP.get(title, title)
            
            country = event.get('country', '')
            impact = event.get('importance', 0)
            
            flag = "🇺🇸" if country == "US" else "🇪🇺"
            stars = "⭐" * (impact + 1)
            
            formatted_events.append(
                f"{flag} **{country}** | {time_str} | {stars}\n"
                f"📢 {ko_title}\n"
                f"──────────────────"
            )
        return formatted_events

    except Exception as e:
        return [f"❌ 데이터 연결 실패: {str(e)}"]

async def main():
    if not TOKEN or not CHAT_ID: return
    bot = telegram.Bot(token=TOKEN)
    
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = kst_now.strftime('%Y-%m-%d (%a)')

    data = await get_tradingview_calendar()
    
    if data:
        if "⚠️" in data[0] or "❌" in data[0]:
            await bot.send_message(chat_id=CHAT_ID, text=data[0])
        else:
            header = f"📊 **경제 지표 통합 리포트 ({today_str})**\n\n"
            await bot.send_message(chat_id=CHAT_ID, text=header + "\n".join(data), parse_mode='Markdown')
    else:
        await bot.send_message(chat_id=CHAT_ID, text=f"📭 **{today_str}**\n현재 예정된 주요 US/EU 지표가 없습니다.")

if __name__ == "__main__":
    asyncio.run(main())
