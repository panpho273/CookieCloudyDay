import json
import random
from pathlib import Path
import streamlit as st

TAROT_FILE = Path(__file__).parent / "tarot_cards.json"

@st.cache_data
def load_tarot_cards():
    with open(TAROT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def draw_tarot_card():
    return random.choice(load_tarot_cards())

@st.dialog("🔮 Lucky Cookie Tarot")
def lucky_cookie_tarot_dialog():
    st.markdown(
        """
        <style>
        .tarot-box {
            text-align: center;
            padding: 8px 4px 2px;
        }
        .tarot-card {
            width: 190px;
            height: 280px;
            margin: 0 auto 18px;
            border-radius: 24px;
            background:
              radial-gradient(circle at 50% 25%, rgba(255,255,255,.95), transparent 30%),
              linear-gradient(145deg, #fff7ef, #f1c7bd);
            border: 1px solid rgba(139, 83, 52, .18);
            box-shadow: 0 24px 60px rgba(80, 45, 30, .25);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            animation: flipTarot .8s ease both;
            transform-style: preserve-3d;
        }
        .tarot-emoji {
            font-size: 60px;
            margin-bottom: 14px;
            filter: drop-shadow(0 10px 14px rgba(80,45,30,.18));
        }
        .tarot-name {
            font-size: 24px;
            font-weight: 900;
            color: #3b241b;
        }
        .tarot-sub {
            margin-top: 8px;
            color: #8a5a40;
            font-weight: 700;
        }
        @keyframes flipTarot {
            0% { transform: rotateY(90deg) scale(.88); opacity: 0; }
            55% { transform: rotateY(-12deg) scale(1.03); opacity: 1; }
            100% { transform: rotateY(0deg) scale(1); opacity: 1; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "lucky_tarot_card" not in st.session_state:
        st.session_state["lucky_tarot_card"] = draw_tarot_card()

    card = st.session_state["lucky_tarot_card"]

    st.markdown(
        f"""
        <div class="tarot-box">
          <div class="tarot-card">
            <div class="tarot-emoji">{card["emoji"]}</div>
            <div class="tarot-name">{card["name"]}</div>
            <div class="tarot-sub">Cookie Fortune Card</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### คำทำนายของคุณ")
    st.write(card["meaning"])
    st.success(f"เมนูที่เหมาะกับวันนี้: {card['cookie']}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 สุ่มไพ่ใหม่", use_container_width=True):
            st.session_state["lucky_tarot_card"] = draw_tarot_card()
            st.rerun()
    with col2:
        if st.button("ปิด", use_container_width=True):
            st.session_state["show_lucky_tarot"] = False
            st.rerun()

def render_lucky_cookie_tarot():
    if not st.session_state.get("lucky_cookie_available"):
        return

    st.markdown("---")
    st.success(
        "🎁 ออเดอร์นี้เข้าโปร Lucky Cookie Tarot: ซื้อครบ 3 ชิ้น และยอดรวม 150 บาทขึ้นไป"
    )

    if st.button("🔮 รับไพ่คุกกี้และคำทำนาย", use_container_width=True):
        st.session_state["show_lucky_tarot"] = True
        st.session_state["lucky_tarot_card"] = draw_tarot_card()

    if st.session_state.get("show_lucky_tarot"):
        lucky_cookie_tarot_dialog()
