import re
from sales_logger import get_worksheet


def _to_int(value, default=0):
    try:
        return int(float(str(value).replace(",", "").strip()))
    except Exception:
        return default


def _to_float(value, default=0):
    try:
        return float(str(value).replace(",", "").strip())
    except Exception:
        return default


def get_top_selling_menus_from_sheet(limit=5):
    """
    อ่านยอดขายจาก Google Sheet จริง
    คอลัมน์:
    A = วันที่
    B = เมนู
    C = จำนวน
    D = ราคา
    E = ยอดรวม
    """
    ws = get_worksheet()
    values = ws.get_all_values()

    summary = {}

    for row in values:
        row = row + [""] * 5

        date_value = str(row[0]).strip()
        menu = str(row[1]).strip()

        # เอาเฉพาะแถวข้อมูลจริงที่ขึ้นต้นวันที่แบบ YYYY-MM-DD
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_value):
            continue

        if not menu:
            continue

        quantity = _to_int(row[2], 0)
        price = _to_int(row[3], 0)
        total = _to_float(row[4], quantity * price)

        if quantity <= 0:
            continue

        if menu not in summary:
            summary[menu] = {
                "menu": menu,
                "quantity": 0,
                "total": 0,
                "price": price,
            }

        summary[menu]["quantity"] += quantity
        summary[menu]["total"] += total

        if price:
            summary[menu]["price"] = price

    ranked = sorted(
        summary.values(),
        key=lambda item: (item["quantity"], item["total"]),
        reverse=True,
    )

    return ranked[:limit]


def build_hot_menu_reply(limit=5):
    try:
        top_menus = get_top_selling_menus_from_sheet(limit)
    except Exception as e:
        print("build_hot_menu_reply error:", repr(e))
        return (
            "ได้เลยค่า 🍪

"
            "ตอนนี้ Demi ยังเช็กเมนูฮิตให้ไม่ได้แป๊บนึงนะคะ "
            "ลูกค้าพิมพ์ว่า “เมนูทั้งหมด” เพื่อเลือกดูเมนูได้เลยค่ะ"
        )

    if not top_menus:
        return (
            "ได้เลยค่า 🍪

"
            "ตอนนี้ยังไม่มีเมนูฮิตประจำวันนี้ให้แนะนำเป็นพิเศษน้า "
            "ลูกค้าพิมพ์ว่า “เมนูทั้งหมด” เพื่อเลือกดูเมนูได้เลยค่ะ"
        )

    lines = [
        "ได้เลยค่าา 🍪",
        "",
        "ถ้าให้ Demi แนะนำ ตอนนี้เมนูที่ลูกค้าชอบสั่งกันบ่อย ๆ มีประมาณนี้ค่ะ:",
        "",
    ]

    for index, item in enumerate(top_menus, start=1):
        menu = item["menu"]
        price = int(item.get("price") or 0)

        if price:
            lines.append(f"{index}. {menu} — {price} บาท")
        else:
            lines.append(f"{index}. {menu}")

    lines += [
        "",
        "ถ้าชอบแนวกรอบ ๆ หอม ๆ เลือกตัวคอร์นเฟลกได้เลยค่ะ",
        "ถ้าชอบเข้ม ๆ แนะนำโกโก้หรือช็อกโกแลตน้า",
        "",
        "ลูกค้าพิมพ์ชื่อเมนูพร้อมจำนวนได้เลย เช่น “เอาคุกกี้คอร์นเฟลกคาราเมล 2 ชิ้น”",
        "หรือถ้าจะเลือกจากลิสต์นี้ พิมพ์ได้เลยค่ะ เช่น “รับเมนู 1 จำนวน 3 ชิ้น”",
    ]

    return "
".join(lines)


def get_hot_menu_number_map(limit=5):
    try:
        top_menus = get_top_selling_menus_from_sheet(limit)
    except Exception as e:
        print("get_hot_menu_number_map error:", repr(e))
        return {}

    return {
        str(index): item["menu"]
        for index, item in enumerate(top_menus, start=1)
    }
