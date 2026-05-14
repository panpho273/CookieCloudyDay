# Cost Awareness and Debugging Mindset

## 1. Cost Awareness

โปรเจกต์ CookieCloudyDay ใช้บริการ cloud และ API หลายส่วน ได้แก่ Gemini API, HuggingFace Spaces, Google Sheets, Telegram Bot และ GitHub Actions ดังนั้นต้องระวังเรื่อง quota, rate limit และการเก็บ secret ให้ปลอดภัย

### Gemini API

ระบบใช้ Gemini API สำหรับสร้างคำตอบของ AI ทั้งใน Agent Harness และ RAG Chatbot

สิ่งที่ต้องระวัง:

- ไม่เรียก API ใน loop โดยไม่จำเป็น
- ไม่ส่ง request ถี่เกินไป
- ถ้าเจอ quota หรือ rate limit ควรรอแล้วค่อย retry
- API key ต้องเก็บใน `.env`, GitHub Secrets หรือ HuggingFace Secrets เท่านั้น
- ห้าม hard-code API key ลงในไฟล์ Python

แนวทางป้องกัน:

```python
import time

def safe_generate(generate_func, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return generate_func()
        except Exception as e:
            error_text = str(e).lower()

            if "quota" in error_text or "resource_exhausted" in error_text or "503" in error_text:
                wait = 2 ** attempt
                print(f"Rate limited or unavailable. Retry in {wait} seconds...")
                time.sleep(wait)
            else:
                raise

    raise RuntimeError("เกิน retry limit")