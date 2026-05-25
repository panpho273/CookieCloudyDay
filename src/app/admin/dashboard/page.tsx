"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

type Review = {
  rating: number;
  comment: string;
  createdAt: string;
};

export default function AdminDashboardPage() {
  const router = useRouter();

  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("adminToken");

    if (!token) {
      router.push("/admin/login");
      return;
    }

    fetch("/api/reviews")
      .then((res) => res.json())
      .then((data) => {
        setReviews(data.reviews || []);
      })
      .catch(() => {
        setReviews([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [router]);

  const average = useMemo(() => {
    if (!reviews.length) return "0.0";
    const avg = reviews.reduce((sum, review) => sum + review.rating, 0) / reviews.length;
    return avg.toFixed(1);
  }, [reviews]);

  function logout() {
    localStorage.removeItem("adminToken");
    router.push("/admin/login");
  }

  return (
    <main className="page">
      <div className="dashboard">
        <div className="sectionHeader">
          <h1>Admin Dashboard</h1>
          <p>สรุปข้อมูลรีวิวและระบบ CookieCloudyDay</p>
        </div>

        <div className="heroActions" style={{ marginBottom: 24 }}>
          <a className="btn secondary" href="/">
            กลับหน้าเว็บ
          </a>

          <button className="btn primary" onClick={logout}>
            ออกจากระบบ
          </button>
        </div>

        <div className="statGrid">
          <div className="panel stat">
            <h3>จำนวนรีวิว</h3>
            <h2>{reviews.length}</h2>
          </div>

          <div className="panel stat">
            <h3>คะแนนเฉลี่ย</h3>
            <h2>{average}</h2>
          </div>

          <div className="panel stat">
            <h3>สถานะ</h3>
            <h2>Ready</h2>
          </div>
        </div>

        <div className="panel">
          <h2>รีวิวล่าสุด</h2>

          {loading ? (
            <p>กำลังโหลดข้อมูล...</p>
          ) : (
            <div className="tableWrap">
              <table>
                <thead>
                  <tr>
                    <th>คะแนน</th>
                    <th>ความคิดเห็น</th>
                    <th>วันที่</th>
                  </tr>
                </thead>

                <tbody>
                  {reviews.map((review, index) => (
                    <tr key={`${review.createdAt}-${index}`}>
                      <td>
                        {"★".repeat(review.rating)}
                        {"☆".repeat(5 - review.rating)}
                      </td>
                      <td>{review.comment}</td>
                      <td>{review.createdAt}</td>
                    </tr>
                  ))}

                  {!reviews.length && (
                    <tr>
                      <td colSpan={3}>ยังไม่มีข้อมูลรีวิว</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
