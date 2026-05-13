import os
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
from datetime import datetime

# 1. 변수 명칭 통일 (image_550fe2.png 구조 반영)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

async def get_economic_calendar():
    """경제 캘린더 데이터를 수집하는 함수"""
    # 한국 시간 기준 오늘 날짜
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 예시: 인베스팅닷컴의 당일 주요 지표 요약 (실제 운영 시 API나 특정 뉴스레터 URL 활용 권장)
    msg = f"📅 {today} 경제 캘린더 (AM 06:30)\n\n"
    
    try:
        # 여기에 실제 크롤링 로직이 들어갑니다.
        # 우선은 가독성을 위해 구조화된 예시 텍스트를 생성합니다.
        msg += "✅ 주요 발표 일정:\n"
        msg += "- [미국] 소비자물가지수(CPI) (21:30)\n"
        msg += "- [미국] 신규 실업수당청구건수 (21:30)\n"
        msg += "- [유럽] 통화정책회의 (20:45)\n\n"
        msg += "💡 골드(XAU/USD) 변동성에 유의하세요."
    except Exception as e:
        msg += f"데이터를 불러오는 중 오류가 발생했습니다: {e}"
    
    return msg

async def send_message():
    """텔레그램 메시지 전송 함수 (image_550fe2.png 기반)"""
    if not TOKEN or not CHAT_ID:
        print("에러: TELEGRAM_BOT_TOKEN 또는 CHAT_ID가 설정되지 않았습니다.")
        return

    bot = telegram.Bot(token=TOKEN)
    text = await get_economic_calendar()
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text)
        print("메시지 전송 성공!")
    except Exception as e:
        print(f"전송 실패: {e}")

if __name__ == "__main__":
    asyncio.run(send_message())
