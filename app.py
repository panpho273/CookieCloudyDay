# app.py
import os

import streamlit as st
from dotenv import load_dotenv
from google import genai

from rag_engine import RAGEngine

load_dotenv()

# ===== Streamlit Page Config =====
st.set_page_config(
    page_title="Demi - CookieCloudyDay",
    page_icon="☁️",
    layout="centered",
)

# ===== Custom CSS =====
st.markdown(
    """
    <style>
    .block-container {
        max-width: 900px;
        padding-top: 4rem;
        padding-bottom: 6rem;
    }

    h1 {
        font-size: 44px !important;
        line-height: 1.15 !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }

    [data-testid="stCaptionContainer"] {
        color: #9ca3af !important;
        font-size: 15px !important;
        margin-bottom: 22px !important;
    }

    [data-testid="stChatMessage"] {
        border-radius: 16px;
        padding: 8px 12px;
        margin-bottom: 18px;
    }

    [data-testid="stChatInput"] {
        max-width: 820px;
        margin: 0 auto;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    #MainMenu, footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===== Config =====
MODEL = "gemini-2.5-flash"
KB_PATH = "knowledge/cookiecloudyday_kb.txt"

api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


@st.cache_resource
def load_rag():
    return RAGEngine(KB_PATH)


def build_prompt(user_question: str, context: str) -> str:
    return f"""คุณคือ Demi ผู้ช่วย AI ของร้าน CookieCloudyDay
หน้าที่ของคุณคือช่วยตอบคำถามลูกค้าเกี่ยวกับเมนู ราคา เวลาเปิดร้าน การจัดส่ง และช่องทางสั่งซื้อ

ให้ตอบโดยอ้างอิงจากข้อมูลร้านด้านล่างเป็นหลัก
ถ้าลูกค้าถามกว้าง ๆ เช่น "ขอเมนูหน่อย", "มีอะไรขายบ้าง", "แนะนำเมนูหน่อย"
ให้สรุปรายการเมนูหรือแนะนำเมนูจากข้อมูลที่มีได้

ถ้าลูกค้าถามเรื่องเมนู ให้ตอบเป็นรายการที่อ่านง่าย ไม่ต้องยาวเกินไป
ถ้าลูกค้าถามเรื่องราคา ให้บอกราคาตามข้อมูลที่มี
ถ้าลูกค้าถามเรื่องสุขภาพ แพ้อาหาร ส่วนผสมเฉพาะ หรือข้อมูลที่ไม่มีในข้อมูลร้าน
ให้ตอบว่าไม่พบข้อมูลนี้ในข้อมูลร้าน และแนะนำให้ติดต่อร้านโดยตรง
ถ้าไม่พบข้อมูลจริง ๆ ให้บอกว่าไม่ทราบ อย่าแต่งข้อมูลเอง

ข้อมูลร้าน:
{context}

คำถาม: {user_question}
"""


def fallback_answer(context: str) -> str:
    return (
        "ขออภัยค่ะ ตอนนี้ระบบ AI ตอบไม่ได้ชั่วคราว\n\n"
        "แต่จากข้อมูลร้านที่ค้นเจอ มีข้อมูลที่เกี่ยวข้องดังนี้:\n\n"
        f"{context}"
    )


# ===== Load RAG =====
rag = load_rag()

# ===== UI =====
st.title("☁️ Demi ผู้ช่วย AI ของร้าน CookieCloudyDay")
st.caption("ถามเรื่องเมนู เวลาเปิด หรือข้อมูลร้านได้เลย")

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

    # ดึง context มากขึ้น เพื่อให้ตอบคำถามกว้าง ๆ ได้ดีขึ้น
    context_chunks = rag.search(prompt, top_k=5)
    context = "\n---\n".join(context_chunks)

    full_prompt = build_prompt(prompt, context)

    if client is None:
        answer = (
            "ขออภัยค่ะ ระบบยังไม่ได้ตั้งค่า GOOGLE_API_KEY\n\n"
            "ข้อมูลที่ค้นเจอจาก knowledge base:\n\n"
            f"{context}"
        )
    else:
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=full_prompt,
            )
            answer = response.text.strip() if response.text else fallback_answer(context)

        except Exception:
            answer = fallback_answer(context)

    st.session_state.messages.append({"role": "assistant", "content": answer})

    with st.chat_message("assistant"):
        st.write(answer)