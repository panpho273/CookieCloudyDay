import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';

// ตัวอย่าง credentials (ควรใช้ environment variables จริง ๆ)
const ADMIN_USERNAME = process.env.ADMIN_USERNAME || 'admin';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'cookiecloudyday123';
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-here';

function generateToken(username: string): string {
  // ง่ายๆ token generation (ในโปรเจกต์จริงใช้ JWT library)
  const payload = {
    username,
    iat: Date.now(),
    exp: Date.now() + 24 * 60 * 60 * 1000, // 24 hours
  };
  return Buffer.from(JSON.stringify(payload)).toString('base64');
}

function verifyToken(token: string): { username: string } | null {
  try {
    const payload = JSON.parse(Buffer.from(token, 'base64').toString());
    if (payload.exp < Date.now()) {
      return null;
    }
    return payload;
  } catch {
    return null;
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { username, password } = body;

    // ตรวจสอบ credentials
    if (username === ADMIN_USERNAME && password === ADMIN_PASSWORD) {
      const token = generateToken(username);
      return NextResponse.json({ token, username });
    }

    return NextResponse.json(
      { error: 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง' },
      { status: 401 }
    );
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
