import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration - MUST be first
st.set_page_config(
    page_title="Demi - CookieCloudyDay",
    page_icon="🍪",
    layout="centered"
)

# CSS - Keep it minimal
st.markdown("""
<style>
    .user-msg { text-align: right; color: #0066cc; margin: 8px 0; }
    .bot-msg { color: #333; margin: 8px 0; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "orders" not in st.session_state:
    st.session_state.orders = []

# Try to load Google API (optional)
try:
    from google import genai
    API_KEY = os.getenv("GOOGLE_API_KEY")
    GEMINI_CLIENT = genai.Client(api_key=API_KEY) if API_KEY else None
except:
    GEMINI_CLIENT = None

# Menu data
MENUS = {
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

# Promotion data
PROMOTIONS = {
    "promotion_conditions": {
        "ซื้อครบ 150 บาท": "ได้รับ Cookie Fortune ฟรี 1 ใบ",
        "ซื้อครบ 300 บาท": "ได้รับส่วนลด 10% + Cookie Fortune 2 ใบ",
        "ซื้อครบ 500 บาท": "ได้รับส่วนลด 15% + Cookie Fortune 3 ใบ + ของขวัญพิเศษ",
    }
}

# Header
st.title("☁️ Demi - CookieCloudyDay")
st.markdown("**ผู้ช่วย AI ของร้านคุกกี้โฮมเมด** ⏰ 10:00-20:00")
st.divider()

# System instruction for AI
SYSTEM_INSTRUCTION = """
คุณคือ Demi ผู้ช่วย AI ของร้าน CookieCloudyDay
หน้าที่ของคุณคือตอบคำถามเกี่ยวกับ:
1. เมนูคุกกี้ - ชื่อ รส ราคา
2. เวลาเปิดปิดร้าน
3. การสั่งซื้อ
4. เงื่อนไขโปรโมชั่น - ซื้อครบ 150 บาทได้ Cookie Fortune ฟรี 1 ใบ, ซื้อครบ 300 บาทได้ส่วนลด 10% + Cookie Fortune 2 ใบ, ซื้อครบ 500 บาทได้ส่วนลด 15% + Cookie Fortune 3 ใบ + ของขวัญพิเศษ
5. แนะนำเมนูที่เหมาะสม

ตอบให้ย่อ สดใส และเป็นกันเอง ใช้อิโมจิ
หากไม่รู้ข้อมูล ให้บอกตรงๆ ว่า "ไม่มีข้อมูล ลองติดต่อร้านโดยตรงนะ"
"""

def get_demi_response(user_message):
    """Get response from Google Gemini"""
    if GEMINI_CLIENT is None:
        return "❌ API Key ไม่พบ - ตั้งค่า GOOGLE_API_KEY ใน environment"
    
    try:
        response = GEMINI_CLIENT.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            system_instruction=SYSTEM_INSTRUCTION,
            config={"temperature": 0.7, "max_output_tokens": 300}
        )
        return response.text
    except Exception as e:
        return f"⚠️ Error: {str(e)[:80]}"

def parse_order_from_message(message: str) -> dict:
    """Extract menu and quantity from user message"""
    order = {}
    message_lower = message.lower()
    
    for menu_name in MENUS.keys():
        if menu_name in message:
            # Extract quantity
            quantity = 1
            words = message.split()
            for i, word in enumerate(words):
                if word.isdigit():
                    quantity = int(word)
                elif "อัน" in word or "ชิ้น" in word or "จำนวน" in word:
                    if i > 0 and words[i-1].isdigit():
                        quantity = int(words[i-1])
            
            order["menu"] = menu_name
            order["price"] = MENUS[menu_name]
            order["quantity"] = quantity
            break
    
    return order

def display_bill():
    """Display order bill"""
    if not st.session_state.orders:
        return
    
    st.subheader("🧾 บิลออเดอร์")
    
    total = 0
    for i, order in enumerate(st.session_state.orders, 1):
        item_total = order["price"] * order["quantity"]
        total += item_total
        st.write(f"{i}. {order['menu']} × {order['quantity']} = **{item_total}** ฿")
    
    st.write("---")
    st.write(f"**ยอดรวม: {total} ฿**")
    
    # Show promo
    if total >= 500:
        st.success("💎 ซื้อครบ 500 ฿ → ลด 15% + Fortune 3 + ของขวัญ")
    elif total >= 300:
        st.success("⭐ ซื้อครบ 300 ฿ → ลด 10% + Fortune 2")
    elif total >= 150:
        st.success("🎁 ซื้อครบ 150 ฿ → Fortune 1")

def clear_input():
    """Clear input"""
    st.session_state.user_input = ""

# Chat display
st.subheader("💬 สนทนากับ Demi")

if not st.session_state.messages:
    st.info("👋 สวัสดี! สอบถามเมนู ราคา หรือสั่งซื้อได้เลย")
else:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<p class="user-msg">👤 {msg["content"]}</p>', unsafe_allow_html=True)
        else:
            st.markdown(f'<p class="bot-msg">🤖 {msg["content"]}</p>', unsafe_allow_html=True)

# Show bill if there are orders
if st.session_state.orders:
    st.divider()
    display_bill()
    if st.button("🗑️ ล้างออเดอร์"):
        st.session_state.orders = []
        st.rerun()

st.divider()

# Input
st.subheader("💬 พูดกับ Demi")
col1, col2 = st.columns([5, 1])

with col1:
    user_input = st.text_input(
        "พูดเรื่องอะไร",
        placeholder="เช่น: เมนูแนะนำ, ราคา, เอา 2 ชิ้น",
        key="txt_input"
    )

with col2:
    send = st.button("📤", key="send_btn")

# Process input
if send and user_input:
    # Add user msg
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Check for order
    order = parse_order_from_message(user_input)
    if order:
        st.session_state.orders.append(order)
        ai_msg = f"✅ บันทึก: {order['menu']} × {order['quantity']} ชิ้น = {order['price']*order['quantity']} ฿\n\n"
        ai_msg += get_demi_response(user_input)
    else:
        ai_msg = get_demi_response(user_input)
    
    # Add bot msg
    st.session_state.messages.append({"role": "assistant", "content": ai_msg})
    st.rerun()

st.divider()
st.caption("🤖 Powered by Google Gemini | CookieCloudyDay 2026")
