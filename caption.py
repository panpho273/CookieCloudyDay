import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ไม่พบ GEMINI_API_KEY กรุณาตรวจสอบไฟล์ .env")
    exit()

genai.configure(api_key=api_key)

mmodel = genai.GenerativeModel("gemini-2.5-flash")

product_name = input("ใส่ชื่อสินค้า/รสชาติคุกกี้: ")

prompt = f"""
ช่วยเขียนแคปชันขายคุกกี้สำหรับร้าน CookieCloudyDay
สินค้า: {product_name}

ขอแคปชันภาษาไทย 3 แบบ
สไตล์น่ารัก อบอุ่น เหมาะกับการโพสต์ Instagram
ใส่อีโมจิพอดี ๆ และมี hashtag ท้ายแคปชัน
"""

response = model.generate_content(prompt)

print("\n=== Caption ที่ AI สร้างให้ ===\n")
print(response.text)