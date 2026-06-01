export type DemiReply = {
  text: string;
  intent:
    | "menu"
    | "price"
    | "openTime"
    | "gift"
    | "fortune"
    | "order"
    | "help";
};

export const demiQuickActions = [
  { label: "🍪 เมนูแนะนำ", value: "เมนูแนะนำ" },
  { label: "💸 ราคา", value: "ราคา" },
  { label: "⏰ เวลาเปิดร้าน", value: "เวลาเปิดร้าน" },
  { label: "🎁 ของฝาก", value: "ซื้อฝาก" },
  { label: "🔮 สุ่มไพ่", value: "สุ่มไพ่" },
];

const menuText = `เมนูแนะนำของร้านคือ คุกกี้ช็อกโกแลตชิพ คุกกี้เนยสด และคุกกี้ดับเบิลช็อกโกแลตค่ะ 🍪
ถ้าชอบเข้ม ๆ แนะนำดับเบิลช็อกโกแลต ถ้าชอบนุ่มหอม แนะนำเนยสดค่ะ`;

const priceText = `ราคาคุกกี้ของร้านเริ่มประมาณ 45–69 บาท แล้วแต่เมนูค่ะ
ถ้าซื้อครบ 150 บาท จะได้รับสิทธิ์สุ่มไพ่ Cookie Fortune ฟรี 1 ใบด้วยนะคะ 🔮`;

const openTimeText = `ร้าน CookieCloudyDay เปิดทุกวัน เวลา 10:00–20:00 น. ค่ะ
สามารถเลือกเมนู สั่งซื้อ และดูโปรสมาชิกได้จากหน้าเว็บเลยค่ะ`;

const giftText = `ถ้าซื้อฝาก แนะนำเซ็ตคุกกี้หลายรสค่ะ 🎁
เลือกเป็นช็อกโกแลตชิพ + เนยสด + เรดเวลเวท จะดูน่ารักและกินง่าย เหมาะเป็นของฝากมากค่ะ`;

const fortuneText = `ถ้าซื้อครบ 150 บาท จะได้สุ่มไพ่ Cookie Fortune ฟรี 1 ใบค่ะ 🔮
ไพ่จะมีข้อความน่ารัก ๆ จากร้าน พร้อมคำแนะนำเมนูที่เหมาะกับคุณ`;

const orderText = `ถ้าต้องการสั่งซื้อ ให้สมัคร Cookie Club ก่อนนะคะ
จากนั้นกรอกเบอร์โทรหรืออีเมลในช่องสั่งซื้อ แล้วเลือกเมนูและจำนวนได้เลยค่ะ`;

export function generateDemiReply(input: string): DemiReply {
  const raw = input.trim();
  const message = raw.toLowerCase();

  // Special: order summary payloads prefixed with ORDER_SUMMARY:
  if (raw.startsWith("ORDER_SUMMARY:")) {
    try {
      const payload = JSON.parse(raw.replace(/^ORDER_SUMMARY:\s*/i, ""));
      const parts: string[] = [];

      parts.push(`สรุปออเดอร์: เลขออเดอร์ ${payload.orderId || "-"}`);

      if (payload.menu) {
        parts.push(`${payload.menu} x${payload.quantity ?? 1}`);
      }

      parts.push(`รวม ${payload.total ?? "-"} บาท`);

      if (payload.promoEligible) {
        const cardName = payload.cardName || payload.cardRecommend || "Cookie Fortune";
        const emoji = payload.cardEmoji ? ` ${payload.cardEmoji}` : "";
        parts.push(`ยินดีด้วยค่ะ คุณได้รับสิทธิ์สุ่มไพ่: ${cardName}${emoji}`);
        if (payload.cardFreebieText) parts.push(payload.cardFreebieText);
        if (payload.cardMessage) parts.push(`ข้อความบนการ์ด: ${payload.cardMessage}`);
      } else {
        parts.push("ขณะนี้ยังไม่ถึงโปรสุ่มไพ่");
      }

      return { intent: "order", text: parts.join(" \n") };
    } catch (e) {
      return { intent: "order", text: "สรุปออเดอร์: (ข้อมูลไม่ครบหรือส่งผิดรูปแบบ)" };
    }
  }

  if (
    message.includes("เมนู") ||
    message.includes("แนะนำ") ||
    message.includes("กินอะไร") ||
    message.includes("อร่อย")
  ) {
    return { intent: "menu", text: menuText };
  }

  if (
    message.includes("ราคา") ||
    message.includes("บาท") ||
    message.includes("เท่าไหร่") ||
    message.includes("เท่าไร")
  ) {
    return { intent: "price", text: priceText };
  }

  if (
    message.includes("เวลา") ||
    message.includes("เปิด") ||
    message.includes("ปิด") ||
    message.includes("กี่โมง")
  ) {
    return { intent: "openTime", text: openTimeText };
  }

  if (
    message.includes("ฝาก") ||
    message.includes("ของขวัญ") ||
    message.includes("ของฝาก") ||
    message.includes("เซ็ต")
  ) {
    return { intent: "gift", text: giftText };
  }

  if (
    message.includes("ไพ่") ||
    message.includes("สุ่ม") ||
    message.includes("fortune") ||
    message.includes("ดวง")
  ) {
    return { intent: "fortune", text: fortuneText };
  }

  if (
    message.includes("สั่ง") ||
    message.includes("ซื้อ") ||
    message.includes("ออเดอร์") ||
    message.includes("order")
  ) {
    return { intent: "order", text: orderText };
  }

  return {
    intent: "help",
    text: `Demi ช่วยตอบเรื่องเมนู ราคา เวลาเปิดร้าน ของฝาก โปรสมาชิก และสุ่มไพ่ Cookie Fortune ได้ค่ะ
ลองถามว่า “เมนูอะไรแนะนำบ้าง”, “คุกกี้ราคาเท่าไหร่” หรือ “ซื้อฝากแนะนำอะไรดี” ได้เลยนะคะ 😊`,
  };
}
