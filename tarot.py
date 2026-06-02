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
                "id": card.get("id"),
                "type": card.get("type", ""),
                "suit": card.get("suit", ""),
                "name": str(name),
                "emoji": card.get("emoji", "🍪"),
                "cookie": card.get("cookie", "คุกกี้ช็อกโกแลตชิพ"),
                "cookie_price": card.get("cookie_price", 0),
                "meaning": str(meaning),
                "keyword": str(keyword),
                "freebie_text": card.get("freebie_text", ""),
            })

    return result


def draw_random_card():
    cards = load_tarot_cards()

    if not cards:
        return {
            "id": "fallback",
            "name": "Lucky Cookie",
            "cookie": "คุกกี้ช็อกโกแลตชิพ",
            "cookie_price": 45,
            "meaning": "วันนี้เหมาะกับการเริ่มต้นสิ่งเล็ก ๆ ด้วยความตั้งใจดี",
            "keyword": "ความสดใส การเริ่มต้นเล็ก ๆ",
            "freebie_text": "โปรเปิดร้าน: รับฟรี คุกกี้ช็อกโกแลตชิพ 1 ชิ้น",
        }

    def card_key(card):
        key = card.get("id")
        if key not in [None, ""]:
            return f"id:{key}"
        return "name:" + str(card.get("name", "")).strip()

    if "lucky_tarot_draw_history" not in st.session_state:
        st.session_state["lucky_tarot_draw_history"] = []

    history = list(st.session_state.get("lucky_tarot_draw_history", []))
    last_key = st.session_state.get("last_lucky_tarot_key", "")

    all_keys = [card_key(card) for card in cards]

    # ถ้าสุ่มจนเกือบครบแล้ว ให้เริ่มรอบใหม่ แต่ยังกันใบล่าสุดไว้
    if len(set(history)) >= max(len(all_keys) - 1, 1):
        history = []
        st.session_state["lucky_tarot_draw_history"] = []

    available_cards = [
        card for card in cards
        if card_key(card) not in history
        and card_key(card) != last_key
    ]

    # fallback กรณีเหลือใบเดียวจริง ๆ
    if not available_cards:
        available_cards = [
            card for card in cards
            if card_key(card) != last_key
        ] or cards

    card = random.SystemRandom().choice(available_cards)
    key = card_key(card)

    st.session_state["last_lucky_tarot_key"] = key
    st.session_state["lucky_tarot_draw_history"] = history + [key]

    return card



# ===== CCD TAROT ORDER SUMMARY START =====
def _ccd_render_tarot_order_summary():
    promo = st.session_state.get("lucky_cookie_promo", {}) or {}

    menu_name = (
        promo.get("ordered_menu")
        or promo.get("menu")
        or promo.get("menu_name")
        or promo.get("name")
        or ""
    )

    quantity = (
        promo.get("quantity")
        or promo.get("qty")
        or ""
    )

    total = (
        promo.get("total")
        or promo.get("saved_total")
        or ""
    )

    if not menu_name and not quantity and not total:
        return

    try:
        total_text = f"{int(total):,} บาท"
    except Exception:
        total_text = f"{total} บาท" if total else "-"

    st.markdown(
        f"""
        <div class="tarot-order-summary">
            <div class="tarot-order-title">🍪 สรุปออเดอร์ของคุณ</div>
            <div class="tarot-order-row">
                <span>เมนู</span>
                <strong>{menu_name or "-"}</strong>
            </div>
            <div class="tarot-order-row">
                <span>จำนวน</span>
                <strong>{quantity or "-"} ชิ้น</strong>
            </div>
            <div class="tarot-order-total">
                <span>รวมทั้งหมด</span>
                <strong>{total_text}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
# ===== CCD TAROT ORDER SUMMARY END =====


def render_lucky_cookie_tarot():
    _ccd_render_tarot_order_summary()
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
                promo["freebie_cookie"] = new_card.get("cookie", "คุกกี้ช็อกโกแลตชิพ")
                promo["freebie_text"] = new_card.get("freebie_text", "")
                st.session_state["lucky_cookie_promo"] = promo
                
                st.rerun()

        with col2:
            if st.button("เริ่มแชทใหม่", use_container_width=True):
                st.session_state["show_lucky_tarot"] = False
                st.session_state.pop("lucky_tarot_card", None)
                st.session_state.pop("lucky_cookie_promo", None)
                st.session_state.pop("lucky_tarot_draw_history", None)
                st.session_state.pop("last_lucky_tarot_key", None)
                st.session_state["messages"] = []
                st.rerun()

    lucky_tarot_dialog()


