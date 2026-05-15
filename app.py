# app.py
import json
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.oauth2.service_account import Credentials

from rag_engine import RAGEngine

load_dotenv(".env")

# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="Demi - CookieCloudyDay",
    page_icon="☁️",
    layout="centered",
)


# =========================
# Load CSS
# =========================
def load_css(file_path: str):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("styles.css")


# =========================
# Config
# =========================
MODEL = "gemini-2.5-flash"
KB_PATH = "knowledge/cookiecloudyday_kb.txt"
THAI_TZ = ZoneInfo("Asia/Bangkok")

MENU_PRICES = {
    "คุกกี้ช็อกโกแลตชิพ": 45,
    "คุกกี้เนยสด": 55,
    "คุกกี้ช็อกโกแลตลาวา": 59,
    "คุกกี้ดับเบิลช็อกโกแลต": 59,
    "คุกกี้มัทฉะไวท์ช็อก": 59,
    "คุกกี้โอรีโอ้ครีม": 50,
    "คุกกี้คาราเมลอัลมอนด์": 55,
    "คุกกี้โกโก้เฮเซลนัท": 59,
    "คุกกี้เรดเวลเวต": 55,
    "คุกกี้บราวนี่ฟัดจ์": 55,
    "คุกกี้สตรอว์เบอร์รีชีสเค้ก": 59,
    "คุกกี้วานิลลานมสด": 45,
    "คุกกี้แมคคาเดเมียไวท์ช็อก": 65,
}

api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


# =========================
# RAG / Chatbot
# =========================
@st.cache_resource
def load_rag():
    return RAGEngine(KB_PATH)


def clean_answer(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = text.replace("===", "")
    text = text.replace("\\n", "\n")
    return text.strip()


def build_prompt(user_question: str, context: str) -> str:
    return f"""คุณคือ Demi ผู้ช่วย AI ของร้าน CookieCloudyDay
หน้าที่ของคุณคือช่วยตอบคำถามลูกค้าเกี่ยวกับเมนู ราคา เวลาเปิดร้าน การจัดส่ง และช่องทางสั่งซื้อ

ให้ตอบโดยอ้างอิงจากข้อมูลร้านด้านล่างเป็นหลัก
ห้ามคัดลอกข้อมูลร้านทั้งก้อนออกมาตอบ ให้สรุปเฉพาะคำตอบที่เกี่ยวข้องกับคำถามเท่านั้น
ห้ามตอบด้วย markdown heading เช่น #, ##, ===
ให้ตอบเป็นข้อความธรรมดาหรือ bullet list เท่านั้น

ถ้าลูกค้าถามกว้าง ๆ เช่น "ขอเมนูหน่อย", "มีอะไรขายบ้าง", "แนะนำเมนูหน่อย"
ให้สรุปรายการเมนูหรือแนะนำเมนูจากข้อมูลที่มีได้

ถ้าลูกค้าถามเรื่องราคา ให้บอกราคาตามข้อมูลที่มีแบบสั้นและอ่านง่าย
ถ้าลูกค้าถามเรื่องสุขภาพ แพ้อาหาร ส่วนผสมเฉพาะ หรือข้อมูลที่ไม่มีในข้อมูลร้าน
ให้ตอบว่าไม่พบข้อมูลนี้ในข้อมูลร้าน และแนะนำให้ติดต่อร้านโดยตรง
ถ้าไม่พบข้อมูลจริง ๆ ให้บอกว่าไม่ทราบ อย่าแต่งข้อมูลเอง

ข้อมูลร้าน:
{context}

คำถาม: {user_question}
"""


def fallback_answer(user_question: str) -> str:
    q = user_question.lower()

    if "เปิด" in q or "กี่โมง" in q or "เวลา" in q:
        return "ร้าน CookieCloudyDay เปิดทุกวัน เวลา 10:00–20:00 น. ค่ะ"

    if "ราคา" in q:
        return """ขออภัยค่ะ ตอนนี้ระบบ AI ตอบไม่ได้ชั่วคราว แต่ Demi มีข้อมูลราคาของร้านดังนี้ค่ะ

- คุกกี้ช็อกโกแลตชิพ 45 บาท
- คุกกี้เนยสด 55 บาท
- คุกกี้ช็อกโกแลตลาวา 59 บาท
- คุกกี้ดับเบิลช็อกโกแลต 59 บาท
- คุกกี้มัทฉะไวท์ช็อก 59 บาท
- คุกกี้โอรีโอ้ครีม 50 บาท
- คุกกี้คาราเมลอัลมอนด์ 55 บาท
- คุกกี้โกโก้เฮเซลนัท 59 บาท
- คุกกี้เรดเวลเวต 55 บาท
- คุกกี้บราวนี่ฟัดจ์ 55 บาท
- คุกกี้สตรอว์เบอร์รีชีสเค้ก 59 บาท
- คุกกี้วานิลลานมสด 45 บาท
- คุกกี้แมคคาเดเมียไวท์ช็อก 65 บาท"""

    if "เมนู" in q or "ขายอะไร" in q or "มีอะไรขาย" in q or "ขอเมนู" in q:
        return """ขออภัยค่ะ ตอนนี้ระบบ AI ตอบไม่ได้ชั่วคราว แต่เมนูของร้าน CookieCloudyDay มีดังนี้ค่ะ

- คุกกี้ช็อกโกแลตชิพ
- คุกกี้เนยสด
- คุกกี้ช็อกโกแลตลาวา
- คุกกี้ดับเบิลช็อกโกแลต
- คุกกี้มัทฉะไวท์ช็อก
- คุกกี้โอรีโอ้ครีม
- คุกกี้คาราเมลอัลมอนด์
- คุกกี้โกโก้เฮเซลนัท
- คุกกี้เรดเวลเวต
- คุกกี้บราวนี่ฟัดจ์
- คุกกี้สตรอว์เบอร์รีชีสเค้ก
- คุกกี้วานิลลานมสด
- คุกกี้แมคคาเดเมียไวท์ช็อก"""

    if "ทุเรียน" in q:
        return "จากข้อมูลเมนูของทางร้านในตอนนี้ ยังไม่มีคุกกี้รสทุเรียนในเมนูนะคะ"

    if "เบอร์" in q or "โทร" in q:
        return "ข้อมูลเบอร์โทรของร้านยังไม่ได้ระบุไว้นะคะ สามารถติดต่อทางร้านได้ทาง DM Instagram @cookiecloudyday หรือ LINE Official ค่ะ"

    if "ส่ง" in q or "จัดส่ง" in q:
        return "ร้าน CookieCloudyDay มีบริการจัดส่ง และสามารถรับหน้าร้านได้ค่ะ"

    if "สั่งซื้อ" in q or "สั่ง" in q:
        return "ลูกค้าสามารถสั่งซื้อได้ทาง DM Instagram @cookiecloudyday หรือ LINE Official ค่ะ"

    return "ขออภัยค่ะ ตอนนี้ระบบ AI ตอบไม่ได้ชั่วคราว กรุณาลองใหม่อีกครั้ง หรือสอบถามทางร้านผ่าน DM Instagram @cookiecloudyday หรือ LINE Official ค่ะ"


# =========================
# Google Sheets
# =========================
def get_secret_value(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value

    try:
        secret_value = st.secrets.get(name, "")
        if isinstance(secret_value, str):
            return secret_value.strip()
    except Exception:
        pass

    return ""


def get_sheet_id() -> str:
    return get_secret_value("GOOGLE_SHEETS_ID")


def get_sheet_client():
    import base64

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    # Streamlit Cloud: ใช้ Base64 secret เท่านั้น
    json_b64 = get_secret_value("GOOGLE_SERVICE_ACCOUNT_JSON_B64")

    if json_b64:
        try:
            json_text = base64.b64decode(json_b64).decode("utf-8")
            info = json.loads(json_text)
            creds = Credentials.from_service_account_info(info, scopes=scopes)
            return gspread.authorize(creds)
        except Exception as e:
            raise RuntimeError(
                "ตั้งค่า GOOGLE_SERVICE_ACCOUNT_JSON_B64 ใน Streamlit Secrets ไม่ถูกต้อง "
                f"รายละเอียด: {e}"
            )

    # Local / Codespaces
    if os.path.exists("service-account.json"):
        creds = Credentials.from_service_account_file(
            "service-account.json",
            scopes=scopes,
        )
        return gspread.authorize(creds)

    raise RuntimeError(
        "ยังไม่ได้ตั้งค่า GOOGLE_SERVICE_ACCOUNT_JSON_B64 ใน Streamlit Secrets "
        "หรือไม่มีไฟล์ service-account.json ตอนรันในเครื่อง"
    )


def append_order_to_sheet(menu_name: str, quantity: int, price: int):
    sheet_id = get_sheet_id()

    if not sheet_id:
        raise RuntimeError("ยังไม่ได้ตั้งค่า GOOGLE_SHEETS_ID ใน Secrets")

    now = datetime.now(THAI_TZ)
    today = now.strftime("%Y-%m-%d")
    total = quantity * price

    client_sheet = get_sheet_client()
    spreadsheet = client_sheet.open_by_key(sheet_id)
    worksheet = spreadsheet.sheet1

    # ให้ตรงกับหัวตารางเดิม:
    # วันที่ | เมนู | จำนวน | ราคา | ยอดรวม
    worksheet.append_row(
        [
            today,
            menu_name,
            quantity,
            price,
            total,
        ],
        value_input_option="USER_ENTERED",
    )

    return total


# =========================
# UI Header
# =========================
rag = load_rag()

st.title("☁️ Demi ผู้ช่วย AI ของร้าน CookieCloudyDay")
st.caption("ถามเรื่องเมนู เวลาเปิด ราคา หรือข้อมูลร้านได้เลย")


# =========================
# Chatbot
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

prompt = st.chat_input("ถามอะไรเกี่ยวกับร้านได้เลย...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    context_chunks = rag.search(prompt, top_k=5)
    context = "\n---\n".join(context_chunks)
    full_prompt = build_prompt(prompt, context)

    if client is None:
        answer = fallback_answer(prompt)
    else:
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=full_prompt,
            )
            answer = response.text.strip() if response.text else fallback_answer(prompt)
        except Exception:
            answer = fallback_answer(prompt)

    answer = clean_answer(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

    with st.chat_message("assistant"):
        st.write(answer)


# =========================
# Order Form
# =========================
st.divider()

st.markdown(
    '<div class="order-section">'
    '<div class="order-title">🛒 สั่งซื้อคุกกี้</div>'
    '<p class="order-subtitle">เลือกเมนูและจำนวนที่ต้องการ ระบบจะคำนวณยอดรวมให้อัตโนมัติ</p>'
    '</div>',
    unsafe_allow_html=True,
)

selected_menu = st.selectbox("เลือกเมนู", list(MENU_PRICES.keys()))

quantity = st.number_input(
    "จำนวน",
    min_value=1,
    max_value=100,
    value=1,
    step=1,
)

price = MENU_PRICES[selected_menu]
total = int(price) * int(quantity)

with st.container(border=True):
    st.subheader("สรุปรายการสั่งซื้อ")

    col1, col2 = st.columns(2)
    with col1:
        st.write("เมนู")
        st.write("จำนวน")
        st.write("ราคาต่อชิ้น")

    with col2:
        st.write(f"**{selected_menu}**")
        st.write(f"**{quantity} ชิ้น**")
        st.write(f"**{price} บาท**")

    st.divider()
    st.metric("ยอดรวม", f"{total} บาท")

st.caption("* เป็นคำสั่งซื้อจำลองสำหรับเดโม ระบบจะบันทึกยอดขายเพื่อใช้สรุปรายงาน")

if st.button("ยืนยันคำสั่งซื้อ"):
    try:
        saved_total = append_order_to_sheet(
            selected_menu,
            int(quantity),
            int(price),
        )
        st.success(
            f"รับออเดอร์แล้วค่ะ: {selected_menu} จำนวน {quantity} ชิ้น รวม {saved_total} บาท"
        )
    except Exception as e:
        st.error(f"ขออภัยค่ะ ระบบยังบันทึกออเดอร์ไม่ได้: {e}")