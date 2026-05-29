import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Configuration
st.set_page_config(
    page_title="Demi - CookieCloudyDay AI Assistant",
    page_icon="🍪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .chat-message {
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 8px;
        max-width: 80%;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: auto;
        text-align: right;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    .bill-container {
        background-color: #fffacd;
        border: 2px solid #ffd700;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
    }
    .bill-title {
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 12px;
        color: #333;
    }
    .bill-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #ddd;
    }
    .bill-total {
        display: flex;
        justify-content: space-between;
        padding: 12px 0;
        font-weight: bold;
        font-size: 16px;
        color: #d32f2f;
    }
    .promo-info {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 12px;
        margin: 12px 0;
        border-radius: 4px;
    }
    .promotion-condition {
        font-weight: 500;
        color: #e65100;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "orders" not in st.session_state:
    st.session_state.orders = []

if "client" not in st.session_state:
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        st.session_state.client = genai.Client(api_key=api_key)
    else:
        st.error("ไม่พบ GOOGLE_API_KEY ในไฟล์ .env")

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
st.markdown("""
<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; margin-bottom: 20px;">
    <h1 style="color: white; margin: 0;">☁️ Demi - ผู้ช่วย AI ของ CookieCloudyDay</h1>
    <p style="color: #e0e0e0; margin: 5px 0;">สำหรับการถาม-ตอบเรื่องเมนู ราคา โปรโมชั่น และการสั่งซื้อคุกกี้</p>
</div>
""", unsafe_allow_html=True)

# Store info
st.markdown("""
<div style="background-color: #f0f8ff; padding: 12px; border-radius: 8px; margin-bottom: 20px;">
    <strong>⏰ เวลาเปิดร้าน:</strong> 10:00 - 20:00 น. <br>
    <strong>📍 ที่อยู่:</strong> CookieCloudyDay Homemade Cookies <br>
    <strong>💬 สอบถาม:</strong> เราพร้อมช่วยเหลือตั้งแต่เวลาเปิดร้าน
</div>
""", unsafe_allow_html=True)

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
    """Get response from Demi AI using Google Gemini"""
    if not hasattr(st.session_state, 'client') or st.session_state.client is None:
        return "ขออภัย! ไม่สามารถเชื่อมต่อกับ AI ได้ในตอนนี้"
    
    try:
        response = st.session_state.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            system_instruction=SYSTEM_INSTRUCTION,
            config={"temperature": 0.7, "max_output_tokens": 500},
        )
        return response.text
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
        return "ขออภัย! เกิดข้อผิดพลาดในการประมวลผล"

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
    """Display order bill with consolidation"""
    if not st.session_state.orders:
        return
    
    st.markdown('<div class="bill-container">', unsafe_allow_html=True)
    st.markdown('<div class="bill-title">🧾 บิลสั่งซื้อ</div>', unsafe_allow_html=True)
    
    total_amount = 0
    
    # Display each order item
    for i, order in enumerate(st.session_state.orders, 1):
        item_total = order["price"] * order["quantity"]
        total_amount += item_total
        
        st.markdown(f"""
        <div class="bill-item">
            <span>{i}. {order['menu']} × {order['quantity']} ชิ้น</span>
            <span>{item_total} บ.</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Display total
    st.markdown(f"""
    <div class="bill-total">
        <span>ยอดรวมทั้งสิ้น</span>
        <span>{total_amount} บาท</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Show promotion conditions
    if total_amount >= 150:
        st.markdown('<div class="promo-info">', unsafe_allow_html=True)
        st.markdown('<div class="promotion-condition">🎯 เงื่อนไขโปรโมชั่น</div>', unsafe_allow_html=True)
        
        if total_amount >= 500:
            st.markdown("✨ **ซื้อครบ 500 บาท**")
            st.markdown("- ได้รับส่วนลด 15%")
            st.markdown("- Cookie Fortune 3 ใบ")
            st.markdown("- ของขวัญพิเศษ")
        elif total_amount >= 300:
            st.markdown("⭐ **ซื้อครบ 300 บาท**")
            st.markdown("- ได้รับส่วนลด 10%")
            st.markdown("- Cookie Fortune 2 ใบ")
        else:
            st.markdown("🎁 **ซื้อครบ 150 บาท**")
            st.markdown("- ได้รับ Cookie Fortune ฟรี 1 ใบ")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def clear_input():
    """Clear the input field"""
    st.session_state.user_input = ""

# Chat history display
st.markdown("### 💬 การสนทนากับ Demi")

chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="chat-message user-message">{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message assistant-message">{message["content"]}</div>', unsafe_allow_html=True)

# Display current bill if there are orders
if st.session_state.orders:
    st.divider()
    display_bill()
    
    # Button to clear orders
    if st.button("🗑️ ลบออเดอร์ทั้งหมด", key="clear_orders"):
        st.session_state.orders = []
        st.rerun()

st.divider()

# Input section with proper clearing
col1, col2 = st.columns([4, 1])

with col1:
    user_input = st.text_input(
        "พูดอะไรกับ Demi สิ...",
        key="user_input",
        placeholder="เช่น: เมนูแนะนำ?, คุกกี้เนยสด ราคาเท่าไหร่?, เอา 2 ชิ้น"
    )

with col2:
    send_button = st.button("📤 ส่ง", key="send_button")

# Process user input
if send_button and user_input:
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Check for order in message
    order = parse_order_from_message(user_input)
    if order:
        st.session_state.orders.append(order)
        order_confirmation = f"✅ บันทึกออเดอร์: {order['menu']} × {order['quantity']} ชิ้น ราคา {order['price'] * order['quantity']} บาท"
    else:
        order_confirmation = ""
    
    # Get AI response
    with st.spinner("🤔 Demi กำลังคิด..."):
        ai_response = get_demi_response(user_input)
    
    # Combine responses
    full_response = order_confirmation + "\n\n" + ai_response if order_confirmation else ai_response
    
    # Add AI response to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response
    })
    
    # Clear input by resetting session state
    st.session_state.user_input = ""
    
    # Rerun to show updated chat and clear input
    st.rerun()

# Footer
st.markdown("""
---
<div style="text-align: center; padding: 12px; color: #666;">
    <small>Demi AI Assistant for CookieCloudyDay | Powered by Google Gemini</small>
</div>
""", unsafe_allow_html=True)
