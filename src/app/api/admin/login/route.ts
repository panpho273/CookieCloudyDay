import { NextRequest, NextResponse } from "next/server";

function generateToken(username: string): string {
  const payload = {
    username,
    iat: Date.now(),
    exp: Date.now() + 24 * 60 * 60 * 1000,
  };

  return Buffer.from(JSON.stringify(payload)).toString("base64");
}

export async function POST(req: NextRequest) {
  try {
    const { username, password } = await req.json();

    const adminUsername = process.env.ADMIN_USERNAME || "admin";
    const adminPassword = process.env.ADMIN_PASSWORD || "cookiecloudyday2026";

    if (username === adminUsername && password === adminPassword) {
      const token = generateToken(username);

      const res = NextResponse.json({
        ok: true,
        role: "admin",
        message: "เข้าสู่ระบบหลังบ้านสำเร็จ",
      });

      res.cookies.set("cookiecloudyday_admin_token", token, {
        httpOnly: true,
        sameSite: "lax",
        secure: process.env.NODE_ENV === "production",
        path: "/",
        maxAge: 60 * 60 * 24,
      });

      return res;
    }

    return NextResponse.json(
      {
        ok: false,
        message: "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง",
      },
      { status: 401 }
    );
  } catch {
    return NextResponse.json(
      {
        ok: false,
        message: "เข้าสู่ระบบไม่สำเร็จ",
      },
      { status: 500 }
    );
  }
}
