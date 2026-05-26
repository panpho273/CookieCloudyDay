"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");

    const cleanUsername = username.trim();
    const cleanPassword = password.trim();

    if (!cleanUsername || !cleanPassword) {
      setError("กรุณากรอกชื่อผู้ใช้และรหัสผ่าน");
      return;
    }

    setLoading(true);

    try {
      const adminRes = await fetch("/api/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: cleanUsername,
          password: cleanPassword,
        }),
      });

      const adminData = await adminRes.json();

      if (adminRes.ok && adminData.ok) {
        router.push("/admin/dashboard");
        return;
      }

      // ลูกค้าทั่วไป: ใช้สำหรับ demo เข้ากลับไปหน้าสั่งซื้อ
      localStorage.setItem("cookiecloudyday_member_username", cleanUsername);
      router.push("/#member");
    } catch {
      setError("เข้าสู่ระบบไม่สำเร็จ กรุณาลองใหม่อีกครั้ง");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="loginPage">
      <section className="loginCard">
        <div className="loginBrandIcon">🍪</div>

        <span className="miniBadge">CookieCloudyDay</span>

        <h1>เข้าสู่ระบบ</h1>
        <p>
          เข้าสู่ระบบสมาชิกเพื่อสั่งซื้อ หรือเข้าสู่ระบบหลังบ้านสำหรับแอดมิน
        </p>

        <form onSubmit={handleLogin} className="loginForm">
          <label>
            ชื่อผู้ใช้
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="กรอกชื่อผู้ใช้"
              autoComplete="username"
              autoFocus
            />
          </label>

          <label>
            รหัสผ่าน
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="กรอกรหัสผ่าน"
              autoComplete="current-password"
            />
          </label>

          {error && <div className="loginError">{error}</div>}

          <button type="submit" className="loginPrimaryBtn" disabled={loading}>
            {loading ? "กำลังเข้าสู่ระบบ..." : "เข้าสู่ระบบ"}
          </button>

          <Link href="/" className="loginSecondaryBtn">
            กลับหน้าเว็บ
          </Link>
        </form>

        <small className="loginHint">
          สำหรับแอดมิน ใช้ชื่อผู้ใช้และรหัสผ่านหลังบ้านที่ตั้งไว้ในระบบ
        </small>
      </section>
    </main>
  );
}
