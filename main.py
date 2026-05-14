import os
import requests
import telegram
import asyncio
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

TRANSLATION_MAP = {
    "Initial Jobless Claims": "신규 실업수당청구건수",
    "Continuing Jobless Claims": "연속 실업수당청구건수",
    "Jobless Claims 4-week Average": "실업수당청구 4주 평균",
    "Retail Sales MoM": "소매판매 (전월비)",
    "Retail Sales YoY": "소매판매 (전년비)",
    "Retail Sales Ex Autos MoM": "자동차 제외 소매판매",
    "Export Prices MoM": "수출물가지수 (전월비)",
    "Import Prices MoM": "수입물가지수 (전월비)",
    "ECB President Lagarde Speech": "라가르드 ECB 총재 연설",
    "ECB Machado Speech": "마차도 위원 연설"
}

async def get_data():
    kst_now = datetime.utcnow() + timedelta(hours=9)
    date_str = kst_now.strftime('%Y-%m-%d')
    url = "https://economic-calendar.tradingview.com/events"
    params = {"from": f"{date_str}T00:00:00.000Z", "to": f"{date_str}T23:59:59.999Z", "countries": "US,EU"}
    headers = {"User-Agent": "Mozilla/5.0", "Origin": "https://www.tradingview.com"}
    
    res = requests.get(url, params=params, headers=headers)
    events = res.json().get('result', [])
    
    parsed = []
    for e in events:
        t = datetime.fromisoformat(e['date'].replace('Z', '+00:00')) + timedelta(hours=9)
        parsed.append({
            "시간": t.strftime('%H:%M'),
            "국가": "🇺🇸 US" if e['country'] == "US" else "🇪🇺 EU",
            "지표명": TRANSLATION_MAP.get(e['title'], e['title']),
            "중요도": "⭐" * (e['importance'] + 1)
        })
    return parsed

def create_image(data, date_str):
    if not data: return None
    df = pd.DataFrame(data)
    
    # 시각화 설정 (한글 폰트 문제로 기본 폰트 사용 시 영문/기호 위주 설정)
    fig, ax = plt.subplots(figsize=(10, len(df)*0.6 + 1))
    ax.axis('off')
    
    # 표 생성
    table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='left', colColours=['#f2f2f2']*4)
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.2, 2.5)
    
    plt.title(f"Economic Calendar ({date_str})", fontsize=16, pad=20)
    
    file_path = "calendar.png"
    plt.savefig(file_path, bbox_inches='tight', dpi=150)
    plt.close()
    return file_path

async def main():
    if not TOKEN or not CHAT_ID: return
    bot = telegram.Bot(token=TOKEN)
    
    kst_now = datetime.utcnow() + timedelta(hours=9)
    date_str = kst_now.strftime('%Y-%m-%d')
    
    data = await get_data()
    if data:
        img_path = create_image(data, date_str)
        if img_path:
            with open(img_path, 'rb') as f:
                await bot.send_photo(chat_id=CHAT_ID, photo=f, caption=f"📅 {date_str} 주요 경제 지표")
    else:
        await bot.send_message(chat_id=CHAT_ID, text=f"📭 {date_str} 예정된 지표가 없습니다.")

if __name__ == "__main__":
    asyncio.run(main())
