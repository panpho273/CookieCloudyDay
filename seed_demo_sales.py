import json
import random
import re
import time
from pathlib import Path
from urllib import request

MENU_FILE = Path("shop_menu.json")
SCRIPT_FILE = Path("script.js")

def get_apps_script_url():
    text = SCRIPT_FILE.read_text(encoding="utf-8")
    match = re.search(r'const\s+SHEET_WEB_APP_URL\s*=\s*"([^"]+)"', text)
    if not match:
        raise RuntimeError("ไม่พบ SHEET_WEB_APP_URL ใน script.js")
    return match.group(1).strip()

def post_order(url, menu, quantity, price):
    payload = json.dumps({
        "menu": menu,
        "quantity": quantity,
        "price": price
    }).encode("utf-8")

    req = request.Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"}
    )

    with request.urlopen(req, timeout=20) as res:
        return res.read().decode("utf-8", errors="ignore")

def main():
    url = get_apps_script_url()
    menus = json.loads(MENU_FILE.read_text(encoding="utf-8"))

    random.seed(42)
    total_rows = 100

    print(f"กำลังเติมยอดขายตัวอย่าง {total_rows} รายการ จากเมนูทั้งหมด {len(menus)} เมนู...")

    for i in range(total_rows):
        item = random.choice(menus)
        quantity = random.randint(1, 8)
        price = int(item["price"])

        post_order(url, item["name"], quantity, price)

        print(f"{i + 1:03d}/{total_rows} {item['name']} x {quantity} = {quantity * price} บาท")
        time.sleep(0.15)

    print("เติมยอดขายตัวอย่างเรียบร้อยแล้ว")

if __name__ == "__main__":
    main()
