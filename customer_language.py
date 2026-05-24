import json
import re
from pathlib import Path


THAI_NUMBERS_MAP = str.maketrans(
    "๐๑๒๓๔๕๖๗๘๙",
    "0123456789",
)

THAI_WORD_NUMBERS = {
    "หนึ่ง": 1,
    "นึง": 1,
    "อันนึง": 1,
    "สอง": 2,
    "คู่": 2,
    "สาม": 3,
    "สี่": 4,
    "ห้า": 5,
    "หก": 6,
    "เจ็ด": 7,
    "แปด": 8,
    "เก้า": 9,
    "สิบ": 10,
}

ORDER_TERMS = [
    "สั่ง",
    "ซื้อ",
    "เอา",
    "ขอ",
    "รับ",
    "จัดมา",
    "จัดให้",
    "เอาอันนี้",
    "เอาตัวนี้",
    "อยากได้",
    "อยากสั่ง",
    "ขอรับ",
]

QUESTION_TERMS = [
    "กี่บาท",
    "ราคา",
    "ราคาเท่าไหร่",
    "กี่โมง",
    "เวลาเปิด",
    "ร้านเปิด",
    "เปิดกี่โมง",
    "มีอะไรขาย",
    "ขายอะไร",
    "เมนูอะไร",
    "โปรอะไร",
    "โปรโมชั่น",
]

HOT_MENU_TERMS = [
    "เมนูขายดี",
    "ขายดี",
    "เมนูยอดฮิต",
    "ยอดฮิต",
    "ยอดนิยม",
    "เมนูแนะนำ",
    "แนะนำเมนู",
    "เมนูไหนขายดี",
    "อะไรขายดี",
    "ตัวไหนดี",
    "อันไหนดี",
    "ตัวไหนอร่อย",
    "อะไรอร่อย",
    "แนะนำหน่อย",
    "อยากลองเมนูฮิต",
]

MENU_NUMBER_TERMS = [
    "เมนู",
    "เมนูที่",
    "เบอร์",
    "อันดับ",
    "อันดับที่",
    "ตัวที่",
    "อันที่",
]

FIRST_MENU_TERMS = [
    "ตัวแรก",
    "อันแรก",
    "เมนูแรก",
    "อันดับแรก",
    "ตัวขายดี",
    "เมนูขายดีสุด",
    "ขายดีสุด",
    "ตัวท็อป",
    "ตัวฮิต",
]

FRIENDLY_OPENING = "ได้เลยค่าา 🥹🍪"

FLAVOR_HINTS = {
    "ช็อก": "ถ้าชอบสายช็อกโกแลต Demi แนะนำดูตัวช็อกโกแลตชิพ ดับเบิลช็อก หรือโกโก้เฮเซลนัทเลยค่ะ เข้ม ๆ ฟิน ๆ",
    "โกโก้": "ถ้าชอบโกโก้ เข้ม ๆ หอม ๆ Demi แนะนำโกโก้เฮเซลนัทหรือโกโก้ครันช์ค่ะ",
    "หวานน้อย": "ถ้าชอบหวานน้อย แนะนำแนวข้าวโอ๊ต วานิลลา หรือคอร์นเฟลกคาราเมลค่ะ กินง่าย ไม่หนักมาก",
    "กรอบ": "ถ้าชอบกรอบ ๆ แนะนำคอร์นเฟลกคาราเมลหรือโกโก้ครันช์เลยค่ะ",
    "นุ่ม": "ถ้าชอบนุ่ม ๆ หนึบ ๆ แนะนำบราวนี่ฟัดจ์หรือช็อกโกแลตลาวาค่ะ",
    "เปรี้ยว": "ถ้าอยากได้สดชื่น ๆ แนะนำแนวสตรอว์เบอร์รีหรือผลไม้ค่ะ",
    "พรีเมียม": "ถ้าชอบพรีเมียม ๆ แนะนำแมคคาเดเมีย พิสตาชิโอ หรือเฮเซลนัทค่ะ",
}


def normalize_thai_numbers(text: str) -> str:
    return str(text or "").translate(THAI_NUMBERS_MAP)


def normalize_text(text: str) -> str:
    text = normalize_thai_numbers(text)
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def is_general_question(text: str) -> bool:
    q = normalize_text(text)
    return any(term in q for term in QUESTION_TERMS)


def has_order_intent(text: str) -> bool:
    q = normalize_text(text)
    return any(term in q for term in ORDER_TERMS)


def is_hot_menu_question(text: str) -> bool:
    q = normalize_text(text)
    return any(term in q for term in HOT_MENU_TERMS)


def is_order_start(text: str) -> bool:
    q = normalize_text(text)
    return q in ["ซื้อ", "สั่ง", "สั่งซื้อ", "ออเดอร์", "order"]


def detect_flavor_preference(text: str):
    q = normalize_text(text)
    for keyword, reply in FLAVOR_HINTS.items():
        if keyword in q:
            return keyword, reply
    return None


def build_flavor_reply(preference):
    if not preference:
        return None

    _, reply = preference

    return (
        f"{FRIENDLY_OPENING}\n\n"
        f"{reply}\n\n"
        "ถ้าจะสั่ง พิมพ์ชื่อเมนูพร้อมจำนวนได้เลยนะคะ เช่น "
        "“เอาคุกกี้โกโก้เฮเซลนัท 2 ชิ้น”"
    )


def load_menu_prices_from_json(file_path="shop_menu.json"):
    menu_prices = {}

    possible_paths = [
        Path(file_path),
        Path.cwd() / file_path,
        Path(__file__).resolve().parent / file_path,
    ]

    for path in possible_paths:
        if not path.exists():
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                menus = json.load(f)

            for item in menus:
                if not isinstance(item, dict):
                    continue

                name = item.get("name") or item.get("menu") or item.get("title")
                price = item.get("price") or item.get("cookie_price") or 0

                if name:
                    menu_prices[str(name)] = int(price)

            if menu_prices:
                return menu_prices

        except Exception:
            continue

    return menu_prices


def clean_for_match(value: str) -> str:
    value = normalize_text(value)
    value = value.replace("คุกกี้", "")
    value = value.replace(" ", "")
    value = value.replace("-", "")
    value = value.replace("_", "")

    removable_words = [
        "ชิ้น",
        "อัน",
        "กล่อง",
        "จำนวน",
        "เอา",
        "รับ",
        "ซื้อ",
        "สั่ง",
        "ขอ",
        "อยากได้",
        "อยากสั่ง",
        "จัดมา",
        "จัดให้",
        "หน่อย",
        "ค่ะ",
        "คะ",
        "ครับ",
        "จ้า",
        "ค่า",
    ]

    for word in removable_words:
        value = value.replace(word, "")

    value = re.sub(r"\d+", "", value)

    return value.strip()


def extract_quantity(text: str, menu_number=None):
    q = normalize_text(text)

    # ตัวเลขที่มีหน่วย เช่น 3 ชิ้น
    match = re.search(r"(\d+)\s*(ชิ้น|อัน|กล่อง)", q)
    if match:
        return int(match.group(1))

    # คำไทยที่มีหน่วย เช่น สามชิ้น / สาม ชิ้น
    for word, number in THAI_WORD_NUMBERS.items():
        pattern = rf"{word}\s*(ชิ้น|อัน|กล่อง)"
        if re.search(pattern, q):
            return number

    # รูปแบบ จำนวน 3
    match = re.search(r"จำนวน\s*(\d+)", q)
    if match:
        return int(match.group(1))

    # รูปแบบ จำนวน สาม
    for word, number in THAI_WORD_NUMBERS.items():
        if f"จำนวน {word}" in q or f"จำนวน{word}" in q:
            return number

    # ถ้ามีเลขหลายตัว เช่น รับเมนู 1 จำนวน 3 ชิ้น ให้เอาเลขตัวท้ายเป็นจำนวน
    numbers = [int(n) for n in re.findall(r"\d+", q)]
    if len(numbers) >= 2:
        return numbers[-1]

    # ถ้ามีเลขเดียว แต่เลขนั้นเป็นเลขเมนู ให้ยังไม่ถือว่าเป็นจำนวน
    if len(numbers) == 1 and menu_number and numbers[0] == int(menu_number):
        return None

    # ถ้ามีเลขเดียว และมีเจตนาสั่ง เช่น เอาช็อกโกแลต 2
    if len(numbers) == 1 and has_order_intent(q):
        return numbers[0]

    return None


def extract_menu_number(text: str):
    q = normalize_text(text)

    for phrase in FIRST_MENU_TERMS:
        if phrase in q:
            return "1"

    patterns = [
        r"(?:เมนูที่|เมนู|เบอร์|อันดับที่|อันดับ|ตัวที่|อันที่)\s*(\d+)",
        r"(?:รับ|เอา|ขอ)\s*(?:เมนู|เบอร์|อันดับ|ตัว)\s*(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            return str(int(match.group(1)))

    return None


def find_menu_by_name(text: str, menu_prices: dict):
    cleaned_message = clean_for_match(text)

    if not cleaned_message:
        return None, 0

    # จับแบบตรงชื่อเต็มก่อน
    normalized_message_no_space = normalize_text(text).replace(" ", "")

    for menu_name, price in sorted(menu_prices.items(), key=lambda item: -len(item[0])):
        menu_full = normalize_text(menu_name).replace(" ", "")
        if menu_full in normalized_message_no_space:
            return menu_name, int(price)

    # จับแบบตัดคำว่า "คุกกี้"
    for menu_name, price in sorted(menu_prices.items(), key=lambda item: -len(item[0])):
        cleaned_menu = clean_for_match(menu_name)

        if cleaned_menu and cleaned_menu in cleaned_message:
            return menu_name, int(price)

        # ถ้าลูกค้าพิมพ์สั้น เช่น "โกโก้", "คาราเมล"
        if cleaned_menu and cleaned_message in cleaned_menu and len(cleaned_message) >= 3:
            return menu_name, int(price)

    return None, 0


def extract_order_from_text(message: str, menu_prices: dict, menu_number_map=None):
    q = normalize_text(message)

    if not q:
        return None

    # คำถามทั่วไป ไม่ถือเป็นออเดอร์
    if is_general_question(q) and not has_order_intent(q):
        return None

    menu_number_map = menu_number_map or {}

    menu_number = extract_menu_number(q)
    quantity = extract_quantity(q, menu_number=menu_number)

    menu_name = None
    price = 0

    # 1) สั่งด้วยเลขเมนู เช่น รับเมนู 1 จำนวน 3 ชิ้น
    if menu_number and str(menu_number) in menu_number_map:
        menu_name = menu_number_map[str(menu_number)]
        price = int(menu_prices.get(menu_name, 0))

    # 2) สั่งด้วยชื่อเมนู
    if not menu_name:
        menu_name, price = find_menu_by_name(q, menu_prices)

    # ไม่มีเจตนาสั่ง และไม่มีเมนู/จำนวนชัดเจน
    if not has_order_intent(q) and not menu_name:
        return None

    # มีเจตนาสั่งแต่ยังไม่รู้เมนูหรือจำนวน ปล่อยให้ระบบตอบแนะนำ/ถามต่อ
    if not menu_name or not quantity:
        return None

    if price <= 0:
        return None

    return {
        "menu_name": menu_name,
        "menu": menu_name,
        "quantity": int(quantity),
        "price": int(price),
    }
