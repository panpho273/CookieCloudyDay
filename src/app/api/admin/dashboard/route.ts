import { NextResponse } from "next/server";
import {
  getMembersSheet,
  getOrdersSheet,
  getReviewsSheet,
} from "@/lib/google-sheets";

export const dynamic = "force-dynamic";
export const revalidate = 0;

function normalize(text: unknown) {
  return String(text || "").trim().toLowerCase();
}

function toNumber(value: unknown) {
  const num = Number(String(value || "").replace(/[^\d.]/g, ""));
  return Number.isFinite(num) ? num : 0;
}

function findColumn(headers: unknown[], keywords: string[]) {
  return headers.findIndex((header) => {
    const value = normalize(header);
    return keywords.some((keyword) => value.includes(keyword.toLowerCase()));
  });
}

function calculateAgeFromBirthDate(value: unknown) {
  const raw = String(value || "").trim();

  if (!raw) return null;

  const directAge = Number(raw);
  if (Number.isFinite(directAge) && directAge > 0 && directAge < 120) {
    return directAge;
  }

  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return null;

  const today = new Date();
  let age = today.getFullYear() - date.getFullYear();

  const hasBirthdayPassed =
    today.getMonth() > date.getMonth() ||
    (today.getMonth() === date.getMonth() && today.getDate() >= date.getDate());

  if (!hasBirthdayPassed) age -= 1;

  return age > 0 && age < 120 ? age : null;
}

function getAgeGroup(age: number) {
  if (age < 18) return "ต่ำกว่า 18 ปี";
  if (age <= 24) return "18–24 ปี";
  if (age <= 34) return "25–34 ปี";
  if (age <= 44) return "35–44 ปี";
  if (age <= 54) return "45–54 ปี";
  return "55 ปีขึ้นไป";
}

function analyzeMembersByAge(rows: unknown[][]) {
  if (rows.length <= 1) {
    return {
      totalMembersWithAge: 0,
      bestAgeGroup: "-",
      ageGroups: [],
    };
  }

  const headers = rows[0];

  const ageIndex = findColumn(headers, ["age", "อายุ"]);
  const birthIndex = findColumn(headers, [
    "birthday",
    "birth",
    "birthdate",
    "วันเกิด",
    "เกิด",
  ]);

  const counts: Record<string, number> = {};
  let totalMembersWithAge = 0;

  for (const row of rows.slice(1)) {
    let age: number | null = null;

    if (ageIndex !== -1) {
      age = calculateAgeFromBirthDate(row[ageIndex]);
    }

    if (age === null && birthIndex !== -1) {
      age = calculateAgeFromBirthDate(row[birthIndex]);
    }

    if (age === null) {
      // fallback: เผื่อไม่มี header ชัดเจน ให้ลองหา column ที่ดูเหมือนอายุหรือวันเกิด
      for (const cell of row) {
        const guessed = calculateAgeFromBirthDate(cell);
        if (guessed !== null) {
          age = guessed;
          break;
        }
      }
    }

    if (age === null) continue;

    const group = getAgeGroup(age);
    counts[group] = (counts[group] || 0) + 1;
    totalMembersWithAge += 1;
  }

  const ageGroups = Object.entries(counts)
    .map(([group, count]) => ({
      group,
      count,
      percent:
        totalMembersWithAge > 0
          ? Number(((count / totalMembersWithAge) * 100).toFixed(1))
          : 0,
    }))
    .sort((a, b) => b.count - a.count);

  return {
    totalMembersWithAge,
    bestAgeGroup: ageGroups[0]?.group || "-",
    ageGroups,
  };
}

function analyzeReviews(rows: unknown[][]) {
  if (rows.length <= 1) {
    return {
      totalReviews: 0,
      averageRating: "0.0",
      latestReviews: [],
    };
  }

  const body = rows.slice(1);

  const ratings = body
    .map((row) => toNumber(row[2]))
    .filter((rating) => rating > 0);

  const average =
    ratings.length > 0
      ? ratings.reduce((sum, rating) => sum + rating, 0) / ratings.length
      : 0;

  const latestReviews = body
    .slice(-5)
    .reverse()
    .map((row) => ({
      date: row[0] || "",
      time: row[1] || "",
      rating: toNumber(row[2]),
      comment: row[3] || "",
      source: row[4] || "",
    }));

  return {
    totalReviews: body.length,
    averageRating: average.toFixed(1),
    latestReviews,
  };
}

function analyzeOrders(rows: unknown[][]) {
  if (rows.length <= 1) {
    return {
      totalOrders: 0,
      totalSales: 0,
      topMenu: "-",
    };
  }

  const headers = rows[0];

  const menuIndex = findColumn(headers, ["menu", "เมนู", "สินค้า", "cookie"]);
  const totalIndex = findColumn(headers, ["total", "ยอดรวม", "ราคา", "amount"]);

  const menuCounts: Record<string, number> = {};
  let totalSales = 0;

  for (const row of rows.slice(1)) {
    const menu = String(row[menuIndex] || "").trim();

    if (menu) {
      menuCounts[menu] = (menuCounts[menu] || 0) + 1;
    }

    if (totalIndex !== -1) {
      totalSales += toNumber(row[totalIndex]);
    }
  }

  const topMenu =
    Object.entries(menuCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || "-";

  return {
    totalOrders: rows.length - 1,
    totalSales,
    topMenu,
  };
}

export async function GET() {
  try {
    const [ordersRows, reviewsRows, membersRows] = await Promise.all([
      getOrdersSheet(),
      getReviewsSheet(),
      getMembersSheet(),
    ]);

    const reviewSummary = analyzeReviews(reviewsRows);
    const orderSummary = analyzeOrders(ordersRows);
    const memberAgeSummary = analyzeMembersByAge(membersRows);

    return NextResponse.json({
      ok: true,

      reviews: reviewSummary.totalReviews,
      totalReviews: reviewSummary.totalReviews,
      averageRating: reviewSummary.averageRating,
      avgRating: reviewSummary.averageRating,
      latestReviews: reviewSummary.latestReviews,

      orders: orderSummary.totalOrders,
      totalOrders: orderSummary.totalOrders,
      totalSales: orderSummary.totalSales,
      topMenu: orderSummary.topMenu,

      members: Math.max(membersRows.length - 1, 0),
      totalMembers: Math.max(membersRows.length - 1, 0),

      bestAgeGroup: memberAgeSummary.bestAgeGroup,
      totalMembersWithAge: memberAgeSummary.totalMembersWithAge,
      ageGroups: memberAgeSummary.ageGroups,

      sheets: {
        orders: {
          name: "ชีต1",
          rows: Math.max(ordersRows.length - 1, 0),
        },
        reviews: {
          name: "reviews",
          rows: Math.max(reviewsRows.length - 1, 0),
        },
        members: {
          name: "members",
          rows: Math.max(membersRows.length - 1, 0),
        },
      },
    });
  } catch (error) {
    return NextResponse.json(
      {
        ok: false,
        message:
          error instanceof Error
            ? error.message
            : "Cannot load admin dashboard",
      },
      { status: 500 }
    );
  }
}
