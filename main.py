import os
import requests
import telegram
import asyncio
from datetime import datetime, timedelta

# 환경 변수 및 설정
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 번역 사전을 최소화하고 필요 시에만 접근하도록 설정
TRANSLATION_MAP = {
    "Initial Jobless Claims": "신규 실업수당 청구",
    "Continuing Jobless Claims": "연속 실업수당 청구",
    "Retail Sales MoM": "소매판매 (전월비)",
    "ECB President Lagarde Speech": "라가르드 ECB 총재 연설",
    "Fed Williams Speech": "윌리엄스 연준 위원 연설"
}

async def get_data():
    # KST 계산 최적화
    now = datetime.utcnow() + timedelta(hours=9)
    date_str = now.strftime('%Y-%m-%d')
    
    # API 요청 시 국가를 필요한 곳으로 한정해 데이터 양 축소
    url = "https://economic-calendar.tradingview.com/events"
    params = {
        "from": f"{date_str}T00:00:00.000Z",
        "to": f"{date_str}T23:59:59.999Z",
        "countries": "US,EU",
        "importance": "0,1,2" # 전체 중요도 포함하되 데이터 필터링은 내부에서 처리
    }
    
    try:
        # 타임아웃을 짧게 설정해 무한 대기 방지
        res = requests.get(url, params=params, timeout=10)
        return res.json().get('result', [])
    except:
        return []

async def main():
    if not (TOKEN and CHAT_ID): return
    
    events = await get_data()
    if not events: return

    # 리스트 컴프리헨션을 사용해 루프를 한 번만 돌도록 최적화
    kst_offset = timedelta(hours=9)
    today = (datetime.utcnow() + kst_offset).strftime('%m월 %d일 (%a)')
    
    sections = {"EU": [], "US": []}
    for e in events:
        c = e.get('country')
        if c in sections:
            sections[c].append(e)

    # 메시지 빌드 (문자열 결합 최적화)
    output = [f"✨ **{today} 지표 브리핑**\n"]
    
    for country, name, flag in [("EU", "EUROZONE", "🇪🇺"), ("US", "UNITED STATES", "🇺🇸")]:
        if not sections[country]: continue
        
        output.append(f"\n{flag} **{name}**\n━━━━━━━━━━━━━━━━━━")
        
        # 시간순 정렬 및 포맷팅
        sections[country].sort(key=lambda x: x['date'])
        for e in sections[country]:
            t = (datetime.fromisoformat(e['date'][:19]) + kst_offset).strftime('%H:%M')
            label = TRANSLATION_MAP.get(e['title'], e['title'])
            stars = "⭐" * (e['importance'] + 1)
            
            # 데이터 유무 확인 로직 간소화
            f, p = e.get('forecast'), e.get('previous')
            val = f" | `{f}` (`{p}`)" if f or p else ""
            output.append(f"`{t}` {stars} {label}{val}")

    # 리스트를 한 번에 join하여 문자열 생성 (메모리 효율적)
    final_text = "\n".join(output)
    
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=final_text, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(main())
