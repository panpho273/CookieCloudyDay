import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;

const fortuneCards = [
  {
    name: "The Butter Star",
    emoji: "⭐",
    meaning: "วันนี้เหมาะกับคุกกี้หอมเนยละมุน ๆ ให้รางวัลตัวเองสักชิ้นนะคะ",
    recommend: "คุกกี้เนยสด",
  },
  {
    name: "Chocolate Moon",
    emoji: "🌙",
    meaning: "สายช็อกโกแลตกำลังมีโชค ลองเมนูเข้มข้นแล้วจะยิ้มได้ทั้งวัน",
    recommend: "คุกกี้ดับเบิ้ลช็อกโกแลต",
  },
  {
    name: "Red Velvet Heart",
    emoji: "💗",
    meaning: "ความน่ารักกำลังเข้าข้างคุณ เหมาะกับคุกกี้สีหวานและของฝากเล็ก ๆ",
    recommend: "คุกกี้เรดเวลเวท",
  },
  {
    name: "Cookie Cloud",
    emoji: "☁️",
    meaning: "วันนุ่มฟูเหมือนก้อนเมฆ เลือกคุกกี้รสโปรดแล้วพักใจสักหน่อยนะคะ",
    recommend: "คุกกี้ช็อกโกแลตชิพ",
  },
  {
    name: "Nutella Charm",
    emoji: "🍫",
    meaning: "ความหวานกำลังพอดี เหมาะกับเมนูที่มีไส้เยิ้ม ๆ และรสชาติพิเศษ",
    recommend: "คุกกี้นูเทลล่า",
  },
  {
    name: "Golden Crumb",
    emoji: "🍪",
    meaning: "เศษความสุขเล็ก ๆ กำลังรวมเป็นวันที่ดี คุกกี้สักกล่องช่วยเติมพลังได้ค่ะ",
    recommend: "คุกกี้คอร์นเฟลกคาราเมล",
  },
];

export async function GET() {
  const card = fortuneCards[Math.floor(Math.random() * fortuneCards.length)];

  return NextResponse.json(
    { ok: true, card },
    { headers: { "Cache-Control": "no-store" } }
  );
}
