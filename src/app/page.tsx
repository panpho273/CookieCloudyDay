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

export default function HomePage() {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [reviews, setReviews] = useState<Review[]>([]);

  
  const [demiOpen, setDemiOpen] = useState(false);
  const [demiInput, setDemiInput] = useState("");
  const [demiMessages, setDemiMessages] = useState([
    {
      role: "bot",
      text: "สวัสดีค่ะ! ยินดีให้บริการ มีอะไรให้ช่วยไหมคะ? 😊",
    },
  ]);

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

    return "Demi ยังตอบแบบสั้น ๆ บนหน้าเว็บนะคะ ถ้าอยากคุยแบบเต็ม ให้กดปุ่มเปิด Demi AI ตัวเต็มได้เลยค่ะ 💜";
  }

  function sendDemiMessage() {
    const cleanInput = demiInput.trim();

    if (!cleanInput) return;

    const userMessage = {
      role: "user",
      text: cleanInput,
    };

    const botMessage = {
      role: "bot",
      text: getDemiReply(cleanInput),
    };

    setDemiMessages((prev) => [...prev, userMessage, botMessage]);
    setDemiInput("");
  }

const streamlitUrl = "https://cookiecloudyday-demi.streamlit.app/";

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
          <a href="#demi">Demi AI</a>
          <a href="/admin/login" className="adminPill">Admin</a>
        </div>
      </nav>

      <section className="hero">
        <div>
          <div className="badge">CookieCloudyDay Assistant</div>
          <h1>Demi ผู้ช่วย AI ของร้านคุกกี้</h1>
          <p>
            ถามเมนู เวลาเปิดร้าน ราคา หรือให้ Demi ช่วยแนะนำคุกกี้ที่เหมาะกับคุณได้เลย
            พร้อมระบบรีวิว 1–5 ดาว และหน้า Admin สำหรับดูข้อมูลหลังบ้าน
          </p>

          <div className="heroActions">
            <a className="btn primary" href="#demi">คุยกับ Demi</a>
            <a className="btn secondary" href="#menu">ดูเมนูยอดนิยม</a>
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
      <section id="demi" className="section demiInfoSection">
        <div className="demiInfoCard">
          <span className="miniBadge">Demi AI Assistant</span>
          <h2>คุยกับ Demi AI</h2>
          <p>
            กดปุ่มแชทมุมขวาล่างเพื่อคุยกับ Demi แบบรวดเร็ว
            หรือเปิด Demi AI ตัวเต็มเพื่อถามเมนู ราคา และคำแนะนำเกี่ยวกับคุกกี้ของร้าน
          </p>

          <button
            type="button"
            className="demiInfoButton"
            onClick={() => setDemiOpen(true)}
          >
            เปิดกล่องแชท Demi
          </button>

          <a
            href={streamlitUrl}
            target="_blank"
            rel="noreferrer"
            className="demiInfoLink"
          >
            เปิด Demi AI ตัวเต็ม
          </a>
        </div>
      </section>

      <footer className="footer">
        CookieCloudyDay © 2026 | Pastel Cookie Cloud Experience
      </footer>
      <div className={`demiFloatingWidget ${demiOpen ? "open" : ""}`}>
        {demiOpen && (
          <div className="demiChatWindow">
            <div className="demiChatHeader">
              <div className="demiAvatar">✣</div>
              <div>
                <h3>Demi AI</h3>
                <p><span></span> ออนไลน์</p>
              </div>

              <button
                type="button"
                className="demiCloseBtn"
                onClick={() => setDemiOpen(false)}
                aria-label="ปิดแชท Demi"
              >
                ×
              </button>
            </div>

            <div className="demiChatBody">
              {demiMessages.map((message, index) => (
                <div
                  className={`demiMessage ${message.role === "user" ? "user" : "bot"}`}
                  key={`${message.role}-${index}`}
                >
                  {message.text}
                </div>
              ))}
            </div>

            <div className="demiChatFooter">
              <a
                href={streamlitUrl}
                target="_blank"
                rel="noreferrer"
                className="demiMenuBtn"
                title="เปิด Demi AI ตัวเต็ม"
              >
                ☰
              </a>

              <input
                value={demiInput}
                onChange={(e) => setDemiInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    sendDemiMessage();
                  }
                }}
                placeholder='เช่น "มีเมนูอะไรแนะนำบ้าง"...'
              />

              <button
                type="button"
                className="demiSendBtn"
                onClick={sendDemiMessage}
                aria-label="ส่งข้อความ"
              >
                ➤
              </button>
            </div>
          </div>
        )}

        <button
          type="button"
          className="demiFloatingButton"
          onClick={() => setDemiOpen((prev) => !prev)}
          aria-label="เปิดแชท Demi"
        >
          🤖
          <span></span>
        </button>
      </div>

    </main>
  );
}
