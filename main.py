import os
import requests
import telegram
import asyncio
from datetime import datetime, timedelta

# 1. 설정값 로드
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
    if not TOKEN or not CHAT_ID: return

    # 2. 데이터 가져오기 (타임아웃 5초로 단축)
    now = datetime.utcnow() + timedelta(hours=9)
    date_str = now.strftime('%Y-%m-%d')
    url = f"https://economic-calendar.tradingview.com/events?from={date_str}T00:00:00.000Z&to={date_str}T23:59:59.999Z&countries=US,EU"
    
    try:
        res = requests.get(url, timeout=5)
        events = res.json().get('result', [])
    except: return

    if not events: return

    # 3. 메시지 빌드 (속도 최적화)
    output = [f"✨ **{now.strftime('%m월 %d일 (%a)')} 지표 브리핑**\n"]
    
    # 국가별 분류
    sections = {"EU": [], "US": []}
    for e in events:
        c = e.get('country')
        if c in sections: sections[c].append(e)

    for code, name, flag in [("EU", "EUROZONE", "🇪🇺"), ("US", "UNITED STATES", "🇺🇸")]:
        if not sections[code]: continue
        output.append(f"\n{flag} **{name}**\n━━━━━━━━━━━━━━━━━━")
        
        for e in sorted(sections[code], key=lambda x: x['date']):
            t = (datetime.fromisoformat(e['date'][:19]) + timedelta(hours=9)).strftime('%H:%M')
            label = TRANSLATION_MAP.get(e['title'], e['title'])
            stars = "⭐" * (e['importance'] + 1)
            f, p = e.get('forecast'), e.get('previous')
            val = f" | `{f}` (`{p}`)" if f or p else ""
            output.append(f"`{t}` {stars} {label}{val}")

    # 4. 메시지 전송 (알림 설정 핵심)
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(
        chat_id=CHAT_ID, 
        text="\n".join(output), 
        parse_mode='Markdown',
        disable_notification=False, # ⭐ False로 설정해야 소리/진동 알림이 옵니다.
        protect_content=False
    )

if __name__ == "__main__":
    asyncio.run(main())
