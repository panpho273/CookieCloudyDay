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
# Style
# =========================
st.markdown(
    """
    <style>
    .block-container {
        max-width: 920px;
        padding-top: 3.2rem;
        padding-bottom: 7rem;
        margin: 0 auto;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    .hero {
        padding: 20px 0 28px 0;
    }

    .app-title {
        font-size: 44px;
        line-height: 1.16;
        font-weight: 850;
        letter-spacing: -0.8px;
        color: #ffffff;
        margin-bottom: 10px;
        word-break: break-word;
    }

    .app-caption {
        color: #a7adba;
        font-size: 15px;
        line-height: 1.7;
    }

    .divider {
        height: 1px;
        background: rgba(255,255,255,0.12);
        margin: 28px 0 34px 0;
    }

    [data-testid="stChatMessage"] {
        border-radius: 18px;
        padding: 8px 12px;
        margin-bottom: 18px;
    }

    [data-testid="stChatMessageContent"],
    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessageContent"] li {
        font-size: 16px !important;
        line-height: 1.75 !important;
    }

    [data-testid="stChatInput"] {
        max-width: 820px;
        margin: 0 auto;
    }

    .order-card {
        margin-top: 14px;
        padding: 26px;
        border-radius: 26px;
        background:
            radial-gradient(circle at top left, rgba(255, 197, 94, 0.18), transparent 34%),
            linear-gradient(145deg, rgba(255,255,255,0.075), rgba(255,255,255,0.025));
        border: 1px solid rgba(255,255,255,0.12);
        box-shadow: 0 18px 50px rgba(0,0,0,0.25);
    }

    .order-title {
        font-size: 34px;
        font-weight: 850;
        margin-bottom: 8px;
        color: #ffffff;
        letter-spacing: -0.4px;
    }

    .order-subtitle {
        color: #a7adba;
        font-size: 15px;
        margin-bottom: 22px;
        line-height: 1.7;
    }

    .summary-box {
        margin-top: 20px;
        padding: 20px 22px;
        border-radius: 22px;
        background: rgba(0,0,0,0.24);
        border: 1px solid rgba(255,255,255,0.10);
    }

    .summary-title {
        font-size: 19px;
        font-weight: 800;
        margin-bottom: 12px;
        color: #ffffff;
    }

    .summary-row {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        padding: 8px 0;
        color: #d8dce7;
        border-bottom: 1px solid rgba(255,255,255,0.07);
    }

    .summary-row:last-child {
        border-bottom: none;
    }

    .summary-total {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        padding-top: 16px;
        margin-top: 10px;
        font-size: 24px;
        font-weight: 850;
        color: #ffffff;
    }

    .tiny-note {
        color: #8f96a8;
        font-size: 13px;
        margin-top: 14px;
        line-height: 1.6;
    }

    div.stButton > button {
        border-radius: 999px;
        padding: 0.65rem 1.25rem;
        font-weight: 750;
        border: 1px solid rgba(255,255,255,0.18);
        background: linear-gradient(135deg, #ffb547, #ff7a45);
        color: #111827;
    }

    div.stButton > button:hover {
        border: 1px solid rgba(255,255,255,0.3);
        transform: translateY(-1px);
    }

    @media (max-width: 768px) {
        .block-container {
            padding-top: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .app-title {
            font-size: 31px;
        }

        .order-title {
            font-size: 27px;
        }

        .summary-total {
            font-size: 21px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    # Streamlit Cloud: ใช้ Secrets
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(
                dict(st.secrets["gcp_service_account"]),
                scopes=scopes,
            )
            return gspread.authorize(creds)
    except Exception as e:
        raise RuntimeError(f"ตั้งค่า gcp_service_account ใน Streamlit Secrets ไม่ถูกต้อง: {e}")

    # Env JSON string
    json_str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if json_str:
        info = json.loads(json_str)
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        return gspread.authorize(creds)

    # Local / Codespaces
    if os.path.exists("service-account.json"):
        creds = Credentials.from_service_account_file(
            "service-account.json",
            scopes=scopes,
        )
        return gspread.authorize(creds)

    raise RuntimeError(
        "ยังไม่ได้ตั้งค่าบัญชีสำหรับบันทึกออเดอร์ "
        "กรุณาใส่ [gcp_service_account] ใน Streamlit Secrets หรือมีไฟล์ service-account.json ตอนรันในเครื่อง"
    )


def append_order_to_sheet(menu_name: str, quantity: int, price: int):
    sheet_id = get_sheet_id()
    if not sheet_id:
        raise RuntimeError("ยังไม่ได้ตั้งค่า GOOGLE_SHEETS_ID ใน Secrets")

    now = datetime.now(THAI_TZ)
    today = now.strftime("%Y-%m-%d")
    time_text = now.strftime("%H:%M:%S")
    total = quantity * price

    client_sheet = get_sheet_client()
    spreadsheet = client_sheet.open_by_key(sheet_id)
    worksheet = spreadsheet.sheet1

    worksheet.append_row(
        [
            today,
            time_text,
            menu_name,
            quantity,
            price,
            total,
            "Demo Order",
        ],
        value_input_option="USER_ENTERED",
    )

    return total


# =========================
# UI
# =========================
rag = load_rag()

st.markdown(
    """
    <div class="hero">
        <div class="app-title">☁️ Demi ผู้ช่วย AI ของร้าน CookieCloudyDay</div>
        <div class="app-caption">ถามเรื่องเมนู เวลาเปิด ราคา หรือข้อมูลร้านได้เลย</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Chatbot
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

# Order Form
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

st.markdown(
    """
    <div class="order-card">
        <div class="order-title">🛒 สั่งซื้อคุกกี้</div>
        <div class="order-subtitle">
            เลือกเมนูและจำนวนที่ต้องการ ระบบจะคำนวณยอดรวมให้อัตโนมัติ
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

selected_menu = st.selectbox(
    "เลือกเมนู",
    list(MENU_PRICES.keys()),
)

quantity = st.number_input(
    "จำนวน",
    min_value=1,
    max_value=100,
    value=1,
    step=1,
)

price = MENU_PRICES[selected_menu]
total = int(price) * int(quantity)

st.markdown(
    f"""
    <div class="summary-box">
        <div class="summary-title">สรุปรายการสั่งซื้อ</div>

        <div class="summary-row">
            <span>เมนู</span>
            <b>{selected_menu}</b>
        </div>

        <div class="summary-row">
            <span>จำนวน</span>
            <b>{quantity} ชิ้น</b>
        </div>

        <div class="summary-row">
            <span>ราคาต่อชิ้น</span>
            <b>{price} บาท</b>
        </div>

        <div class="summary-total">
            <span>ยอดรวม</span>
            <span>{total} บาท</span>
        </div>
    </div>
    <div class="tiny-note">
        * เป็นคำสั่งซื้อจำลองสำหรับเดโม ระบบจะบันทึกยอดขายเพื่อใช้สรุปรายงาน
    </div>
    """,
    unsafe_allow_html=True,
)

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