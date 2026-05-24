const SHEET_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxs8TXwZQnbRnr5YiUU-TKcD1Rj91TEwcaQjGDIxDWUOlyh8F6x-BBUZl2JdSaXUWyz5g/exec";

const menus = [
  { name: "คุกกี้ช็อกโกแลตชิพ", price: 45, emoji: "🍪", desc: "หอมเนย ช็อกโกแลตชิพแน่น ๆ" },
  { name: "คุกกี้แมคคาเดเมียไวท์ช็อก", price: 65, emoji: "🥜", desc: "พรีเมียม หอมมัน ละมุนที่สุด" },
  { name: "คุกกี้เนยสด", price: 55, emoji: "🧈", desc: "รสคลาสสิก กินง่าย หอมละมุน" },
  { name: "คุกกี้สตรอว์เบอร์รีชีสเค้ก", price: 59, emoji: "🍓", desc: "หวานอมเปรี้ยว น่ารักสดใส" },
  { name: "คุกกี้ช็อกโกแลตลาวา", price: 59, emoji: "🍫", desc: "เข้มข้น หวานกำลังดี" },
  { name: "คุกกี้มัทฉะไวท์ช็อก", price: 59, emoji: "🍵", desc: "มัทฉะหอมกับไวท์ช็อกนุ่ม ๆ" },
];

const allMenus = [
  { name: "คุกกี้ช็อกโกแลตชิพ", price: 45 },
  { name: "คุกกี้เนยสด", price: 55 },
  { name: "คุกกี้ช็อกโกแลตลาวา", price: 59 },
  { name: "คุกกี้ดับเบิลช็อกโกแลต", price: 59 },
  { name: "คุกกี้มัทฉะไวท์ช็อก", price: 59 },
  { name: "คุกกี้โอรีโอ้ครีม", price: 50 },
  { name: "คุกกี้คาราเมลอัลมอนด์", price: 55 },
  { name: "คุกกี้โกโก้เฮเซลนัท", price: 59 },
  { name: "คุกกี้เรดเวลเวต", price: 55 },
  { name: "คุกกี้บราวนี่ฟัดจ์", price: 55 },
  { name: "คุกกี้สตรอว์เบอร์รีชีสเค้ก", price: 59 },
  { name: "คุกกี้วานิลลานมสด", price: 45 },
  { name: "คุกกี้แมคคาเดเมียไวท์ช็อก", price: 65 },
];

const navToggle = document.getElementById("navToggle");
const navLinks = document.getElementById("navLinks");
const year = document.getElementById("year");
const productGrid = document.getElementById("productGrid");
const menuSelect = document.getElementById("menuSelect");
const quantityInput = document.getElementById("quantityInput");
const totalText = document.getElementById("totalText");
const orderForm = document.getElementById("orderForm");

let toastTimer = null;

function showToast(title, message, type = "success") {
  const toast = document.getElementById("toast");
  const toastTitle = document.getElementById("toast-title");
  const toastMessage = document.getElementById("toast-message");
  const toastClose = document.getElementById("toast-close");

  if (!toast || !toastTitle || !toastMessage) {
    console.log(title, message);
    return;
  }

  toastTitle.textContent = title;
  toastMessage.textContent = message;

  toast.classList.remove("success", "error", "show");
  toast.classList.add(type);

  requestAnimationFrame(() => {
    toast.classList.add("show");
  });

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.classList.remove("show");
  }, 4200);

  if (toastClose) {
    toastClose.onclick = () => {
      toast.classList.remove("show");
      clearTimeout(toastTimer);
    };
  }
}

if (navToggle && navLinks) {
  navToggle.addEventListener("click", () => {
    navLinks.classList.toggle("show");
  });

  navLinks.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => navLinks.classList.remove("show"));
  });
}

if (year) {
  year.textContent = new Date().getFullYear();
}

function getPrice(menuName) {
  const item = allMenus.find((m) => m.name === menuName);
  return item ? item.price : 0;
}

function updateTotal() {
  if (!menuSelect || !quantityInput || !totalText) return;

  const price = getPrice(menuSelect.value);
  const quantity = Math.max(1, Number(quantityInput.value || 1));
  totalText.textContent = `${price * quantity} บาท`;
}

async function saveOrder(menuName, quantity) {
  const price = getPrice(menuName);
  const total = price * quantity;

  if (!menuName || !price || quantity <= 0) {
    showToast(
      "ข้อมูลออเดอร์ไม่ถูกต้อง",
      "กรุณาเลือกเมนูและจำนวนใหม่อีกครั้งนะคะ",
      "error"
    );
    return;
  }

  const submitButtons = document.querySelectorAll("button");
  submitButtons.forEach((button) => {
    if (button.textContent.includes("สั่ง")) {
      button.disabled = true;
      button.dataset.oldText = button.textContent;
      button.textContent = "กำลังบันทึก...";
    }
  });

  try {
    await fetch(SHEET_WEB_APP_URL, {
      method: "POST",
      mode: "no-cors",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        menu: menuName,
        quantity: quantity,
        price: price
      })
    });

    showToast(
      "สั่งซื้อสำเร็จ 🍪",
      `${menuName}\nจำนวน ${quantity} ชิ้น\nรวม ${total} บาท`,
      "success"
    );
  } catch (error) {
    console.error(error);
    showToast(
      "ส่งออเดอร์ไม่สำเร็จ",
      "ลองใหม่อีกครั้งนะคะ หรือสั่งผ่าน Demi AI ได้เลย",
      "error"
    );
  } finally {
    submitButtons.forEach((button) => {
      if (button.dataset.oldText) {
        button.textContent = button.dataset.oldText;
        delete button.dataset.oldText;
      }
      button.disabled = false;
    });
  }
}

if (productGrid) {
  productGrid.innerHTML = menus.map((item) => `
    <article class="product-card">
      <div class="product-img">${item.emoji}</div>
      <div class="product-body">
        <h3>${item.name}</h3>
        <p>${item.desc}</p>
        <div class="product-bottom">
          <strong>${item.price} บาท</strong>
          <button type="button" data-menu="${item.name}">สั่งซื้อ</button>
        </div>
      </div>
    </article>
  `).join("");

  productGrid.querySelectorAll("button[data-menu]").forEach((button) => {
    button.addEventListener("click", async () => {
      await saveOrder(button.dataset.menu, 1);
    });
  });
}

if (menuSelect) {
  menuSelect.innerHTML = allMenus.map((item) => `
    <option value="${item.name}">
      ${item.name} — ${item.price} บาท
    </option>
  `).join("");
}

if (menuSelect) menuSelect.addEventListener("change", updateTotal);
if (quantityInput) quantityInput.addEventListener("input", updateTotal);

if (orderForm) {
  orderForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const menuName = menuSelect.value;
    const quantity = Math.max(1, Number(quantityInput.value || 1));

    await saveOrder(menuName, quantity);
  });
}

updateTotal();

/* =========================================================
   HOME UI ENHANCER
   ========================================================= */
document.addEventListener("DOMContentLoaded", () => {
  const header = document.querySelector("header");
  const aboutSection =
    document.querySelector("#about") ||
    document.querySelector(".about-section") ||
    document.querySelector("section.about");

  const menuSection =
    document.querySelector("#menu") ||
    document.querySelector(".menu-section") ||
    document.querySelector(".best-seller-section") ||
    document.querySelector(".product-section");

  const productGrid =
    document.querySelector("#productGrid") ||
    document.querySelector(".product-grid") ||
    document.querySelector(".best-seller-grid") ||
    document.querySelector(".home-product-grid");

  const orderPanel =
    document.querySelector("#orderPanel") ||
    document.querySelector(".order-panel") ||
    document.querySelector(".order-box") ||
    document.querySelector(".menu-order-panel") ||
    document.querySelector(".order-online-card") ||
    document.querySelector(".order-sidebar");

  /* remove order panel from HOME */
  if (orderPanel) {
    orderPanel.remove();
  }

  /* rename section to best sellers */
  if (menuSection) {
    const heading =
      menuSection.querySelector("h2") ||
      menuSection.querySelector(".section-title") ||
      menuSection.querySelector(".section-heading");

    const kicker =
      menuSection.querySelector(".kicker") ||
      menuSection.querySelector(".section-kicker") ||
      menuSection.querySelector("small");

    const desc =
      menuSection.querySelector("p") ||
      menuSection.querySelector(".section-subtitle") ||
      menuSection.querySelector(".section-desc");

    if (kicker) kicker.textContent = "BEST SELLERS";
    if (heading) heading.textContent = "เมนูยอดฮิต";
    if (desc) desc.textContent = "รวมเมนูขายดีที่สุดของร้าน ดูง่าย น่ารัก และไม่รกเหมือนเดิม";
  }

  /* hide extra cards, keep top 4 only */
  if (productGrid) {
    const cards = Array.from(productGrid.querySelectorAll(".product-card"));
    cards.forEach((card, index) => {
      if (index >= 4) card.style.display = "none";
    });

    /* remove/rename order buttons in hot menu */
    productGrid.querySelectorAll("button").forEach((btn) => {
      btn.remove();
    });
  }

  /* insert oval divider before ABOUT section */
  if (aboutSection && !document.querySelector(".oval-divider")) {
    const divider = document.createElement("section");
    divider.className = "oval-divider";
    divider.innerHTML = `
      <div class="oval-divider__blob"></div>
      <div class="oval-divider__glow"></div>
      <div class="oval-divider__float oval-divider__float--1">🍪</div>
      <div class="oval-divider__float oval-divider__float--2">☁️</div>
      <div class="oval-divider__float oval-divider__float--3">✨</div>
    `;
    aboutSection.parentNode.insertBefore(divider, aboutSection);
  }

  const divider = document.querySelector(".oval-divider");
  const blob = divider?.querySelector(".oval-divider__blob");
  const floats = divider ? divider.querySelectorAll(".oval-divider__float") : [];

  function onScrollEffects() {
    const y = window.scrollY || 0;

    if (header) {
      header.classList.toggle("scrolled", y > 10);
    }

    if (divider && blob) {
      const rect = divider.getBoundingClientRect();
      const viewportH = window.innerHeight || 1;
      const visible = rect.top < viewportH && rect.bottom > 0;

      if (visible) {
        divider.classList.add("is-active");

        const progress = Math.max(-1, Math.min(1, (viewportH * 0.5 - rect.top) / viewportH));
        const moveY = progress * 18;
        const scale = 1 + Math.abs(progress) * 0.03;

        blob.style.transform = `translateX(-50%) translateY(${moveY}px) scale(${scale})`;

        floats.forEach((el, i) => {
          const multi = (i + 1) * 6;
          el.style.transform = `translateY(${progress * multi}px) rotate(${progress * multi}deg)`;
        });
      } else {
        divider.classList.remove("is-active");
      }
    }
  }

  window.addEventListener("scroll", onScrollEffects, { passive: true });
  onScrollEffects();

  /* reveal animation */
  const revealTargets = document.querySelectorAll(
    ".product-card, #about, .about-section, section.about"
  );

  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
      }
    });
  }, { threshold: 0.15 });

  revealTargets.forEach((el) => {
    el.classList.add("reveal-up");
    io.observe(el);
  });
});
