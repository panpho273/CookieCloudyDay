import os
import sys
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("ไม่พบ GOOGLE_API_KEY กรุณาตรวจสอบไฟล์ .env")
    sys.exit()

if len(sys.argv) < 3:
    print('วิธีใช้: python caption.py "ชื่อเมนู" "ราคา"')
    print('ตัวอย่าง: python caption.py "คุกกี้ช็อกโกแลตชิพ" "45"')
    sys.exit()

menu_name = sys.argv[1]
price = sys.argv[2]

client = genai.Client(api_key=api_key)

prompt = f"""
คุณคือ AI Marketing Assistant ของร้าน CookieCloudyDay

คอนเซปต์ร้าน:
CookieCloudyDay เป็นร้านคุกกี้โฮมเมดสไตล์น่ารัก ละมุน อบอุ่น
คุกกี้ของร้านพกง่าย กินได้ทุกเวลา เหมาะกับวันเรียนหนัก วันทำงานเหนื่อย
หรือวันที่อยากมีของหวานติดกระเป๋าไว้เติมความสุขระหว่างวัน

ข้อมูลสินค้า:
ชื่อเมนู: {menu_name}
ราคา: {price} บาท

ช่วยเขียนแคปชันภาษาไทย 3 แบบสำหรับโพสต์ขายคุกกี้

รูปแบบ:
1. cute = น่ารัก สดใส
2. minimal = สั้น เรียบง่าย ดูละมุน
3. gen-z = วัยรุ่น สนุก ๆ น่าแชร์

เงื่อนไข:
- ต้องมีชื่อเมนูในทุกแคปชัน
- แต่ละแคปชันต้องสั้น ไม่เกิน 1 ประโยค
- แต่ละแคปชันไม่เกิน 12 คำ
- ไม่ต้องใส่รายละเอียดเยอะ
- ไม่จำเป็นต้องใส่ราคาในทุกแคปชัน
- ถ้าจะใส่ราคา ให้ใส่แบบธรรมชาติ
- เข้ากับแบรนด์ CookieCloudyDay
- ใส่อีโมจิได้พอดี ๆ
- ตอบกลับเป็น JSON เท่านั้น ห้ามอธิบายเพิ่ม

รูปแบบคำตอบ:
{{
  "cute": "...",
  "minimal": "...",
  "gen-z": "..."
}}
"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

print(response.text)
