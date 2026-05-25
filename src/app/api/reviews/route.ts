import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;

type ReviewPayload = {
  rating?: number;
  comment?: string;
  source?: string;
};

function noStoreResponse(data: unknown, status = 200) {
  return NextResponse.json(data, {
    status,
    headers: {
      "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
      Pragma: "no-cache",
      Expires: "0",
    },
  });
}

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as ReviewPayload;

    const rating = Number(body.rating);
    const comment = String(body.comment || "");
    const source = String(body.source || "CookieCloudyDay Website");

    if (!Number.isFinite(rating) || rating < 1 || rating > 5) {
      return noStoreResponse(
        { ok: false, message: "Rating must be 1-5" },
        400
      );
    }

    if (!comment.trim()) {
      return noStoreResponse(
        { ok: false, message: "Comment cannot be empty" },
        400
      );
    }

    const webhookUrl = process.env.GOOGLE_REVIEW_WEBHOOK_URL;

    if (!webhookUrl) {
      return noStoreResponse(
        { ok: false, message: "Missing GOOGLE_REVIEW_WEBHOOK_URL" },
        500
      );
    }

    const googleRes = await fetch(webhookUrl, {
      method: "POST",
      headers: {
        "Content-Type": "text/plain;charset=utf-8",
        "Cache-Control": "no-cache",
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
      return noStoreResponse(
        {
          ok: false,
          message: "Google Apps Script failed",
          status: googleRes.status,
          detail: googleText,
        },
        500
      );
    }

    let googleData: unknown = googleText;

    try {
      googleData = JSON.parse(googleText);
    } catch {}

    return noStoreResponse({
      ok: true,
      savedToSheet: true,
      google: googleData,
    });
  } catch (error) {
    return noStoreResponse(
      {
        ok: false,
        message: error instanceof Error ? error.message : "Cannot save review",
      },
      500
    );
  }
}

export async function GET() {
  try {
    const webhookUrl = process.env.GOOGLE_REVIEW_WEBHOOK_URL;

    if (!webhookUrl) {
      return noStoreResponse(
        {
          ok: false,
          message: "Missing GOOGLE_REVIEW_WEBHOOK_URL",
          reviews: [],
        },
        500
      );
    }

    const googleRes = await fetch(`${webhookUrl}?t=${Date.now()}`, {
      method: "GET",
      cache: "no-store",
      headers: {
        "Cache-Control": "no-cache",
      },
    });

    const googleText = await googleRes.text();

    if (!googleRes.ok) {
      return noStoreResponse(
        {
          ok: false,
          message: "Cannot load reviews from Google Sheet",
          detail: googleText,
          reviews: [],
        },
        500
      );
    }

    const data = JSON.parse(googleText);

    return noStoreResponse({
      ok: true,
      reviews: Array.isArray(data.reviews) ? data.reviews : [],
    });
  } catch (error) {
    return noStoreResponse(
      {
        ok: false,
        message: error instanceof Error ? error.message : "Cannot load reviews",
        reviews: [],
      },
      500
    );
  }
}
