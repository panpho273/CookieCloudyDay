import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv(".env")

THAI_TZ = ZoneInfo("Asia/Bangkok")
SERVICE_ACCOUNT_FILE = "service-account.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_sheet_id():
    sheet_id = os.getenv("GOOGLE_SHEETS_ID", "").strip()
    if not sheet_id:
        raise RuntimeError("ไม่พบ GOOGLE_SHEETS_ID ในไฟล์ .env")
    return sheet_id


def get_worksheet():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError("ไม่พบไฟล์ service-account.json")

    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )

    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(get_sheet_id())
    return spreadsheet.sheet1


def log_sale(menu_name: str, quantity: int, price: int):
    today = datetime.now(THAI_TZ).strftime("%Y-%m-%d")
    total = quantity * price

    worksheet = get_worksheet()

    # ให้ตรงหัวตารางเดิม:
    # วันที่ | เมนู | จำนวน | ราคา | ยอดรวม
    worksheet.append_row(
        [
            today,
            menu_name,
            quantity,
            price,
            total,
        ],
        value_input_option="USER_ENTERED",
    )

    print("✅ บันทึกยอดขายสำเร็จ")
    print(f"วันที่: {today}")
    print(f"เมนู: {menu_name}")
    print(f"จำนวน: {quantity}")
    print(f"ราคา: {price}")
    print(f"ยอดรวม: {total} บาท")


def main():
    # แบบที่ 1: รับจาก command line
    # python sales_logger.py "คุกกี้ช็อกโกแลตชิพ" 3 45
    if len(sys.argv) == 4:
        menu_name = sys.argv[1]
        quantity = int(sys.argv[2])
        price = int(sys.argv[3])
        log_sale(menu_name, quantity, price)
        return

    # แบบที่ 2: ถ้าไม่ส่ง argument ค่อยถามทีละช่อง
    menu_name = input("ชื่อเมนู: ").strip()
    quantity = int(input("จำนวน: ").strip())
    price = int(input("ราคา: ").strip())

    log_sale(menu_name, quantity, price)


if __name__ == "__main__":
    main()
