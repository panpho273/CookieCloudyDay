import json
import random
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


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

    # กัน dialog ถูกเปิดซ้ำใน run เดียวกัน
    if st.session_state.get("_lucky_tarot_dialog_opened"):
        return

    st.session_state["_lucky_tarot_dialog_opened"] = True

    if "lucky_tarot_card" not in st.session_state:
        st.session_state["lucky_tarot_card"] = draw_random_card()

    @st.dialog("🔮 Lucky Cookie Tarot")
    def lucky_tarot_dialog():
        card = st.session_state["lucky_tarot_card"]

        components.html(
            f"""
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Mitr:wght@300;400;500;600;700&display=swap');

                body {{
                    margin: 0;
                    font-family: 'Mitr', sans-serif;
                    color: #4a2e2a;
                    background: transparent;
                }}

                .tarot-wrap {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 16px;
                    padding: 4px 0 10px;
                }}

                .tarot-card {{
                    width: 190px;
                    min-height: 250px;
                    border-radius: 26px;
                    background: linear-gradient(180deg, #ffe8df 0%, #ffd7cb 100%);
                    border: 1px solid rgba(168, 112, 91, 0.22);
                    box-shadow: 0 18px 45px rgba(92, 52, 43, 0.14);
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    text-align: center;
                    padding: 18px;
                }}

                .tarot-cookie {{
                    font-size: 46px;
                    margin-bottom: 22px;
                }}

                .tarot-name {{
                    font-size: 24px;
                    font-weight: 700;
                    line-height: 1.25;
                    margin-bottom: 16px;
                }}

                .tarot-sub {{
                    font-size: 14px;
                    font-weight: 600;
                    opacity: 0.72;
                }}

                .tarot-section-title {{
                    width: 100%;
                    max-width: 430px;
                    font-size: 18px;
                    font-weight: 700;
                    text-align: left;
                    margin-top: 2px;
                }}

                .tarot-meaning {{
                    width: 100%;
                    max-width: 430px;
                    font-size: 15px;
                    line-height: 1.8;
                    text-align: left;
                }}

                .tarot-keyword {{
                    width: 100%;
                    max-width: 430px;
                    padding: 14px 16px;
                    border-radius: 12px;
                    background: #d9ecff;
                    font-size: 14px;
                    line-height: 1.7;
                    font-weight: 500;
                    box-sizing: border-box;
                }}

                .tarot-promo {{
                    width: 100%;
                    max-width: 430px;
                    padding: 14px 16px;
                    border-radius: 12px;
                    background: #dcf8e8;
                    font-size: 14px;
                    line-height: 1.7;
                    font-weight: 500;
                    box-sizing: border-box;
                }}
            </style>

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
            height=570,
            scrolling=False,
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("สุ่มไพ่ใหม่", use_container_width=True):
                st.session_state["lucky_tarot_card"] = draw_random_card()
                st.session_state.pop("_lucky_tarot_dialog_opened", None)
                st.rerun()

        with col2:
            if st.button("จบออเดอร์และเริ่มแชทใหม่", use_container_width=True):
                st.session_state["show_lucky_tarot"] = False
                st.session_state.pop("lucky_tarot_card", None)
                st.session_state.pop("lucky_cookie_promo", None)
                st.session_state.pop("_lucky_tarot_dialog_opened", None)
                st.rerun()

    lucky_tarot_dialog()
