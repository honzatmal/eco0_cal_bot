import os
import requests
import telegram
import asyncio
from datetime import datetime, timedelta

# 1. 설정 및 번역 사전
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

TRANSLATION_MAP = {
    "Initial Jobless Claims": "신규 실업수당 청구",
    "Continuing Jobless Claims": "연속 실업수당 청구",
    "Retail Sales MoM": "소매판매 (전월비)",
    "ECB President Lagarde Speech": "라가르드 ECB 총재 연설",
    "Fed Williams Speech": "윌리엄스 연준 위원 연설"
}

async def main():
    if not TOKEN or not CHAT_ID:
        print("❌ 환경 변수 설정 누락")
        return

    # 2. 날짜 설정 및 데이터 호출
    now_kst = datetime.utcnow() + timedelta(hours=9)
    today = now_kst.strftime('%Y-%m-%d')
    url = f"https://economic-calendar.tradingview.com/events?from={today}T00:00:00.000Z&to={today}T23:59:59.999Z&countries=US,EU"
    
    try:
        res = requests.get(url, timeout=7)
        events = res.json().get('result', [])
    except Exception as e:
        print(f"❌ API 에러: {e}")
        return

    if not events:
        print("⚠️ 오늘 예정된 지표가 없습니다.")
        return

    # 3. 데이터 분류 및 메시지 빌드
    sections = {"EU": [], "US": []}
    for e in events:
        c = e.get('country')
        if c in sections:
            sections[c].append(e)

    output = [f"✨ **{now_kst.strftime('%m월 %d일 (%a)')} 지표 브리핑**\n"]
    
    for code, name, flag in [("EU", "EUROZONE", "🇪🇺"), ("US", "UNITED STATES", "🇺🇸")]:
        if not sections[code]: continue
        output.append(f"\n{flag} **{name}**\n━━━━━━━━━━━━━━━━━━")
        
        # 시간순 정렬
        sorted_events = sorted(sections[code], key=lambda x: x['date'])
        for e in sorted_events:
            t = (datetime.fromisoformat(e['date'][:19]) + timedelta(hours=9)).strftime('%H:%M')
            label = TRANSLATION_MAP.get(e['title'], e['title'])
            stars = "⭐" * (e['importance'] + 1)
            
            f, p = e.get('forecast'), e.get('previous')
            val = f" | `{f}` (`{p}`)" if f or p else ""
            output.append(f"`{t}` {stars} {label}{val}")

    # 4. 메시지 전송 (알림 강제 활성화)
    try:
        bot = telegram.Bot(token=TOKEN)
        await bot.send_message(
            chat_id=CHAT_ID, 
            text="\n".join(output), 
            parse_mode='Markdown',
            disable_notification=False  # 소리/진동 알림 켜기
        )
        print("✅ 전송 성공!")
    except Exception as e:
        print(f"❌ 전송 실패: {e}")

if __name__ == "__main__":
    asyncio.run(main())
