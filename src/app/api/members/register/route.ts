import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    const webhookUrl =
      process.env.GOOGLE_SHOP_WEBHOOK_URL ||
      process.env.GOOGLE_REVIEW_WEBHOOK_URL;

    /*
      LOCAL FALLBACK:
      ถ้าไม่มี webhook ใน local ให้สมัครสำเร็จแบบจำลอง
    */
    if (!webhookUrl) {
      return NextResponse.json({
        ok: true,
        localOnly: true,
        alreadyMember: false,
        member: {
          memberCode: `LOCAL-${Date.now()}`,
          name: body.name,
          phone: body.phone,
          email: body.email,
        },
        message: "Local member registered for preview only",
      });
    }

    const googleRes = await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify({
        action: "registerMember",
        name: body.name,
        phone: body.phone,
        email: body.email,
        birthday: body.birthday,
        favoriteCookie: body.favoriteCookie,
      }),
      cache: "no-store",
    });

    const text = await googleRes.text();
    const data = JSON.parse(text);

    if (!data.ok) {
      return NextResponse.json(
        { ok: false, message: data.error || "Cannot register member" },
        { status: 400 }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      {
        ok: false,
        message:
          error instanceof Error ? error.message : "Cannot register member",
      },
      { status: 500 }
    );
  }
}
