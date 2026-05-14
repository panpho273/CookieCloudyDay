# CookieCloudyDay

CookieCloudyDay คือโปรเจกต์ AI สำหรับร้านคุกกี้โฮมเมด โดยพัฒนาต่อจากตัวอย่าง MilkLab ให้กลายเป็นธุรกิจของตัวเอง ระบบนี้ประกอบด้วย caption generator, sales logger, Telegram morning report, agent harness และ RAG chatbot สำหรับตอบคำถามลูกค้าจาก knowledge base ของร้าน

## Live Demo

HuggingFace Space: https://huggingface.co/spaces/panpho273/cookiecloudyday-demi

## Features

- Generate captions for CookieCloudyDay menu items
- Record sales into Google Sheets
- Send daily sales summary to Telegram
- Use Agent Harness to convert Thai commands into tool actions
- Use RAG chatbot to answer customer questions from CookieCloudyDay knowledge base

## Demo Questions

ตัวอย่างคำถามที่ใช้ทดสอบ chatbot:

1. ร้านเปิดกี่โมง
2. เมนูขายดีมีอะไรบ้าง
3. ถ้าไม่ชอบหวานมากควรเลือกเมนูไหน
4. มีบริการจัดส่งไหม
5. สั่งซื้อได้ทางไหน

## Local Setup

ติดตั้ง dependencies:

```bash
pip install -r requirements.txt