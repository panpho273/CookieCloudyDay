import { NextRequest, NextResponse } from "next/server";
import { appendReview, getReviews } from "@/lib/google-sheets";

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

    if (!comment.trim()) {
      return NextResponse.json(
        { ok: false, message: "Comment cannot be empty" },
        { status: 400 }
      );
    }

    // Save to Google Sheets
    await appendReview(rating, comment, source);

    return NextResponse.json({
      ok: true,
      message: "Review saved successfully",
    });
  } catch (error) {
    console.error("Error saving review:", error);
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
  try {
    const reviews = await getReviews();
    return NextResponse.json({
      ok: true,
      reviews: reviews,
    });
  } catch (error) {
    console.error("Error fetching reviews:", error);
    return NextResponse.json(
      {
        ok: false,
        message: "Cannot fetch reviews",
      },
      { status: 500 }
    );
  }
}
