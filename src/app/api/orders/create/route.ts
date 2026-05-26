import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export const dynamic = "force-dynamic";
export const revalidate = 0;

type TarotCard = {
  id?: number;
  type?: string;
  name?: string;
  emoji?: string;
  cookie?: string;
  cookie_price?: number;
  keyword?: string;
  meaning?: string;
  freebie_text?: string;
};

function getTarotDeck(): TarotCard[] {
  try {
    const filePath = path.join(process.cwd(), "tarot_cards.json");
    const raw = fs.readFileSync(filePath, "utf-8");
    const data = JSON.parse(raw);

    if (Array.isArray(data)) return data as TarotCard[];

    if (data && typeof data === "object") {
      for (const key of ["cards", "tarot_cards", "deck", "items"]) {
        if (Array.isArray(data[key])) {
          return data[key] as TarotCard[];
        }
      }
    }

    return [];
  } catch {
    return [];
  }
}

function randomCard() {
  const deck = getTarotDeck();

  if (!deck.length) {
    return {
      name: "Cookie Fortune",
      emoji: "🔮",
      message: "วันนี้เหมาะกับการให้รางวัลตัวเองด้วยคุกกี้ชิ้นโปรดค่ะ",
      recommend: "คุกกี้ช็อกโกแลตชิพ",
      keyword: "ความสุขเล็ก ๆ การดูแลตัวเอง และพลังใจ",
      freebieText: "โปรเปิดร้าน: รับฟรีคุกกี้ 1 ชิ้น เมื่อซื้อครบ 150 บาท",
    };
  }

  const card = deck[Math.floor(Math.random() * deck.length)];

  const name = card.name || "Cookie Fortune";
  const emoji = card.emoji || "🔮";
  const recommend = card.cookie || "คุกกี้ช็อกโกแลตชิพ";
  const message =
    card.meaning ||
    "วันนี้มีเรื่องดี ๆ รออยู่ ลองเลือกคุกกี้ที่ชอบแล้วเติมความสุขให้ตัวเองนะคะ";
  const keyword =
    card.keyword || "ความสุขเล็ก ๆ การดูแลตัวเอง และพลังใจ";
  const freebieText =
    card.freebie_text ||
    `โปรเปิดร้าน: รับฟรี ${recommend} 1 ชิ้น ตามไพ่ ${name}`;

  return {
    name,
    emoji,
    message,
    recommend,
    keyword,
    freebieText,
  };
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    const total = Number(body.total || 0);
    const promoEligible = total >= 150;
    const card = promoEligible ? randomCard() : null;

    const webhookUrl =
      process.env.GOOGLE_SHOP_WEBHOOK_URL ||
      process.env.GOOGLE_REVIEW_WEBHOOK_URL;

    if (!webhookUrl) {
      return NextResponse.json({
        ok: true,
        localOnly: true,
        order: {
          orderId: `LOCAL-${Date.now()}`,
          promoEligible,
          cardName: card?.name || "",
          cardMessage: card?.message || "",
          cardRecommend: card?.recommend || "",
          cardKeyword: card?.keyword || "",
          cardFreebieText: card?.freebieText || "",
          cardEmoji: card?.emoji || "",
        },
        message: "Local order saved for preview only",
      });
    }

    const googleRes = await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify({
        action: "createOrder",
        memberKey: body.memberKey,
        menu: body.menu,
        quantity: body.quantity,
        total,
        promoEligible,
        cardName: card?.name || "",
        cardMessage: card?.message || "",
        cardRecommend: card?.recommend || "",
        cardKeyword: card?.keyword || "",
        cardFreebieText: card?.freebieText || "",
        cardEmoji: card?.emoji || "",
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

    return NextResponse.json({
      ...data,
      order: {
        ...(data.order || {}),
        promoEligible,
        cardName: data.order?.cardName || card?.name || "",
        cardMessage: data.order?.cardMessage || card?.message || "",
        cardRecommend: data.order?.cardRecommend || card?.recommend || "",
        cardKeyword: data.order?.cardKeyword || card?.keyword || "",
        cardFreebieText: data.order?.cardFreebieText || card?.freebieText || "",
        cardEmoji: data.order?.cardEmoji || card?.emoji || "",
      },
    });
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
