import os
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
from datetime import datetime

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def get_economic_data(mode="schedule"):
    """
    mode="schedule": 아침용 (전체 일정)
    mode="result": 밤용 (실제 결과값 포함)
    """
    # 실제 운영 시에는 Investing.com 또는 API를 통해 데이터를 가져옵니다.
    # 여기서는 USD, EUR 필터링 로직의 예시를 보여줍니다.
    
    target_currencies = ['USD', 'EUR']
    msg = ""
    
    if mode == "schedule":
        msg = "📅 [오늘의 주요 일정] (USD/EUR)\n\n"
        # 예시 데이터 (필터링 로직 적용)
        msg += "🇪🇺 EUR - 독일 소비자물가지수 (16:00)\n"
        msg += "🇺🇸 USD - 미 신규 실업수당청구건수 (21:30)\n"
    else:
        msg = "📢 [지표 발표 결과] (USD/EUR)\n\n"
        # 실제치(Actual)가 업데이트된 데이터만 포함
        msg += "🇺🇸 USD - 실업수당청구건수\n"
        msg += "실제: 212K (예상: 215K) ✅\n"
        msg += "\n💡 골드(XAU/USD) 변동성을 체크하세요."

    return msg

async def send_message():
    if not TOKEN or not CHAT_ID: return
    bot = telegram.Bot(token=TOKEN)
    
    # 실행 시간에 따라 모드 자동 전환 (아침 6시경이면 일정, 그 외엔 결과)
    current_hour = datetime.now().hour
    mode = "schedule" if 5 <= current_hour <= 8 else "result"
    
    text = await get_economic_data(mode=mode)
    await bot.send_message(chat_id=CHAT_ID, text=text)

if __name__ == "__main__":
    asyncio.run(send_message())
