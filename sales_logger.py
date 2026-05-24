import os
import sys
import json
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
        try:
            import streamlit as st
            sheet_id = str(st.secrets.get("GOOGLE_SHEETS_ID", "")).strip()
        except Exception:
            sheet_id = ""

    if not sheet_id:
        raise RuntimeError("ไม่พบ GOOGLE_SHEETS_ID ใน .env หรือ Streamlit Secrets")

    return sheet_id


def get_credentials():
    """
    ใช้ service-account.json ตอนรัน local
    ใช้ Streamlit Secrets ตอนรันบน Streamlit Cloud
    """

    # 1) Local / Codespaces
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        return Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES,
        )

    # 2) Streamlit Cloud Secrets แบบ [gcp_service_account]
    try:
        import streamlit as st

        print("DEBUG Streamlit secret keys:", list(st.secrets.keys()))

        if "gcp_service_account" in st.secrets:
            print("DEBUG found gcp_service_account")
            service_account_info = dict(st.secrets["gcp_service_account"])
            return Credentials.from_service_account_info(
                service_account_info,
                scopes=SCOPES,
            )
        else:
            print("DEBUG gcp_service_account not found")
    except Exception as e:
        print("DEBUG Streamlit secrets error:", repr(e))

    # 3) สำรอง: อ่านจาก env เป็น JSON string
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if service_account_json:
        service_account_info = json.loads(service_account_json)
        return Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES,
        )

    raise FileNotFoundError(
        "ไม่พบ service-account.json และไม่พบ gcp_service_account ใน Streamlit Secrets"
    )


def get_worksheet():
    creds = get_credentials()
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(get_sheet_id())
    return spreadsheet.sheet1


def log_sale(menu_name: str, quantity: int, price: int):
    today = datetime.now(THAI_TZ).strftime("%Y-%m-%d")
    total = int(quantity) * int(price)

    worksheet = get_worksheet()

    worksheet.append_row(
        [
            today,
            menu_name,
            int(quantity),
            int(price),
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
    if len(sys.argv) == 4:
        menu_name = sys.argv[1]
        quantity = int(sys.argv[2])
        price = int(sys.argv[3])
        log_sale(menu_name, quantity, price)
        return

    menu_name = input("ชื่อเมนู: ").strip()
    quantity = int(input("จำนวน: ").strip())
    price = int(input("ราคา: ").strip())

    log_sale(menu_name, quantity, price)


if __name__ == "__main__":
    main()
