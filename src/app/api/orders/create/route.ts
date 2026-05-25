import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { cart, customerName, customerPhone } = body;

    if (!cart || cart.length === 0) {
      return NextResponse.json(
        { error: 'ตะกร้าว่างเปล่า' },
        { status: 400 }
      );
    }

    // TODO: บันทึกลง Google Sheets API
    // const gsheet = await saveToGoogleSheet({ cart, customerName, customerPhone });

    // TODO: ส่ง notification ไปยัง Telegram (ถ้ามี)
    // await sendTelegramNotification({ cart, customerName });

    // ตัวอย่าง response
    const orderData = {
      orderId: 'ORD' + Date.now(),
      items: cart,
      total: cart.reduce((sum: number, item: any) => sum + (item.price * item.quantity), 0),
      customerName,
      customerPhone,
      status: 'pending',
      createdAt: new Date().toISOString(),
    };

    return NextResponse.json({
      success: true,
      message: 'บันทึกออเดอร์สำเร็จ',
      data: orderData,
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'เกิดข้อผิดพลาดในการบันทึกออเดอร์' },
      { status: 500 }
    );
  }
}
