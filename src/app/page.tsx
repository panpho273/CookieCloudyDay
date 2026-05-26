"use client";

import { useEffect, useMemo, useState } from "react";

const menus = [
  {
    name: "คุกกี้ช็อกโกแลตชิพ",
    price: 45,
    emoji: "🍪",
    desc: "เมนูคลาสสิก หอมเนย ช็อกโกแลตแน่น",
  },
  {
    name: "คุกกี้คอร์นเฟลกคาราเมล",
    price: 55,
    emoji: "🌽",
    desc: "กรอบ หอมคาราเมล เหมาะกับสายกรุบ",
  },
  {
    name: "คุกกี้ชาเขียวมัทฉะ",
    price: 59,
    emoji: "🍵",
    desc: "หอมชาเขียว นุ่มละมุน ไม่หวานเกิน",
  },
  {
    name: "คุกกี้เรดเวลเวท",
    price: 65,
    emoji: "❤️",
    desc: "สีสวย รสนุ่ม เหมาะเป็นของขวัญ",
  },
  {
    name: "คุกกี้ดับเบิ้ลช็อกโกแลต",
    price: 59,
    emoji: "🍫",
    desc: "ช็อกโกแลตเข้ม สำหรับสายหวาน",
  },
  {
    name: "คุกกี้นูเทลล่า",
    price: 69,
    emoji: "🌰",
    desc: "เข้มข้น หอมมัน ฟีลพรีเมียม",
  },
];

type Review = {
  rating: number;
  comment: string;
  createdAt: string;
};


type DemiMessage = {
  role: "bot" | "user";
  text: string;
  time: string;
};

function getThaiTime() {
  return new Date().toLocaleTimeString("th-TH", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getDemiReply(message: string) {
  const text = message.toLowerCase();

  if (
    text.includes("เมนู") ||
    text.includes("แนะนำ") ||
    text.includes("อะไรอร่อย") ||
    text.includes("คุกกี้")
  ) {
    return "เมนูแนะนำของร้านวันนี้คือ คุกกี้เรดเวลเวท, คุกกี้ดับเบิ้ลช็อกโกแลต และคุกกี้นูเทลล่าค่ะ 🍪 ถ้าชอบหวานละมุน Demi แนะนำเรดเวลเวทเลย";
  }

  if (
    text.includes("ราคา") ||
    text.includes("กี่บาท") ||
    text.includes("เท่าไหร่")
  ) {
    return "คุกกี้ของร้านเริ่มต้นประมาณ 55–69 บาทต่อชิ้นค่ะ แล้วแต่รสชาติ ถ้าอยากได้แนวเข้มข้น Demi แนะนำดับเบิ้ลช็อกโกแลตค่ะ";
  }

  if (
    text.includes("เปิด") ||
    text.includes("ปิด") ||
    text.includes("เวลา")
  ) {
    return "ร้านเปิดทุกวันเวลา 10:00–20:00 น. ค่ะ 💜";
  }

  if (
    text.includes("ของฝาก") ||
    text.includes("ซื้อฝาก") ||
    text.includes("ฝาก")
  ) {
    return "ถ้าซื้อเป็นของฝาก Demi แนะนำคุกกี้เรดเวลเวทกับคุกกี้นูเทลล่าค่ะ หน้าตาน่ารัก กินง่าย และถูกใจหลายคน";
  }

  if (
    text.includes("ช็อกโกแลต") ||
    text.includes("เข้ม") ||
    text.includes("หวาน")
  ) {
    return "ถ้าชอบช็อกโกแลตเข้ม ๆ Demi แนะนำคุกกี้ดับเบิ้ลช็อกโกแลตค่ะ แต่ถ้าชอบหวานละมุน ลองเรดเวลเวทได้เลย";
  }

  if (
    text.includes("โปร") ||
    text.includes("โปรโมชั่น") ||
    text.includes("150") ||
    text.includes("ไพ่") ||
    text.includes("สุ่ม")
  ) {
    return "โปร Cookie Fortune สำหรับสมาชิก: ซื้อคุกกี้ครบ 150 บาท รับสิทธิ์สุ่มไพ่ฟรี 1 ใบ พร้อมข้อความในการ์ดน่ารัก ๆ จาก CookieCloudyDay ค่ะ 🔮🍪";
  }

  return "Demi ช่วยแนะนำเมนู ราคา เวลาเปิดร้าน โปรโมชัน และคุกกี้ที่เหมาะกับคุณได้นะคะ ลองพิมพ์ว่า “เมนูแนะนำ”, “ราคาเท่าไหร่” หรือกด “สุ่มไพ่” ได้เลย 🍪";
}

function DemiBotIcon() {
  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="demiBotSvg"
      aria-hidden="true"
    >
      <rect x="16" y="18" width="32" height="24" rx="12" fill="#ffffff" />
      <rect x="20" y="22" width="24" height="16" rx="8" fill="#c4b5fd" />
      <circle cx="28" cy="30" r="2.2" fill="#5b3b91" />
      <circle cx="36" cy="30" r="2.2" fill="#5b3b91" />
      <rect x="29" y="12" width="6" height="8" rx="3" fill="#c4b5fd" />
      <circle cx="32" cy="10" r="3" fill="#f9a8d4" />
      <rect x="26" y="35" width="12" height="3.5" rx="1.75" fill="#8b5cf6" />
      <rect x="12" y="24" width="5" height="11" rx="2.5" fill="#e9d5ff" />
      <rect x="47" y="24" width="5" height="11" rx="2.5" fill="#e9d5ff" />
      <rect x="22" y="42" width="5" height="8" rx="2.5" fill="#ddd6fe" />
      <rect x="37" y="42" width="5" height="8" rx="2.5" fill="#ddd6fe" />
    </svg>
  );
}


export default function HomePage() {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [reviews, setReviews] = useState<Review[]>([]);

  
  
  
  const cookieMenus = [
    { name: "คุกกี้เรดเวลเวท", price: 59 },
    { name: "คุกกี้ดับเบิ้ลช็อกโกแลต", price: 69 },
    { name: "คุกกี้นูเทลล่า", price: 69 },
    { name: "คุกกี้เนยสด", price: 55 },
    { name: "คุกกี้ช็อกโกแลตชิพ", price: 59 },
  ];

  const [memberForm, setMemberForm] = useState({
    name: "",
    phone: "",
    email: "",
    birthday: "",
    favoriteCookie: "",
  });

  const [orderForm, setOrderForm] = useState({
    memberKey: "",
    menu: "คุกกี้เรดเวลเวท",
    quantity: 1,
  });

  const [shopMessage, setShopMessage] = useState("");
  const [orderResult, setOrderResult] = useState<{
    orderId?: string;
    promoEligible?: boolean;
    cardName?: string;
    cardMessage?: string;
  } | null>(null);

  const selectedCookie =
    cookieMenus.find((item) => item.name === orderForm.menu) || cookieMenus[0];

  const orderTotal = selectedCookie.price * Number(orderForm.quantity || 1);

  async function submitMember() {
    setShopMessage("");

    try {
      const res = await fetch("/api/members/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(memberForm),
      });

      const data = await res.json();

      if (!res.ok || !data.ok) {
        throw new Error(data.message || "สมัครสมาชิกไม่สำเร็จ");
      }

      setShopMessage(
        data.alreadyMember
          ? `เป็นสมาชิกอยู่แล้วค่ะ รหัสสมาชิก ${data.member.memberCode}`
          : `สมัครสมาชิกสำเร็จค่ะ รหัสสมาชิก ${data.member.memberCode}`
      );

      setOrderForm((prev) => ({
        ...prev,
        memberKey: memberForm.phone || memberForm.email,
      }));
    } catch (error) {
      setShopMessage(
        error instanceof Error ? error.message : "สมัครสมาชิกไม่สำเร็จ"
      );
    }
  }

  async function submitOrder() {
    setShopMessage("");
    setOrderResult(null);

    try {
      const res = await fetch("/api/orders/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...orderForm,
          quantity: Number(orderForm.quantity || 1),
          total: orderTotal,
        }),
      });

      const data = await res.json();

      if (!res.ok || !data.ok) {
        throw new Error(data.message || "สั่งซื้อไม่สำเร็จ");
      }

      setOrderResult(data.order);
      setShopMessage("บันทึกออเดอร์สำเร็จค่ะ");
    } catch (error) {
      setShopMessage(
        error instanceof Error ? error.message : "สั่งซื้อไม่สำเร็จ"
      );
    }
  }

const [isDemiOpen, setIsDemiOpen] = useState(true);
  const [demiInput, setDemiInput] = useState("");
  const [demiMessages, setDemiMessages] = useState<DemiMessage[]>([
    {
      role: "bot",
      text: "สวัสดีค่ะ! ยินดีให้บริการ มีอะไรให้ช่วยไหมคะ? 😊",
      time: getThaiTime(),
    },
  ]);

  function sendDemiMessage(preset?: string) {
    const finalText = (preset ?? demiInput).trim();

    if (!finalText) return;

    const userMessage: DemiMessage = {
      role: "user",
      text: finalText,
      time: getThaiTime(),
    };

    setDemiMessages((prev) => [...prev, userMessage]);
    setDemiInput("");

    setTimeout(() => {
      const botMessage: DemiMessage = {
        role: "bot",
        text: getDemiReply(finalText),
        time: getThaiTime(),
      };

      setDemiMessages((prev) => [...prev, botMessage]);
    }, 350);
  }
function getDemiReply(message: string) {
    const msg = message.toLowerCase();

    if (msg.includes("เมนู") || msg.includes("แนะนำ") || msg.includes("คุกกี้")) {
      return "เมนูแนะนำของร้านคือคุกกี้ช็อกโกแลตชิพ คุกกี้เนยสด และคุกกี้ดับเบิลช็อกโกแลตค่ะ 🍪";
    }

    if (msg.includes("ราคา") || msg.includes("กี่บาท") || msg.includes("เท่าไหร่")) {
      return "ราคาคุกกี้เริ่มประมาณ 45–69 บาท แล้วแต่เมนูค่ะ ดูเมนูยอดฮิตด้านบนของเว็บได้เลยนะคะ";
    }

    if (msg.includes("เปิด") || msg.includes("เวลา") || msg.includes("ร้าน")) {
      return "ร้าน CookieCloudyDay เปิดทุกวัน เวลา 10:00–20:00 น. ค่ะ";
    }

    if (msg.includes("ของฝาก") || msg.includes("ฝาก") || msg.includes("ของขวัญ")) {
      return "ถ้าซื้อเป็นของฝาก แนะนำคุกกี้เนยสดหรือคุกกี้ช็อกโกแลตชิพค่ะ แพ็กเกจน่ารักและรสชาติทานง่ายมาก";
    }

    if (msg.includes("สั่ง") || msg.includes("ออเดอร์")) {
      return "ตอนนี้สามารถดูเมนูและสอบถาม Demi ได้ก่อนค่ะ หากต้องการสั่งซื้อ ให้ติดต่อร้านตามช่องทางที่ร้านแจ้งไว้ได้เลย";
    }

    return "Demi ยังตอบแบบสั้น ๆ บนหน้าเว็บนะคะ ถ้าอยากคุยแบบเต็ม ให้กดปุ่มเปิดผู้ช่วย Demiได้เลยค่ะ 💜";
  }


  const avgRating = useMemo(() => {
    if (!reviews.length) return "0.0";
    const avg = reviews.reduce((sum, review) => sum + review.rating, 0) / reviews.length;
    return avg.toFixed(1);
  }, [reviews]);

  useEffect(() => {
    async function loadReviews() {
      try {
        const res = await fetch(`/api/reviews?t=${Date.now()}`, {
          cache: "no-store",
          headers: {
            "Cache-Control": "no-cache",
          },
        });

        const data = await res.json();

        if (res.ok && data.ok && Array.isArray(data.reviews)) {
          setReviews(data.reviews);
        }
      } catch {
        // ถ้าโหลดจาก Google Sheet ไม่ได้ ให้หน้าเว็บยังไม่พัง
      }
    }

    loadReviews();
  }, []);

  async function submitReview() {
    if (!comment.trim()) {
      setError("กรุณาเขียนรีวิวก่อนส่ง");
      return;
    }

    setSending(true);
    setError("");

    try {
      const res = await fetch(`/api/reviews?t=${Date.now()}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          rating,
          comment,
          source: "CookieCloudyDay Website",
        }),
      });

      const data = await res.json();

      if (!res.ok || !data.ok) {
        throw new Error(data.message || "Cannot submit review");
      }

      const newReview: Review = {
        rating,
        comment,
        createdAt: new Date().toLocaleString("th-TH"),
      };

      setReviews((prev) => [newReview, ...prev]);
      setComment("");
      setRating(5);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "ส่งรีวิวไม่สำเร็จ ลองใหม่อีกครั้ง");
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="page">
      <nav className="nav">
        <div className="brand">
          <div className="logo">☁️</div>
          <span>CookieCloudyDay</span>
        </div>

        <div className="navLinks">
          <a href="#menu">เมนู</a>
          <a href="#reviews">รีวิว</a>
          <a href="#demi">Demi</a>
          <a href="/admin/login" className="adminPill">Admin</a>
        </div>
      </nav>

      <section className="hero">
        <div>
          <div className="badge">Fresh Homemade Cookies</div>
          <h1>CookieCloudyDay</h1>
          <p>
            ถามเมนู เวลาเปิดร้าน ราคา หรือให้ Demi ช่วยแนะนำคุกกี้ที่เหมาะกับคุณได้เลย
            พร้อมระบบรีวิว 1–5 ดาว และหน้า Admin สำหรับดูข้อมูลหลังบ้าน
          </p>

          <div className="heroActions">
            <a className="btn primary" href="#demi">เลือกคุกกี้กับDemi</a>
            <a className="btn secondary" href="#menu">ดูเมนูคุกกี้</a>
          </div>
        </div>

        <div className="heroCard">
          <div className="cookiePreview">🍪</div>
        </div>
      </section>

      <section id="menu" className="section">
        <div className="sectionHeader">
          <h2>เมนูแนะนำ</h2>
          <p>ตัวอย่างเมนูฮิตของร้าน CookieCloudyDay</p>
        </div>

        <div className="grid">
          {menus.map((menu) => (
            <article className="card" key={menu.name}>
              <div className="menuTop">
                <span className="menuEmoji">{menu.emoji}</span>
                <span className="price">{menu.price} บาท</span>
              </div>
              <h3>{menu.name}</h3>
              <p>{menu.desc}</p>
            </article>
          ))}
        </div>
      </section>


      <section id="member" className="section memberSection">
        <div className="memberShell">
          <div className="memberHero">
            <span className="miniBadge">Cookie Club Member</span>
            <h2>สมัครสมาชิกก่อนสั่งซื้อ</h2>
            <p>
              สมัคร Cookie Club เพื่อใช้สิทธิ์โปรโมชันของร้าน
              เมื่อซื้อครบ 150 บาท รับสิทธิ์สุ่มไพ่ Cookie Fortune ฟรี
              พร้อมข้อความน่ารักในการ์ดจากร้าน
            </p>

            <div className="promoCard">
              <div className="promoIcon">🔮</div>
              <div>
                <h3>โปร Cookie Fortune</h3>
                <p>
                  สมาชิกซื้อคุกกี้ครบ 150 บาท สุ่มไพ่ฟรี 1 ใบ
                  พร้อมข้อความในการ์ดพิเศษจาก CookieCloudyDay
                </p>
              </div>
            </div>
          </div>

          <div className="memberGrid">
            <div className="shopPanel">
              <h3>สมัครสมาชิก</h3>

              <div className="formGrid">
                <input
                  value={memberForm.name}
                  onChange={(e) =>
                    setMemberForm({ ...memberForm, name: e.target.value })
                  }
                  placeholder="ชื่อสมาชิก"
                />

                <input
                  value={memberForm.phone}
                  onChange={(e) =>
                    setMemberForm({ ...memberForm, phone: e.target.value })
                  }
                  placeholder="เบอร์โทร"
                />

                <input
                  value={memberForm.email}
                  onChange={(e) =>
                    setMemberForm({ ...memberForm, email: e.target.value })
                  }
                  placeholder="อีเมล"
                />

                <input
                  type="date"
                  value={memberForm.birthday}
                  onChange={(e) =>
                    setMemberForm({ ...memberForm, birthday: e.target.value })
                  }
                />

                <input
                  className="fullInput"
                  value={memberForm.favoriteCookie}
                  onChange={(e) =>
                    setMemberForm({
                      ...memberForm,
                      favoriteCookie: e.target.value,
                    })
                  }
                  placeholder="รสคุกกี้ที่ชอบ เช่น ช็อกโกแลต / เนยสด"
                />
              </div>

              <button type="button" className="shopButton" onClick={submitMember}>
                สมัคร Cookie Club
              </button>
            </div>

            <div className="shopPanel">
              <h3>สั่งซื้อสำหรับสมาชิก</h3>

              <div className="formGrid">
                <input
                  className="fullInput"
                  value={orderForm.memberKey}
                  onChange={(e) =>
                    setOrderForm({ ...orderForm, memberKey: e.target.value })
                  }
                  placeholder="กรอกเบอร์โทร / อีเมล / รหัสสมาชิก"
                />

                <select
                  value={orderForm.menu}
                  onChange={(e) =>
                    setOrderForm({ ...orderForm, menu: e.target.value })
                  }
                >
                  {cookieMenus.map((item) => (
                    <option key={item.name} value={item.name}>
                      {item.name} - {item.price} บาท
                    </option>
                  ))}
                </select>

                <input
                  type="number"
                  min="1"
                  value={orderForm.quantity}
                  onChange={(e) =>
                    setOrderForm({
                      ...orderForm,
                      quantity: Number(e.target.value),
                    })
                  }
                  placeholder="จำนวน"
                />
              </div>

              <div className="orderSummary">
                <span>ยอดรวม</span>
                <strong>{orderTotal} บาท</strong>
                <small>
                  {orderTotal >= 150
                    ? "ถึงโปรสุ่มไพ่ Cookie Fortune แล้ว"
                    : `ซื้อเพิ่มอีก ${150 - orderTotal} บาท เพื่อรับสิทธิ์สุ่มไพ่`}
                </small>
              </div>

              <button type="button" className="shopButton" onClick={submitOrder}>
                บันทึกออเดอร์
              </button>
            </div>
          </div>

          {shopMessage && <div className="shopMessage">{shopMessage}</div>}

          {orderResult && (
            <div className="fortuneResult">
              <span>เลขออเดอร์: {orderResult.orderId}</span>

              {orderResult.promoEligible ? (
                <>
                  <h3>คุณได้รับไพ่ {orderResult.cardName}</h3>
                  <p>{orderResult.cardMessage}</p>
                </>
              ) : (
                <p>ออเดอร์นี้ยังไม่ถึงโปรสุ่มไพ่ ซื้อครบ 150 บาทครั้งหน้ารับสิทธิ์ได้เลยค่ะ</p>
              )}
            </div>
          )}
        </div>
      </section>

      <section id="reviews" className="section">
        <div className="sectionHeader">
          <h2>รีวิวจากลูกค้า</h2>
          <p>คะแนนเฉลี่ย {avgRating} / 5 จาก {reviews.length} รีวิว</p>
        </div>

        <div className="reviewBox">
          <div className="panel">
            <h3>ให้คะแนนร้าน ⭐</h3>

            <div className="reviewForm">
              {error && <div className="errorBox">{error}</div>}

              <div className="stars">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    className={`starBtn ${star <= rating ? "active" : ""}`}
                    onClick={() => setRating(star)}
                    aria-label={`${star} stars`}
                  >
                    ★
                  </button>
                ))}
              </div>

              <textarea
                className="textarea"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="บอกความรู้สึกหลังใช้บริการ หรือแนะนำร้านเพิ่มเติม..."
              />

              <button className="btn primary" onClick={submitReview} disabled={sending}>
                {sending ? "กำลังส่ง..." : `ส่งรีวิว ${rating} ดาว`}
              </button>
            </div>
          </div>

          <div className="panel">
            <h3>รีวิวล่าสุด</h3>

            <div className="reviewList">
              {reviews.map((review, index) => (
                <div className="reviewItem" key={`${review.createdAt}-${index}`}>
                  <div className="reviewStars">
                    {"★".repeat(review.rating)}
                    {"☆".repeat(5 - review.rating)}
                  </div>
                  <p>{review.comment}</p>
                  <small>{review.createdAt}</small>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
      <section id="demi" className="section demiSection">
        <div className="demiShell">
          <div className="demiIntro">
            <span className="demiBadge">Demi AI Assistant</span>

            <h2>คุยกับ Demi</h2>

            <p className="demiLead">
              CookieCloudyDay คือร้านคุกกี้โฮมเมดโทนอบอุ่น หอมเนย
              หวานละมุน และมีหลายรสให้เลือก ส่วน Demi เป็นผู้ช่วยตัวน้อยของร้าน
              ที่ช่วยแนะนำเมนู ราคา เวลาเปิดร้าน และช่วยเลือกคุกกี้ที่เหมาะกับคุณได้ง่ายขึ้น
            </p>

            <div className="demiInfoCard">
              <div className="demiInfoIcon">
                <DemiBotIcon />
              </div>

              <div className="demiInfoText">
                <h3>Demi พร้อมช่วยแล้วค่ะ</h3>
                <p>
                  ลองถามเรื่องเมนู ราคา เวลาเปิดร้าน
                  หรือขอให้แนะนำคุกกี้สำหรับกินเล่นและซื้อฝากได้เลย
                </p>
              </div>
            </div>

            <div className="demiQuickButtons">
              <button type="button" onClick={() => sendDemiMessage("เมนูแนะนำ")}>
                🍪 เมนูแนะนำ
              </button>
              <button type="button" onClick={() => sendDemiMessage("ราคาเท่าไหร่")}>
                💸 ราคา
              </button>
              <button type="button" onClick={() => sendDemiMessage("เวลาเปิดร้าน")}>
                ⏰ เวลาเปิดร้าน
              </button>
              <button type="button" onClick={() => sendDemiMessage("แนะนำคุกกี้ซื้อฝาก")}>
                🎁 ของฝาก
              </button>
              <button type="button" onClick={drawFortuneCard}>
                🔮 สุ่มไพ่
              </button>
            </div>
          </div>

          <div className="demiChatCard">
            <div className="demiChatHeader">
              <div className="demiHeaderLeft">
                <div className="demiAvatar">
                  <DemiBotIcon />
                </div>

                <div className="demiHeaderText">
                  <h3>Demi</h3>
                  <span>ออนไลน์</span>
                </div>
              </div>

              <button
                type="button"
                className="demiToggleBtn"
                onClick={() => setIsDemiOpen((prev) => !prev)}
                aria-label="toggle chat"
              >
                {isDemiOpen ? "−" : "+"}
              </button>
            </div>

            {isDemiOpen && (
              <>
                <div className="demiSuggestionRow">
                  <button type="button" onClick={() => sendDemiMessage("เมนูแนะนำ")}>
                    เมนูแนะนำ
                  </button>
                  <button type="button" onClick={() => sendDemiMessage("คุกกี้รสไหนขายดี")}>
                    รสขายดี
                  </button>
                  <button type="button" onClick={() => sendDemiMessage("แนะนำคุกกี้ซื้อฝาก")}>
                    ซื้อฝาก
                  </button>
                  <button type="button" onClick={drawFortuneCard}>
                    สุ่มไพ่
                  </button>
                </div>

                <div className="demiMessages">
                  {demiMessages.map((msg, index) => (
                    <div
                      key={`${msg.time}-${index}`}
                      className={`demiMessage ${msg.role === "user" ? "user" : "bot"}`}
                    >
                      {msg.role === "bot" && (
                        <div className="demiMessageIcon">
                          <DemiBotIcon />
                        </div>
                      )}

                      <div className="demiBubbleWrap">
                        <div className="demiBubble">{msg.text}</div>
                        <small>{msg.time}</small>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="demiComposer">
                  <input
                    type="text"
                    value={demiInput}
                    onChange={(e) => setDemiInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        sendDemiMessage();
                      }
                    }}
                    placeholder='เช่น "เมนูอะไรแนะนำบ้าง"'
                    className="demiInput"
                  />

                  <button
                    type="button"
                    className="demiSendBtn"
                    onClick={() => sendDemiMessage()}
                  >
                    ส่ง
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </section>


      <footer className="footer">
        CookieCloudyDay © 2026 | Pastel Cookie Cloud Experience
      </footer>
</main>
  );
}
