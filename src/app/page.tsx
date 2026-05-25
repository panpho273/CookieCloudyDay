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

  const streamlitUrl =
  process.env.NEXT_PUBLIC_STREAMLIT_URL ||
  "https://cookiecloudyday-demi.streamlit.app/";

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
      <section id="demi" className="section demiSection">
        <div className="demiUnifiedCard">
          <div className="demiTop">
            <div>
              <span className="miniBadge">Demi AI Assistant</span>
              <h2>คุยกับ Demi AI</h2>
              <p>
                ผู้ช่วย AI ของ CookieCloudyDay สำหรับถามเมนู ราคา เวลาเปิดร้าน
                และช่วยแนะนำคุกกี้ที่เหมาะกับคุณ
              </p>
            </div>

            <div className="demiFloatingIcon">💬</div>
          </div>

          <div className="demiContent">
            <div className="demiSide">
              <div className="demiBotIcon">🤖</div>

              <h3>Demi พร้อมช่วยแล้วค่ะ</h3>
              <p>
                ลองถาม Demi ได้เลย เช่น เมนูแนะนำ ราคา หรือคุกกี้ที่เหมาะกับการซื้อเป็นของฝาก
              </p>

              <div className="demiQuickActions">
                <a
                  href={streamlitUrl || "#demi"}
                  target={streamlitUrl ? "_blank" : undefined}
                  rel={streamlitUrl ? "noreferrer" : undefined}
                  className="demiQuickBtn"
                >
                  🍪 ถามเมนู
                </a>

                <a
                  href={streamlitUrl || "#demi"}
                  target={streamlitUrl ? "_blank" : undefined}
                  rel={streamlitUrl ? "noreferrer" : undefined}
                  className="demiQuickBtn"
                >
                  💜 แนะนำรสชาติ
                </a>

                <a
                  href={streamlitUrl || "#demi"}
                  target={streamlitUrl ? "_blank" : undefined}
                  rel={streamlitUrl ? "noreferrer" : undefined}
                  className="demiQuickBtn"
                >
                  🛒 ช่วยสรุปออเดอร์
                </a>
              </div>

              {streamlitUrl && (
                <a
                  href={streamlitUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="demiOpenBtn"
                >
                  เปิด Demi AI แบบเต็มหน้า
                </a>
              )}
            </div>

            <div className="demiChatPanel">
              {streamlitUrl ? (
                <>
                  <iframe
                    className="demiIframe"
                    src={streamlitUrl}
                    title="CookieCloudyDay Demi AI"
                  />

                  <div className="demiIframeNote">
                    ถ้ากล่องแชทโหลดไม่ขึ้น ให้กด “เปิด Demi AI แบบเต็มหน้า”
                  </div>
                </>
              ) : (
                <div className="demiMissingCard">
                  <h3>ยังไม่ได้ตั้งค่า Streamlit URL</h3>
                  <p>
                    เพิ่มค่า <b>NEXT_PUBLIC_STREAMLIT_URL</b> ใน Vercel Environment Variables
                    แล้ว Redeploy เพื่อให้หน้าแชท Demi แสดงตรงนี้
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      <footer className="footer">
        CookieCloudyDay © 2026 | Pastel Cookie Cloud Experience
      </footer>
    </main>
  );
}
