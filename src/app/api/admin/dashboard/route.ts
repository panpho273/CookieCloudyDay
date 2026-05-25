import { NextRequest, NextResponse } from 'next/server';
import { getReviews } from '@/lib/google-sheets';

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

  try {
    // Get real reviews from Google Sheets
    const reviews = await getReviews();

    const mockData = {
      totalOrders: 45,
      totalRevenue: 2340,
      topMenu: 'คุกกี้ช็อกโกแลตชิพ',
      recentOrders: [
        { menu: 'คุกกี้ช็อกโกแลตชิพ', quantity: 2, total: 90, date: '25 พ.ค.' },
        { menu: 'คุกกี้เนยสด', quantity: 1, total: 55, date: '25 พ.ค.' },
        { menu: 'คุกกี้มัทฉะไวท์ช็อก', quantity: 3, total: 177, date: '24 พ.ค.' },
      ],
      reviews: reviews.slice(0, 10), // Show latest 10 reviews
    };

    return NextResponse.json(mockData);
  } catch (err) {
    console.error('Error in dashboard:', err);
    return NextResponse.json(
      { error: 'Failed to load dashboard data' },
      { status: 500 }
    );
  }
}
