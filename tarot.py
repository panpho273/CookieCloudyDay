import json
import random
from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
TAROT_FILE = BASE_DIR / "tarot_cards.json"


def load_tarot_cards():
    if not TAROT_FILE.exists():
        return []

    with open(TAROT_FILE, "r", encoding="utf-8") as f:
        cards = json.load(f)

    if isinstance(cards, dict):
        cards = cards.get("cards", [])

    if not isinstance(cards, list):
        return []

    result = []

    for card in cards:
        if not isinstance(card, dict):
            continue

        name = (
            card.get("name")
            or card.get("title")
            or card.get("card")
            or card.get("thai_name")
            or ""
        )

        meaning = (
            card.get("meaning")
            or card.get("message")
            or card.get("description")
            or card.get("fortune")
            or ""
        )

        keyword = (
            card.get("keyword")
            or card.get("keywords")
            or card.get("theme")
            or ""
        )

        if name:
            result.append({
                "name": str(name),
                "meaning": str(meaning),
                "keyword": str(keyword),
            })

    return result


def draw_random_card():
    cards = load_tarot_cards()

    if not cards:
        return {
            "name": "Lucky Cookie",
            "meaning": "วันนี้เหมาะกับการเริ่มต้นสิ่งเล็ก ๆ ด้วยความตั้งใจดี",
            "keyword": "ความสดใส การเริ่มต้นเล็ก ๆ",
        }

    last_name = st.session_state.get("last_lucky_tarot_name")

    if len(cards) > 1 and last_name:
        choices = [card for card in cards if card.get("name") != last_name]
        if choices:
            cards = choices

    card = random.SystemRandom().choice(cards)
    st.session_state["last_lucky_tarot_name"] = card.get("name")

    return card


def render_lucky_cookie_tarot():
    if (
        not st.session_state.get("show_lucky_tarot")
        or not st.session_state.get("lucky_cookie_promo")
    ):
        return

    # ถ้าเคยค้างเป็น default เก่า ให้สุ่มใหม่จากไฟล์จริง
    old_card = st.session_state.get("lucky_tarot_card")
    if old_card and old_card.get("name") in ["The Choco Chip", "Lucky Cookie"]:
        st.session_state.pop("lucky_tarot_card", None)

    if "lucky_tarot_card" not in st.session_state:
        st.session_state["lucky_tarot_card"] = draw_random_card()

    def lucky_tarot_dialog():
        card = st.session_state["lucky_tarot_card"]

        st.markdown(
            """
            <style>
            div[role="dialog"] {
                border-radius: 28px !important;
            }

            div[role="dialog"] button[aria-label="Close"],
            div[role="dialog"] button[title="Close"] {
                display: none !important;
            }

            .tarot-card-box {
                width: 220px;
                min-height: 280px;
                margin: 0 auto 22px auto;
                padding: 22px 18px;
                border-radius: 28px;
                background: linear-gradient(180deg, #ffe8df 0%, #ffd8cd 100%);
                border: 1px solid rgba(168, 112, 91, 0.22);
                box-shadow:
                    0 18px 42px rgba(91, 51, 42, 0.16),
                    0 0 32px rgba(255, 198, 185, 0.34),
                    inset 0 1px 0 rgba(255,255,255,0.45);
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
            }

            .tarot-cookie-icon {
                font-size: 46px;
                margin-bottom: 24px;
            }

            .tarot-card-name {
                font-size: 24px;
                font-weight: 700;
                line-height: 1.25;
                margin-bottom: 14px;
                color: #4a2e2a;
                word-break: break-word;
            }

            .tarot-card-sub {
                font-size: 14px;
                font-weight: 600;
                color: rgba(74, 46, 42, 0.68);
            }

            div[role="dialog"] div.stButton > button {
                min-height: 54px !important;
                border-radius: 999px !important;
                border: none !important;
                background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 55%, #7547d8 100%) !important;
                color: #4a2e2a !important;
                font-family: 'Mitr', sans-serif !important;
                font-size: 16px !important;
                font-weight: 700 !important;
                box-shadow:
                    0 14px 28px rgba(124, 58, 237, 0.26),
                    0 0 20px rgba(167, 139, 250, 0.26),
                    inset 0 1px 0 rgba(255,255,255,0.30) !important;
            }

            div[role="dialog"] div.stButton > button:hover {
                transform: translateY(-1px) !important;
                box-shadow:
                    0 18px 34px rgba(124, 58, 237, 0.32),
                    0 0 24px rgba(167, 139, 250, 0.34),
                    inset 0 1px 0 rgba(255,255,255,0.34) !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
<div class="tarot-card-box">
    <div class="tarot-cookie-icon">🍪</div>
    <div class="tarot-card-name">{card.get("name", "Lucky Cookie")}</div>
    <div class="tarot-card-sub">Cookie Fortune Card</div>
</div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### คำทำนายของคุณ")
        st.write(card.get("meaning", ""))

        keyword = card.get("keyword", "")
        if keyword:
            st.info(f"ความหมายหลักของไพ่: {keyword}")

        promo = st.session_state.get("lucky_cookie_promo", {})
        freebie_cookie = promo.get("freebie_cookie", "คุกกี้ช็อกโกแลตชิพ")
        
        st.success(
            f"🎁 โปรเปิดร้าน: ออเดอร์ครบ 150 บาทขึ้นไป\n"
            f"รับฟรี **{freebie_cookie}** 1 ชิ้น ตามไพ่ที่ดึงได้"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("สุ่มไพ่ใหม่", use_container_width=True):
                new_card = draw_random_card()
                st.session_state["lucky_tarot_card"] = new_card
                
                promo = st.session_state.get("lucky_cookie_promo", {})
                promo["card_name"] = new_card.get("name")
                promo["freebie_cookie"] = new_card.get("cookie")
                promo["freebie_text"] = new_card.get("freebie_text")
                st.session_state["lucky_cookie_promo"] = promo
                
                st.rerun()

        with col2:
            if st.button("ไม่รับโปร / เริ่มแชทใหม่", use_container_width=True):
                st.session_state["show_lucky_tarot"] = False
                st.session_state.pop("lucky_tarot_card", None)
                st.session_state.pop("lucky_cookie_promo", None)
                st.session_state["messages"] = []
                st.rerun()

    lucky_tarot_dialog()
