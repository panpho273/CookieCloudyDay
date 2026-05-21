import json
import os
import random
from datetime import datetime, timedelta

import gspread

MENU_FILE = "shop_menu.json"

def main():
    sheet_id = os.getenv("GOOGLE_SHEETS_ID", "").strip()
    cred_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip() or "service-account.json"

    if not sheet_id:
        raise RuntimeError("ไม่พบ GOOGLE_SHEETS_ID ใน env")

    menus = json.load(open(MENU_FILE, encoding="utf-8"))

    gc = gspread.service_account(filename=cred_file)
    sh = gc.open_by_key(sheet_id)
    ws = sh.sheet1

    random.seed(42)
    today = datetime.now()

    rows = []

    # 100 รายการ เกินจำนวนไพ่ 78 ใบ ใช้สำหรับเดโมยอดขาย
    for i in range(100):
        item = random.choice(menus)
        quantity = random.randint(1, 8)
        price = item["price"]
        total = quantity * price
        date = (today - timedelta(days=random.randint(0, 6))).strftime("%Y-%m-%d")

        rows.append([
            date,
            item["name"],
            quantity,
            price,
            total
        ])

    ws.append_rows(rows, value_input_option="USER_ENTERED")
    print("เติมยอดขายตัวอย่าง 100 รายการเรียบร้อยแล้ว")

if __name__ == "__main__":
    main()
