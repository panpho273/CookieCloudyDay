"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

type AgeGroup = {
  group: string;
  count: number;
  percent: number;
};

type AdminStats = {
  reviews: number;
  orders: number;
  members: number;
  averageRating: string;
  totalSales: number;
  topMenu: string;
  bestAgeGroup: string;
  ageGroups: AgeGroup[];
};

export default function AdminDashboardPage() {
  const router = useRouter();

  const [stats, setStats] = useState<AdminStats>({
    reviews: 0,
    orders: 0,
    members: 0,
    averageRating: "0.0",
    totalSales: 0,
    topMenu: "-",
    bestAgeGroup: "-",
    ageGroups: [],
  });

  useEffect(() => {
    async function checkAdminSession() {
      const sessionRes = await fetch("/api/admin/session", {
        cache: "no-store",
      });

      if (!sessionRes.ok) {
        router.push("/login");
        return false;
      }

      return true;
    }

    async function loadDashboard() {
      const allowed = await checkAdminSession();

      if (!allowed) return;
      const res = await fetch(`/api/admin/dashboard?t=${Date.now()}`, {
        cache: "no-store",
      });

      const data = await res.json();

      if (!res.ok || !data.ok) return;

      setStats({
        reviews: data.reviews ?? 0,
        orders: data.orders ?? 0,
        members: data.members ?? 0,
        averageRating: data.averageRating ?? "0.0",
        totalSales: data.totalSales ?? 0,
        topMenu: data.topMenu ?? "-",
        bestAgeGroup: data.bestAgeGroup ?? "-",
        ageGroups: data.ageGroups ?? [],
      });
    }

    loadDashboard();
  }, [router]);

  async function handleLogout() {
    await fetch("/api/admin/logout", { method: "POST" });
    router.push("/login");
  }

  return (
    <main className="adminPage">
      <section className="adminDashboardCard">
        <div className="adminTopBar">
          <div>
            <span className="miniBadge">CookieCloudyDay Admin</span>
            <h1>แดชบอร์ดหลังบ้าน</h1>
            <p>
              ดึงข้อมูลจาก 3 ชีท: ชีต1, reviews และ members เพื่อดูภาพรวมร้าน
            </p>
          </div>

          <div className="adminActions">
            <Link href="/" className="adminGhostBtn">
              กลับหน้าเว็บ
            </Link>

            <button type="button" className="adminLogoutBtn" onClick={handleLogout}>
              ออกจากระบบ
            </button>
          </div>
        </div>

        <div className="adminStatsGrid">
          <div className="adminStatCard">
            <span>⭐</span>
            <p>คะแนนเฉลี่ย</p>
            <strong>{stats.averageRating}</strong>
          </div>

          <div className="adminStatCard">
            <span>💬</span>
            <p>รีวิวจากลูกค้า</p>
            <strong>{stats.reviews}</strong>
          </div>

          <div className="adminStatCard">
            <span>🛒</span>
            <p>ออเดอร์</p>
            <strong>{stats.orders}</strong>
          </div>

          <div className="adminStatCard">
            <span>👥</span>
            <p>สมาชิก</p>
            <strong>{stats.members}</strong>
          </div>
        </div>

        <div className="adminStatsGrid adminStatsGridSecond">
          <div className="adminStatCard">
            <span>💰</span>
            <p>ยอดขายรวม</p>
            <strong>{stats.totalSales.toLocaleString()} บาท</strong>
          </div>

          <div className="adminStatCard">
            <span>🍪</span>
            <p>เมนูขายดี</p>
            <strong>{stats.topMenu}</strong>
          </div>

          <div className="adminStatCard">
            <span>🎯</span>
            <p>ช่วงอายุลูกค้าหลัก</p>
            <strong>{stats.bestAgeGroup}</strong>
          </div>
        </div>

        <div className="adminNotice">
          <h2>วิเคราะห์อายุสมาชิก</h2>

          {stats.ageGroups.length > 0 ? (
            <div className="ageInsightList">
              {stats.ageGroups.map((item) => (
                <div className="ageInsightItem" key={item.group}>
                  <div>
                    <strong>{item.group}</strong>
                    <span>{item.count} คน</span>
                  </div>

                  <div className="ageInsightBar">
                    <span style={{ width: `${item.percent}%` }} />
                  </div>

                  <b>{item.percent}%</b>
                </div>
              ))}
            </div>
          ) : (
            <p>
              ยังไม่มีข้อมูลอายุในชีท members หรือยังไม่พบ column อายุ/วันเกิด
            </p>
          )}
        </div>
      </section>
    </main>
  );
}
