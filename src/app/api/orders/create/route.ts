import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    const webhookUrl =
      process.env.GOOGLE_SHOP_WEBHOOK_URL ||
      process.env.GOOGLE_REVIEW_WEBHOOK_URL;

    if (!webhookUrl) {
      return NextResponse.json(
        { ok: false, message: "Missing Google webhook URL" },
        { status: 500 }
      );
    }

    const googleRes = await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify({
        action: "createOrder",
        memberKey: body.memberKey,
        menu: body.menu,
        quantity: body.quantity,
        total: body.total,
      }),
      cache: "no-store",
    });

    const text = await googleRes.text();
    const data = JSON.parse(text);

    if (!data.ok) {
      return NextResponse.json(
        { ok: false, message: data.error || "Cannot create order" },
        { status: 400 }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      {
        ok: false,
        message: error instanceof Error ? error.message : "Cannot create order",
      },
      { status: 500 }
    );
  }
}
