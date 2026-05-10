from datetime import datetime
from sheets_client import get_sheet


def add_sale(menu, quantity, price):
    sheet = get_sheet()

    total = quantity * price
    today = datetime.now().strftime("%Y-%m-%d")

    sheet.append_row([today, menu, quantity, price, total])

    print("บันทึกยอดขายสำเร็จ")
    print(f"วันที่: {today}")
    print(f"เมนู: {menu}")
    print(f"จำนวน: {quantity}")
    print(f"ราคา: {price}")
    print(f"ยอดรวม: {total}")


if __name__ == "__main__":
    menu = input("ชื่อเมนู: ")
    quantity = int(input("จำนวน: "))
    price = float(input("ราคา: "))

    add_sale(menu, quantity, price)