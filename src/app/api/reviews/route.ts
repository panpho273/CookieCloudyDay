import { NextRequest, NextResponse } from "next/server";

type ReviewPayload = {
  rating?: number;
  comment?: string;
  source?: string;
};

const mockReviews = [
  {
    rating: 5,
    comment: "เว็บน่ารัก ใช้งานง่าย",
    createdAt: "mock",
  },
  {
    rating: 5,
    comment: "Demi แนะนำเมนูดีมาก",
    createdAt: "mock",
  },
];

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as ReviewPayload;

    const rating = Number(body.rating);
    const comment = String(body.comment || "");
    const source = String(body.source || "website");

    if (!Number.isFinite(rating) || rating < 1 || rating > 5) {
      return NextResponse.json(
        { ok: false, message: "Rating must be 1-5" },
        { status: 400 }
      );
    }

    const webhookUrl = process.env.GOOGLE_REVIEW_WEBHOOK_URL;

    if (webhookUrl) {
      await fetch(webhookUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          rating,
          comment,
          source,
          createdAt: new Date().toISOString(),
        }),
      });
    }

    return NextResponse.json({
      ok: true,
      savedToSheet: Boolean(webhookUrl),
      review: {
        rating,
        comment,
        source,
      },
    });
  } catch {
    return NextResponse.json(
      { ok: false, message: "Cannot save review" },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({
    ok: true,
    reviews: mockReviews,
  });
}
