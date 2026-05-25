import { NextRequest, NextResponse } from 'next/server';

function verifyToken(token: string | null): boolean {
  if (!token) return false;
  try {
    const payload = JSON.parse(Buffer.from(token.replace('Bearer ', ''), 'base64').toString());
    return payload.exp > Date.now();
  } catch {
    return false;
  }
}

export async function GET(request: NextRequest) {
  const authHeader = request.headers.get('authorization');
  const token = authHeader?.split(' ')[1];

  if (!token || !verifyToken(token)) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  // TODO: ดึงข้อมูลจาก Google Sheets API
  // สำหรับตอนนี้ให้เป็นข้อมูลจำลอง

  const mockData = {
    totalOrders: 45,
    totalRevenue: 2340,
    topMenu: 'คุกกี้ช็อกโกแลตชิพ',
    recentOrders: [
      { menu: 'คุกกี้ช็อกโกแลตชิพ', quantity: 2, total: 90, date: '25 พ.ค.' },
      { menu: 'คุกกี้เนยสด', quantity: 1, total: 55, date: '25 พ.ค.' },
      { menu: 'คุกกี้มัทฉะไวท์ช็อก', quantity: 3, total: 177, date: '24 พ.ค.' },
    ],
    reviews: [
      { name: 'น้อย', rating: 5, comment: 'อร่อยมากค่า!', date: '25 พ.ค.' },
      { name: 'ตั้ม', rating: 5, comment: 'ส่งเร็ว หิ้วไม่หัก', date: '24 พ.ค.' },
    ],
  };

  return NextResponse.json(mockData);
}
