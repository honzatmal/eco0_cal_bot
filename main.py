import os
import requests
import telegram
import asyncio
from datetime import datetime, timedelta

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
        print("❌ 설정 오류: TOKEN이나 CHAT_ID가 없습니다.")
        return

    # 1. 날짜 설정 (KST 9시간 후)
    now = datetime.utcnow() + timedelta(hours=9)
    date_str = now.strftime('%Y-%m-%d')
    print(f"🕒 조회 날짜: {date_str}")

    # 2. API 호출
    url = f"https://economic-calendar.tradingview.com/events?from={date_str}T00:00:00.000Z&to={date_str}T23:59:59.999Z&countries=US,EU"
    
    try:
        res = requests.get(url, timeout=7)
        events = res.json().get('result', [])
        print(f"📊 검색된 지표 개수: {len(events)}개")
    except Exception as e:
        print(f"❌ API 요청 실패: {e}")
        return

    if not events:
        print("⚠️ 오늘 예정된 지표가 없어 메시지를 보내지 않았습니다.")
        return

    # 3. 메시지 조립
    output = [f"✨ **{now.strftime('%m월 %d일 (%a)')} 지표 브리핑**\n"]
    
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

    # 4. 메시지 전송 (알림 강제 활성화)
    try:
        bot = telegram.Bot(token=TOKEN)
        await bot.send_message(
            chat_id=CHAT_ID, 
            text="\n".join(output), 
            parse_mode='Markdown',
            disable_notification=False  # 소리/진동 알림 켜기
        )
        print("✅ 메시지 전송 완료!")
    except Exception as e:
        print(f"❌ 전송 실패: {e}")

if __name__ == "__main__":
    asyncio.run(main())
