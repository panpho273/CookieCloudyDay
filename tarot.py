import json
import random
from pathlib import Path

import streamlit as st


TAROT_FILE = Path("tarot_cards.json")


def load_tarot_cards():
    if not TAROT_FILE.exists():
        return []

    with open(TAROT_FILE, "r", encoding="utf-8") as f:
        cards = json.load(f)

    if isinstance(cards, dict):
        # รองรับกรณีไฟล์เป็น {"cards": [...]}
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
            or "Lucky Cookie"
        )

        meaning = (
            card.get("meaning")
            or card.get("message")
            or card.get("description")
            or card.get("fortune")
            or "วันนี้เหมาะกับการเริ่มต้นสิ่งเล็ก ๆ ด้วยใจดี ๆ"
        )

        keyword = (
            card.get("keyword")
            or card.get("keywords")
            or card.get("theme")
            or "ความสดใส การเริ่มต้นเล็ก ๆ"
        )

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
            "name": "The Choco Chip",
            "meaning": "วันนี้เหมาะกับการเริ่มต้นอะไรเล็ก ๆ ที่ทำให้ใจฟู ความพยายามเล็กน้อยจะพาไปสู่เรื่องดี ๆ",
            "keyword": "ความสดใส การเริ่มต้นเล็ก ๆ",
        }

    last_name = st.session_state.get("last_lucky_tarot_name")

    # กันสุ่มได้ใบเดิมติดกัน ถ้ามีมากกว่า 1 ใบ
    if len(cards) > 1 and last_name:
        choices = [card for card in cards if card.get("name") != last_name]
        if choices:
            cards = choices

    card = random.SystemRandom().choice(cards)
    st.session_state["last_lucky_tarot_name"] = card.get("name")

    return card


def render_lucky_cookie_tarot():
    if not st.session_state.get("show_lucky_tarot"):
        return

    if "lucky_tarot_card" not in st.session_state:
        st.session_state["lucky_tarot_card"] = draw_random_card()

    @st.dialog("🔮 Lucky Cookie Tarot")
    def lucky_tarot_dialog():
        card = st.session_state["lucky_tarot_card"]

        st.markdown(
            f"""
            <div class="tarot-wrap">
                <div class="tarot-card">
                    <div class="tarot-cookie">🍪</div>
                    <div class="tarot-name">{card.get("name", "Lucky Cookie")}</div>
                    <div class="tarot-sub">Cookie Fortune Card</div>
                </div>

                <div class="tarot-section-title">คำทำนายของคุณ</div>
                <div class="tarot-meaning">
                    {card.get("meaning", "")}
                </div>

                <div class="tarot-keyword">
                    ความหมายหลักของไพ่: {card.get("keyword", "")}
                </div>

                <div class="tarot-promo">
                    🎁 โปรเปิดร้าน: ออเดอร์ครบ 150 บาทขึ้นไป รับฟรีคุกกี้ช็อกโกแลตชิพ 1 ชิ้น ตามไพ่ที่สุ่มได้
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 สุ่มไพ่ใหม่", use_container_width=True):
                st.session_state["lucky_tarot_card"] = draw_random_card()
                st.rerun()

        with col2:
            if st.button("✅ จบออเดอร์และเริ่มแชทใหม่", use_container_width=True):
                st.session_state["show_lucky_tarot"] = False
                st.session_state.pop("lucky_tarot_card", None)
                st.session_state.pop("lucky_cookie_promo", None)
                st.rerun()

    lucky_tarot_dialog()
