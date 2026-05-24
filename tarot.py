import json
import random
from pathlib import Path
import streamlit as st

TAROT_FILE = Path(__file__).parent / "tarot_cards.json"

FALLBACK_TAROT_CARDS = [
    {
        "name": "The Choco Chip",
        "emoji": "🍪",
        "cookie": "คุกกี้ช็อกโกแลตชิพ",
        "cookie_price": 45,
        "keyword": "ความสดใส การเริ่มต้นเล็ก ๆ",
        "meaning": "วันนี้เหมาะกับการเริ่มต้นอะไรเล็ก ๆ ที่ทำให้ใจฟู ความพยายามเล็กน้อยจะพาไปสู่เรื่องดี ๆ",
    }
]

@st.cache_data(ttl=300)
def load_tarot_cards():
    if TAROT_FILE.exists():
        try:
            with open(TAROT_FILE, "r", encoding="utf-8") as f:
                cards = json.load(f)
            if isinstance(cards, list) and cards:
                return cards
        except Exception:
            pass

    return FALLBACK_TAROT_CARDS

def draw_tarot_card():
    return random.choice(load_tarot_cards())

def reset_order_chat():
    keys_to_remove = [
        "lucky_cookie_promo",
        "show_lucky_tarot",
        "lucky_tarot_card",
        "last_order_total",
        "last_order_quantity",
        "last_order_menu",
    ]

    for key in keys_to_remove:
        st.session_state.pop(key, None)

    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "สวัสดีค่ะ Demi พร้อมรับออเดอร์ใหม่แล้วค่ะ 🍪\n\n"
            "ลูกค้าพิมพ์ว่า “สั่งของ” หรือพิมพ์ชื่อเมนูพร้อมจำนวนได้เลยนะคะ"
        )
    })

@st.dialog("🔮 Lucky Cookie Tarot")
def lucky_cookie_tarot_dialog():
    if "lucky_tarot_card" not in st.session_state:
        st.session_state["lucky_tarot_card"] = draw_tarot_card()

    card = st.session_state["lucky_tarot_card"]

    st.markdown(
        f"""
        <style>
        .tarot-card {{
            width: 190px;
            height: 280px;
            margin: 0 auto 18px;
            border-radius: 26px;
            background: linear-gradient(145deg, #fff7ef, #f1c7bd);
            border: 1px solid rgba(139, 83, 52, .18);
            box-shadow: 0 24px 60px rgba(80, 45, 30, .25);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            animation: flipTarot .8s ease both;
        }}
        .tarot-emoji {{
            font-size: 62px;
            margin-bottom: 16px;
        }}
        .tarot-name {{
            font-size: 25px;
            font-weight: 900;
            color: #3b241b;
            text-align: center;
        }}
        .tarot-label {{
            margin-top: 8px;
            color: #8a5a40;
            font-weight: 700;
        }}
        @keyframes flipTarot {{
            0% {{ transform: rotateY(90deg) scale(.88); opacity: 0; }}
            55% {{ transform: rotateY(-12deg) scale(1.03); opacity: 1; }}
            100% {{ transform: rotateY(0deg) scale(1); opacity: 1; }}
        }}
        </style>

        <div class="tarot-card">
            <div class="tarot-emoji">{card.get("emoji", "🔮")}</div>
            <div class="tarot-name">{card.get("name", "Lucky Cookie Tarot")}</div>
            <div class="tarot-label">Cookie Fortune Card</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### คำทำนายของคุณ")
    st.write(card.get("meaning", "วันนี้เหมาะกับการให้รางวัลตัวเองด้วยคุกกี้น่ารัก ๆ"))

    st.info(f"ความหมายหลักของไพ่: {card.get('keyword', '-')}")
    st.success(
        f"🎁 โปรเปิดร้าน: ออเดอร์ครบ 150 บาทขึ้นไป "
        f"รับฟรี {card.get('cookie', 'คุกกี้พิเศษของร้าน')} 1 ชิ้น ตามไพ่ที่สุ่มได้"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 สุ่มไพ่ใหม่", key="btn_redraw_lucky_cookie_tarot", use_container_width=True):
            st.session_state["lucky_tarot_card"] = draw_tarot_card()
            st.rerun()

    with col2:
        if st.button("✅ จบออเดอร์และเริ่มแชทใหม่", key="btn_finish_order_new_chat", use_container_width=True):
            reset_order_chat()
            st.rerun()

def render_lucky_cookie_tarot():
    promo = st.session_state.get("lucky_cookie_promo")

    if not promo:
        return

    st.markdown("---")
    st.success(
        f"🎁 ออเดอร์นี้เข้าโปร Lucky Cookie Tarot แล้วค่ะ "
        f"ครบ {promo.get('quantity')} ชิ้น ยอดรวม {promo.get('total')} บาท"
    )

    if st.button("🔮 รับไพ่คุกกี้และคำทำนาย", key="btn_draw_lucky_cookie_tarot", use_container_width=True):
        st.session_state["show_lucky_tarot"] = True
        st.session_state["lucky_tarot_card"] = draw_tarot_card()

    if st.button("✅ จบออเดอร์ / เริ่มแชทใหม่", use_container_width=True):
        reset_order_chat()
        st.rerun()

    if st.session_state.get("show_lucky_tarot"):
        lucky_cookie_tarot_dialog()
