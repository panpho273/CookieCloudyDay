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
  const { username, password } = await req.json();

  const adminUsername = process.env.ADMIN_USERNAME || "admin";
  const adminPassword = process.env.ADMIN_PASSWORD || "cookiecloudyday2026";

  if (username === adminUsername && password === adminPassword) {
    const token = generateToken(username);
    return NextResponse.json({
      ok: true,
      token,
    });
  }

  return NextResponse.json(
    { ok: false, message: "Invalid username or password" },
    { status: 401 }
  );
}
