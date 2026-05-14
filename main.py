import os
import requests
import telegram
import asyncio
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime, timedelta

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 한글 폰트 설정 (설치한 나눔폰트 경로)
font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
if os.path.exists(font_path):
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)

TRANSLATION_MAP = {
    "Initial Jobless Claims": "신규 실업수당청구건수",
    "Continuing Jobless Claims": "연속 실업수당청구건수",
    "Retail Sales MoM": "소매판매 (전월비)",
    "ECB President Lagarde Speech": "라가르드 ECB 총재 연설",
    "Fed Williams Speech": "윌리엄스 연준 위원 연설"
    # ... 필요한 지표 추가
}

async def get_data():
    kst_now = datetime.utcnow() + timedelta(hours=9)
    date_str = kst_now.strftime('%Y-%m-%d')
    url = "https://economic-calendar.tradingview.com/events"
    params = {"from": f"{date_str}T00:00:00.000Z", "to": f"{date_str}T23:59:59.999Z", "countries": "US,EU"}
    headers = {"User-Agent": "Mozilla/5.0", "Origin": "https://www.tradingview.com"}
    
    try:
        res = requests.get(url, params=params, headers=headers)
        events = res.json().get('result', [])
        events.sort(key=lambda x: x['date'])
        
        parsed = []
        for e in events:
            t = datetime.fromisoformat(e['date'].replace('Z', '+00:00')) + timedelta(hours=9)
            parsed.append({
                "시간": t.strftime('%H:%M'),
                "외화": "USD" if e['country'] == "US" else "EUR",
                "이벤트": TRANSLATION_MAP.get(e['title'], e['title']),
                "중요성": "★" * (e['importance'] + 1) + "☆" * (2 - e['importance']),
                "예측": e.get('forecast', '-'),
                "이전": e.get('previous', '-')
            })
        return parsed
    except: return []

def create_styled_table(data, date_str):
    if not data: return None
    df = pd.DataFrame(data)
    
    # 표 디자인 설정 (image_d8acbf.png 스타일)
    fig, ax = plt.subplots(figsize=(12, len(df)*0.5 + 1.5))
    ax.axis('off')
    
    # 표 생성
    table = ax.table(
        cellText=df.values, 
        colLabels=df.columns, 
        loc='center', 
        cellLoc='left',
        colWidths=[0.08, 0.08, 0.5, 0.12, 0.1, 0.1]
    )
    
    # 스타일링: 선 없애기 및 헤더 강조
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('#eeeeee') # 아주 연한 회색 선
        if row == 0: # 헤더 행
            cell.set_text_props(weight='bold', color='#333333')
            cell.set_facecolor('#ffffff')
            cell.set_edgecolor('#333333')
            cell.set_linewidth(1)
        else:
            cell.set_linewidth(0.5)
            
    plt.title(f"{date_str} 경제 지표", fontsize=15, pad=30, weight='bold')
    
    img_path = "calendar_final.png"
    plt.savefig(img_path, bbox_inches='tight', dpi=200)
    plt.close()
    return img_path

async def main():
    if not TOKEN or not CHAT_ID: return
    bot = telegram.Bot(token=TOKEN)
    
    kst_now = datetime.utcnow() + timedelta(hours=9)
    date_str = kst_now.strftime('%Y년 %m월 %d일')
    
    data = await get_data()
    if data:
        img_path = create_styled_table(data, date_str)
        with open(img_path, 'rb') as f:
            await bot.send_photo(chat_id=CHAT_ID, photo=f)
    else:
        await bot.send_message(chat_id=CHAT_ID, text=f"📭 {date_str} 지표가 없습니다.")

if __name__ == "__main__":
    asyncio.run(main())
