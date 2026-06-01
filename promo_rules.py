import re

def clean_user_message(text):
    if not text:
        return ""

    text = text.replace("\u00A0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_promotion_question(message):
    message = clean_user_message(message).lower()

    promo_keywords = [
        "รับโปร",
        "โปร",
        "โปรโมชั่น",
        "โปรโมชัน",
        "มีโปรไหม",
        "มีโปรมั้ย",
        "โปรวันนี้",
        "ส่วนลด",
        "ลดราคา",
        "โปรร้าน",
        "โปรคุกกี้",
    ]

    return any(word in message for word in promo_keywords)


def build_promotion_prompt(user_message):
    return f"""
ลูกค้าถามเกี่ยวกับโปรโมชั่นของร้าน CookieCloudyDay

ข้อความลูกค้า:
{user_message}

ให้ตอบเฉพาะโปรโมชั่นจริงที่มีอยู่ในข้อมูลร้าน / knowledge base / เอกสารของระบบเท่านั้น
ห้ามแต่งโปรโมชั่นเอง
ห้ามใช้โปรโมชั่นตัวอย่าง
ถ้าไม่พบข้อมูลโปรโมชั่นจริง ให้ตอบว่า:
"ตอนนี้ Demi ยังไม่พบข้อมูลโปรโมชั่นล่าสุดของร้านในระบบค่ะ กรุณาตรวจสอบกับร้านอีกครั้งนะคะ"

ให้ตอบเป็นภาษาไทย สั้น ชัดเจน และเป็นโทนร้านคุกกี้น่ารัก ๆ
"""
