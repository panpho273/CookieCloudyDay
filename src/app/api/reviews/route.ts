import { NextRequest, NextResponse } from "next/server";

type ReviewPayload = {
  rating?: number;
  comment?: string;
  source?: string;
};

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as ReviewPayload;

    const rating = Number(body.rating);
    const comment = String(body.comment || "");
    const source = String(body.source || "CookieCloudyDay Website");

    if (!Number.isFinite(rating) || rating < 1 || rating > 5) {
      return NextResponse.json(
        { ok: false, message: "Rating must be 1-5" },
        { status: 400 }
      );
    }

    const webhookUrl = process.env.GOOGLE_REVIEW_WEBHOOK_URL;

    if (!webhookUrl) {
      return NextResponse.json(
        {
          ok: false,
          message: "Missing GOOGLE_REVIEW_WEBHOOK_URL in Vercel",
        },
        { status: 500 }
      );
    }

    const googleRes = await fetch(webhookUrl, {
      method: "POST",
      headers: {
        "Content-Type": "text/plain;charset=utf-8",
      },
      body: JSON.stringify({
        rating,
        comment,
        source,
      }),
      cache: "no-store",
    });

    const googleText = await googleRes.text();

    if (!googleRes.ok) {
      return NextResponse.json(
        {
          ok: false,
          message: "Google Apps Script failed",
          status: googleRes.status,
          detail: googleText,
        },
        { status: 500 }
      );
    }

    let googleData: unknown = googleText;

    try {
      googleData = JSON.parse(googleText);
    } catch {}

    return NextResponse.json({
      ok: true,
      savedToSheet: true,
      google: googleData,
    });
  } catch (error) {
    return NextResponse.json(
      {
        ok: false,
        message: error instanceof Error ? error.message : "Cannot save review",
      },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({
    ok: true,
    message: "Review API is running",
  });
}
