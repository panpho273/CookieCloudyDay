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
        "cookie fortune",
        "cookie club",
    ]

    return any(word in message for word in promo_keywords)


def get_promotion_reply():
    return """
ตอนนี้ CookieCloudyDay มีโปรโมชันของร้านตามนี้ค่ะ ☁️🍪

🔮 ซื้อครบ 150 บาท
รับสิทธิ์สุ่มไพ่ Cookie Fortune ฟรี 1 ใบ พร้อมข้อความน่ารักจากร้าน

ถ้าลูกค้าสนใจ สั่งเมนูที่ชอบให้ครบ 150 บาทได้เลยนะคะ เดี๋ยว Demi ช่วยสรุปออเดอร์ให้ค่ะ 🤎
"""

