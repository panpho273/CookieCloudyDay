import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const token = req.cookies.get("cookiecloudyday_admin_token")?.value;

  if (!token) {
    return NextResponse.json({ ok: false }, { status: 401 });
  }

  try {
    const payload = JSON.parse(Buffer.from(token, "base64").toString("utf-8"));

    if (!payload.exp || Date.now() > payload.exp) {
      return NextResponse.json({ ok: false }, { status: 401 });
    }

    return NextResponse.json({
      ok: true,
      username: payload.username,
      role: "admin",
    });
  } catch {
    return NextResponse.json({ ok: false }, { status: 401 });
  }
}
