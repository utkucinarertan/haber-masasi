/* Gizlilik, destek ve künye sayfaları: sahibin bilgileri tek yerde. Mağazaya göndermeden önce doldurulmalı. */
const OWNER = {
  name: "[Ad Soyad]",
  email: "[destek e-postası]",
  address: "[Açık adres, posta kodu, şehir, ülke]",
};

const LANGS = ["en", "tr", "de"];
const want = new URLSearchParams(location.search).get("lang") || (navigator.language || "en").slice(0, 2);
const lang = LANGS.includes(want) ? want : "en";
document.documentElement.lang = lang;
document.querySelectorAll("article[data-l]").forEach(a => { a.hidden = a.dataset.l !== lang; });
document.querySelectorAll(".langs a").forEach(a => a.setAttribute("aria-current", a.dataset.l === lang ? "page" : "false"));
document.querySelectorAll("[data-owner]").forEach(e => { e.textContent = OWNER.name; });
document.querySelectorAll("a[data-mail]").forEach(a => { a.textContent = OWNER.email; a.href = "mailto:" + OWNER.email; });
document.querySelectorAll("[data-imprint]").forEach(p => {
  p.replaceChildren(document.createTextNode(OWNER.name), document.createElement("br"),
    document.createTextNode(OWNER.address), document.createElement("br"), document.createTextNode(OWNER.email));
});
