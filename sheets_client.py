import os
import json
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheet():
    """รองรับทั้งโหมดไฟล์ local และโหมด JSON string สำหรับ GitHub Actions"""

    json_str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    file_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    sheet_id = "".join(os.getenv("GOOGLE_SHEETS_ID", "").split())

    if json_str:
        # ใช้ตอนรันบน GitHub Actions
        info = json.loads(json_str)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        print("ใช้ Service Account จาก GitHub Secret:", info["client_email"])

    elif file_path:
        # ใช้ตอนรันใน Codespaces / เครื่องเรา
        with open(file_path, "r", encoding="utf-8") as f:
            info = json.load(f)

        creds = Credentials.from_service_account_file(file_path, scopes=SCOPES)
        print("ใช้ Service Account จากไฟล์ local:", info["client_email"])

    else:
        raise RuntimeError(
            "ไม่พบ GOOGLE_SERVICE_ACCOUNT_JSON หรือ GOOGLE_SERVICE_ACCOUNT_FILE"
        )

    if not sheet_id:
        raise RuntimeError("ไม่พบ GOOGLE_SHEETS_ID")

    print("ความยาว GOOGLE_SHEETS_ID:", len(sheet_id))

    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id).sheet1