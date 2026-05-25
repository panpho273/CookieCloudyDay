import { NextRequest, NextResponse } from "next/server";
import { getReviews } from "@/lib/google-sheets";

type Review = {
  rating: number;
  comment: string;
  source?: string;
  createdAt: string;
};

function verifyToken(token: string | null): boolean {
  if (!token) return false;

  // รองรับ token demo ที่หน้า login ใช้อยู่
  if (token === "cookiecloudyday-admin-demo-token") {
    return true;
  }

  try {
    const payload = JSON.parse(
      Buffer.from(token.replace("Bearer ", ""), "base64").toString()
    );

    return Number(payload.exp || 0) > Date.now();
  } catch {
    return false;
  }
}

function calculateDashboardStats(reviews: Review[]) {
  const totalReviews = reviews.length;

  const averageRating =
    totalReviews > 0
      ? reviews.reduce((sum, review) => sum + Number(review.rating || 0), 0) /
        totalReviews
      : 0;

  const ratingCounts = {
    5: reviews.filter((review) => Number(review.rating) === 5).length,
    4: reviews.filter((review) => Number(review.rating) === 4).length,
    3: reviews.filter((review) => Number(review.rating) === 3).length,
    2: reviews.filter((review) => Number(review.rating) === 2).length,
    1: reviews.filter((review) => Number(review.rating) === 1).length,
  };

  const latestReviews = reviews.slice(0, 10);

  return {
    totalReviews,
    averageRating: Number(averageRating.toFixed(1)),
    ratingCounts,
    latestReviews,
  };
}

export async function GET(request: NextRequest) {
  const authHeader = request.headers.get("authorization");
  const token = authHeader?.split(" ")[1] || null;

  if (!verifyToken(token)) {
    return NextResponse.json(
      {
        ok: false,
        error: "Unauthorized",
      },
      { status: 401 }
    );
  }

  try {
    const reviews = await getReviews();
    const stats = calculateDashboardStats(reviews);

    return NextResponse.json({
      ok: true,

      summary: {
        totalReviews: stats.totalReviews,
        averageRating: stats.averageRating,
        fiveStarReviews: stats.ratingCounts[5],
      },

      ratingCounts: stats.ratingCounts,

      reviews: stats.latestReviews,

      // ยังใส่ mock order ไว้ก่อน เผื่อหน้า dashboard เดิมเรียกใช้
      orders: {
        totalOrders: 45,
        totalRevenue: 2340,
        topMenu: "คุกกี้ช็อกโกแลตชิพ",
        recentOrders: [
          {
            menu: "คุกกี้ช็อกโกแลตชิพ",
            quantity: 2,
            total: 90,
            date: "25 พ.ค.",
          },
          {
            menu: "คุกกี้เนยสด",
            quantity: 1,
            total: 55,
            date: "25 พ.ค.",
          },
          {
            menu: "คุกกี้มัทฉะไวท์ช็อก",
            quantity: 3,
            total: 177,
            date: "24 พ.ค.",
          },
        ],
      },
    });
  } catch (error) {
    console.error("Error in dashboard:", error);

    return NextResponse.json(
      {
        ok: false,
        error:
          error instanceof Error
            ? error.message
            : "Failed to load dashboard data",
      },
      { status: 500 }
    );
  }
}
