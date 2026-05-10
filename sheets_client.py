import os
import json
import re
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def extract_sheet_id(value: str) -> str:
    """รับได้ทั้ง Sheet ID ล้วน และ Google Sheet URL เต็ม"""
    value = "".join(value.split())

    # ถ้าใส่มาเป็น URL เต็ม ให้ดึงเฉพาะส่วนระหว่าง /d/ กับ /edit
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", value)
    if match:
        return match.group(1)

    # ถ้าใส่มาเป็น ID ล้วน ก็ใช้ตรง ๆ
    return value


def get_sheet():
    """รองรับทั้งโหมดไฟล์ local และโหมด JSON string สำหรับ GitHub Actions"""

    json_str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    file_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    raw_sheet_id = os.getenv("GOOGLE_SHEETS_ID", "")
    sheet_id = extract_sheet_id(raw_sheet_id)

    if json_str:
        info = json.loads(json_str)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)

    elif file_path:
        creds = Credentials.from_service_account_file(file_path, scopes=SCOPES)

    else:
        raise RuntimeError(
            "ไม่พบ GOOGLE_SERVICE_ACCOUNT_JSON หรือ GOOGLE_SERVICE_ACCOUNT_FILE"
        )

    if not sheet_id:
        raise RuntimeError("ไม่พบ GOOGLE_SHEETS_ID")

    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id).sheet1