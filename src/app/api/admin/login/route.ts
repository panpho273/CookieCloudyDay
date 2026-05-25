import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const { username, password } = await req.json();

  const adminUsername = process.env.ADMIN_USERNAME || "admin";
  const adminPassword = process.env.ADMIN_PASSWORD || "1234";

  if (username === adminUsername && password === adminPassword) {
    return NextResponse.json({
      ok: true,
      token: "cookiecloudyday-admin-demo-token",
    });
  }

  return NextResponse.json(
    { ok: false, message: "Invalid username or password" },
    { status: 401 }
  );
}
