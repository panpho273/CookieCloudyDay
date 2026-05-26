import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;

type ChatPayload = {
  message?: string;
};

function getDemiReply(message: string) {
  const msg = message.toLowerCase();

  if (
    msg.includes("เมนู") ||
    msg.includes("แนะนำ") ||
    msg.includes("คุกกี้") ||
    msg.includes("cookie")
  ) {
    return "เมนูแนะนำของ CookieCloudyDay คือคุกกี้ช็อกโกแลตชิพ คุกกี้เนยสด และคุกกี้ดับเบิลช็อกโกแลตค่ะ ถ้าชอบหวานละมุนแนะนำคุกกี้เนยสด แต่ถ้าชอบเข้มข้นแนะนำดับเบิลช็อกโกแลตเลยค่ะ 🍪";
  }

  if (
    msg.includes("ราคา") ||
    msg.includes("กี่บาท") ||
    msg.includes("เท่าไหร่") ||
    msg.includes("แพง")
  ) {
    return "ราคาคุกกี้ของร้านเริ่มประมาณ 45–69 บาท แล้วแต่เมนูค่ะ เมนูยอดนิยมส่วนใหญ่จะอยู่ในช่วงราคาน่ารัก เหมาะทั้งกินเองและซื้อเป็นของฝากค่ะ";
  }

  if (
    msg.includes("เปิด") ||
    msg.includes("เวลา") ||
    msg.includes("ปิด") ||
    msg.includes("ร้าน")
  ) {
    return "ร้าน CookieCloudyDay เปิดทุกวัน เวลา 10:00–20:00 น. ค่ะ ถ้าต้องการสั่งคุกกี้ แนะนำเลือกเมนูจากหน้าเว็บแล้วติดต่อร้านได้เลยนะคะ";
  }

  if (
    msg.includes("ของฝาก") ||
    msg.includes("ฝาก") ||
    msg.includes("ของขวัญ") ||
    msg.includes("วันเกิด")
  ) {
    return "ถ้าซื้อเป็นของฝาก Demi แนะนำคุกกี้เนยสดหรือคุกกี้ช็อกโกแลตชิพค่ะ รสชาติทานง่าย แพ็กเกจน่ารัก และเหมาะกับให้เพื่อนหรือคนพิเศษมากค่ะ 💜";
  }

  if (
    msg.includes("สั่ง") ||
    msg.includes("ออเดอร์") ||
    msg.includes("ซื้อ")
  ) {
    return "ตอนนี้สามารถดูเมนูจากหน้าเว็บและให้ Demi ช่วยแนะนำก่อนได้ค่ะ หลังจากเลือกเมนูแล้ว สามารถติดต่อร้านเพื่อสั่งซื้อได้เลยค่ะ";
  }

  if (
    msg.includes("หวาน") ||
    msg.includes("ไม่หวาน") ||
    msg.includes("หวานน้อย")
  ) {
    return "ถ้าชอบหวานน้อย Demi แนะนำคุกกี้เนยสดหรือคุกกี้ชาเขียวค่ะ รสชาติจะละมุนกว่า ส่วนสายหวานเข้มข้นแนะนำช็อกโกแลตชิพหรือดับเบิลช็อกโกแลตค่ะ";
  }

  return "Demi พร้อมช่วยเลือกคุกกี้ให้นะคะ ลองถามได้เลย เช่น “มีเมนูอะไรแนะนำ”, “คุกกี้ราคาเท่าไหร่”, หรือ “อยากได้คุกกี้เป็นของฝาก” 🍪";
}

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as ChatPayload;
    const message = String(body.message || "").trim();

    if (!message) {
      return NextResponse.json(
        { ok: false, reply: "กรุณาพิมพ์ข้อความก่อนนะคะ" },
        { status: 400 }
      );
    }

    return NextResponse.json(
      {
        ok: true,
        reply: getDemiReply(message),
      },
      {
        headers: {
          "Cache-Control": "no-store",
        },
      }
    );
  } catch {
    return NextResponse.json(
      {
        ok: false,
        reply: "ขออภัยค่ะ Demi ตอบไม่ได้ชั่วคราว ลองใหม่อีกครั้งนะคะ",
      },
      { status: 500 }
    );
  }
}
