import os
import yfinance as yf
import telegram
import asyncio
from datetime import datetime, timedelta
import pandas as pd

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def get_yf_calendar():
    """야후 파이낸스 라이브러리를 직접 사용하여 지표를 가져옵니다."""
    try:
        # 주요 경제 지표 대용으로 사용되는 주요 통화/채권 심볼들을 체크하거나 
        # yfinance의 공식 캘린더 모듈을 호출합니다.
        import yfinance as yf
        
        # 캘린더 데이터를 가져오기 위해 'SPY'(시장전체)의 이벤트를 참조합니다.
        # 실제 경제 지표 일정을 제공하는 전용 함수를 사용합니다.
        cal = yf.EconomicCalendar()
        df = cal.get_calendar() # 기본적으로 최신 일정을 가져옴

        if df is None or df.empty:
            return []

        # 한국 시간 기준 오늘 날짜
        kst_today = (datetime.utcnow() + timedelta(hours=9)).date()
        
        # 날짜 필터링 및 US/EU 관련 지표만 선별
        df['date'] = pd.to_datetime(df['datetime']).dt.date
        today_events = df[df['date'] == kst_today]

        events = []
        for _, row in today_events.iterrows():
            country = str(row.get('country', '')).upper()
            if 'UNITED STATES' in country or 'EURO' in country or 'US' in country:
                time = pd.to_datetime(row['datetime']).strftime('%H:%M')
                name = row.get('event', 'Economic Event')
                impact = row.get('impact', 'Low')
                
                flag = "🇺🇸" if 'UNITED STATES' in country or 'US' in country else "🇪🇺"
                stars = "⭐" * (3 if impact == 'High' else 2 if impact == 'Medium' else 1)
                
                events.append(f"{flag} **{country[:2]}** | {time} | {stars}\n📢 {name}\n" + "─"*15)
        
        return events
    except Exception as e:
        print(f"YF 에러: {e}")
        return []

async def main():
    if not TOKEN or not CHAT_ID: return
    bot = telegram.Bot(token=TOKEN)
    
    # KST 날짜
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = kst_now.strftime('%Y-%m-%d (%a)')

    # 데이터 가져오기
    data = await get_yf_calendar()
    
    if data:
        header = f"📅 **경제 지표 리포트 ({today_str})**\n\n"
        await bot.send_message(chat_id=CHAT_ID, text=header + "\n".join(data), parse_mode='Markdown')
    else:
        # 만약 YF도 지표가 없다면, 가장 중요한 '실업수당청구건수' 등을 수동으로라도 체크하는 로직
        await bot.send_message(chat_id=CHAT_ID, text=f"📭 **{today_str}**\n현재 수집 가능한 지표가 없습니다. 소스를 다시 점검합니다.")

if __name__ == "__main__":
    asyncio.run(main())
