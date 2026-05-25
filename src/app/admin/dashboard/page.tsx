"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

type Review = {
  rating: number;
  comment: string;
  createdAt: string;
};

type DashboardData = {
  totalOrders: number;
  totalRevenue: number;
  topMenu: string;
  recentOrders: Array<{ menu: string; quantity: number; total: number; date: string }>;
  reviews: Review[];
};

export default function AdminDashboardPage() {
  const router = useRouter();

  const [data, setData] = useState<DashboardData | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("adminToken");

    if (!token) {
      router.push("/admin/login");
      return;
    }

    fetch("/api/admin/dashboard", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error("Unauthorized");
        }
        return res.json();
      })
      .then((dashboardData) => {
        setData(dashboardData);
        setReviews(dashboardData.reviews || []);
      })
      .catch((err) => {
        console.error("Failed to load dashboard:", err);
        setData(null);
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

  const totalOrders = data?.totalOrders ?? 0;
  const totalRevenue = data?.totalRevenue ?? 0;
  const topMenu = data?.topMenu ?? "-";
  const recentOrders = data?.recentOrders ?? [];

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
            <h3>จำนวนออเดอร์</h3>
            <h2>{totalOrders}</h2>
          </div>

          <div className="panel stat">
            <h3>ยอดขายรวม</h3>
            <h2>฿{totalRevenue.toLocaleString()}</h2>
          </div>

          <div className="panel stat">
            <h3>เมนูยอดนิยม</h3>
            <h2>{topMenu}</h2>
          </div>

          <div className="panel stat">
            <h3>คะแนนเฉลี่ย</h3>
            <h2>{average}</h2>
          </div>

          <div className="panel stat">
            <h3>จำนวนรีวิว</h3>
            <h2>{reviews.length}</h2>
          </div>

          <div className="panel stat">
            <h3>สถานะ</h3>
            <h2>Ready</h2>
          </div>
        </div>

        <div className="panel">
          <h2>ออเดอร์ล่าสุด</h2>

          {loading ? (
            <p>กำลังโหลดข้อมูล...</p>
          ) : (
            <div className="tableWrap">
              <table>
                <thead>
                  <tr>
                    <th>เมนู</th>
                    <th>จำนวน</th>
                    <th>ยอดรวม</th>
                    <th>วันที่</th>
                  </tr>
                </thead>

                <tbody>
                  {recentOrders.map((order, index) => (
                    <tr key={`${order.date}-${index}`}>
                      <td>{order.menu}</td>
                      <td>{order.quantity}</td>
                      <td>฿{order.total}</td>
                      <td>{order.date}</td>
                    </tr>
                  ))}

                  {!recentOrders.length && (
                    <tr>
                      <td colSpan={4}>ยังไม่มีออเดอร์</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
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
