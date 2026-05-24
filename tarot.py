import json
import random
from pathlib import Path

import streamlit as st


TAROT_FILE_CANDIDATES = [
    Path("tarot_cards.json"),
    Path("tarot_cards.json.json"),
    Path("tarot_cards_data.json"),
    Path("tarot_menu_data.json"),
    Path("tarot_cards_th.json"),
]


def find_tarot_file():
    for file_path in TAROT_FILE_CANDIDATES:
        if file_path.exists():
            return file_path
    return None


def load_tarot_cards():
    tarot_file = find_tarot_file()

    if tarot_file is None:
        return []

    with open(tarot_file, "r", encoding="utf-8") as f:
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

    # ถ้าเคยค้างเป็นไพ่ default ให้สุ่มใหม่จากไฟล์ 78 ใบ
    old_card = st.session_state.get("lucky_tarot_card")
    if old_card and old_card.get("name") == "The Choco Chip":
        st.session_state.pop("lucky_tarot_card", None)

    if "lucky_tarot_card" not in st.session_state:
        st.session_state["lucky_tarot_card"] = draw_random_card()

    @st.dialog("🔮 Lucky Cookie Tarot")
    def lucky_tarot_dialog():
        card = st.session_state["lucky_tarot_card"]

        # CSS + เฉพาะการ์ดใช้ HTML
        st.markdown(
            f"""
<style>
.tarot-card {{
    width: 210px;
    min-height: 270px;
    margin: 0 auto 22px auto;
    padding: 22px 18px;
    border-radius: 28px;
    background: linear-gradient(180deg, #ffe8df 0%, #ffd8cd 100%);
    border: 1px solid rgba(168, 112, 91, 0.22);
    box-shadow:
        0 18px 42px rgba(91, 51, 42, 0.14),
        0 0 30px rgba(255, 206, 190, 0.32),
        inset 0 1px 0 rgba(255,255,255,0.45);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
}}

.tarot-cookie {{
    font-size: 46px;
    margin-bottom: 24px;
}}

.tarot-name {{
    font-size: 24px;
    font-weight: 700;
    line-height: 1.25;
    margin-bottom: 14px;
    color: #4a2e2a;
    word-break: break-word;
}}

.tarot-sub {{
    font-size: 14px;
    font-weight: 600;
    color: rgba(74, 46, 42, 0.68);
}}

div[role="dialog"] div.stButton > button {{
    min-height: 54px !important;
    border-radius: 999px !important;
    border: none !important;
    background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 55%, #7547d8 100%) !important;
    color: #4a2e2a !important;
    font-family: 'Mitr', sans-serif !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    box-shadow:
        0 14px 28px rgba(124, 58, 237, 0.24),
        0 0 18px rgba(167, 139, 250, 0.22),
        inset 0 1px 0 rgba(255,255,255,0.28) !important;
}}

div[role="dialog"] div.stButton > button:hover {{
    transform: translateY(-1px) !important;
    box-shadow:
        0 18px 34px rgba(124, 58, 237, 0.30),
        0 0 22px rgba(167, 139, 250, 0.32),
        inset 0 1px 0 rgba(255,255,255,0.32) !important;
}}
</style>

<div class="tarot-card">
    <div class="tarot-cookie">🍪</div>
    <div class="tarot-name">{card.get("name", "Lucky Cookie")}</div>
    <div class="tarot-sub">Cookie Fortune Card</div>
</div>
""",
            unsafe_allow_html=True,
        )

        # ตรงนี้ใช้ Streamlit ปกติ ไม่ใช้ HTML แล้ว จะไม่ขึ้น <div> ดิบอีก
        st.markdown("### คำทำนายของคุณ")
        st.markdown(card.get("meaning", ""))

        st.info(f"ความหมายหลักของไพ่: {card.get('keyword', '')}")

        st.success(
            "โปรเปิดร้าน: ออเดอร์ครบ 150 บาทขึ้นไป "
            "รับฟรีคุกกี้ช็อกโกแลตชิพ 1 ชิ้น ตามไพ่ที่สุ่มได้"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("สุ่มไพ่ใหม่", use_container_width=True):
                st.session_state["lucky_tarot_card"] = draw_random_card()
                st.rerun()

        with col2:
            if st.button("จบออเดอร์และเริ่มแชทใหม่", use_container_width=True):
                st.session_state["show_lucky_tarot"] = False
                st.session_state.pop("lucky_tarot_card", None)
                st.session_state.pop("lucky_cookie_promo", None)
                st.rerun()

    lucky_tarot_dialog()



