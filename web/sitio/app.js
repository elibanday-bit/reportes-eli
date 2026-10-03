// Cifrado compartido por las páginas del sitio. La llave maestra solo vive en sessionStorage
// (se borra al cerrar la pestaña o con "Cerrar sesión").
const enc = new TextEncoder(), dec = new TextDecoder();
const unb64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));

const sesion = {
  get() { try { const k = sessionStorage.getItem("pc_k"); return k ? { k, nombre: sessionStorage.getItem("pc_n") || "" } : null; } catch { return null; } },
  set(k, nombre) { sessionStorage.setItem("pc_k", k); sessionStorage.setItem("pc_n", nombre); },
  clear() { try { sessionStorage.removeItem("pc_k"); sessionStorage.removeItem("pc_n"); } catch {} }
};

async function getVault() {
  const r = await fetch("vault.json", { cache: "no-store" });
  if (!r.ok) throw new Error("No se pudo cargar el sitio");
  return r.json();
}

async function sha256hex(s) {
  const h = await crypto.subtle.digest("SHA-256", enc.encode(s));
  return [...new Uint8Array(h)].map(b => b.toString(16).padStart(2, "0")).join("");
}

async function abrir(key, { iv, ct }) {
  return crypto.subtle.decrypt({ name: "AES-GCM", iv: unb64(iv) }, key, unb64(ct));
}

const llave = raw => crypto.subtle.importKey("raw", unb64(raw), "AES-GCM", false, ["decrypt"]);

// Devuelve {k, nombre} o null si el usuario o la contraseña no son válidos.
async function login(usuario, clave) {
  const vault = await getVault();
  const u = vault.users[await sha256hex(usuario.trim().toLowerCase())];
  if (!u) return null;
  const base = await crypto.subtle.importKey("raw", enc.encode(clave), "PBKDF2", false, ["deriveKey"]);
  const kek = await crypto.subtle.deriveKey({ name: "PBKDF2", hash: "SHA-256", salt: unb64(u.salt), iterations: vault.iter },
    base, { name: "AES-GCM", length: 256 }, false, ["decrypt"]);
  try { return JSON.parse(dec.decode(await abrir(kek, u))); } catch { return null; }
}

// Para páginas protegidas: devuelve la llave o manda al inicio de sesión.
async function requerirSesion() {
  const s = sesion.get();
  if (!s) { location.replace("index.html"); throw new Error("sin sesión"); }
  return { key: await llave(s.k), nombre: s.nombre };
}

async function getManifest(key) {
  const vault = await getVault();
  return JSON.parse(dec.decode(await abrir(key, vault.manifest)));
}

function salir() { sesion.clear(); location.replace("index.html"); }

const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fecha = iso => { const d = new Date(iso + "T12:00:00"); return isNaN(d) ? iso : d.toLocaleDateString("es-PE", { day: "numeric", month: "short", year: "numeric" }); };

// Logo Laureate (versión provisional en SVG; el texto toma el color del contenedor para modo claro y oscuro).
const LOGO_SVG = `<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
<defs><mask id="lm"><rect width="640" height="220" fill="#fff"/><path d="M92 82h15v58h34v14H92z" fill="#000"/></mask></defs>
<path d="M30 210C34 120 100 36 205 10C200 104 136 186 30 210Z" fill="#F26522" mask="url(#lm)"/>
<rect x="216" y="70" width="3" height="96" fill="currentColor"/>
<text x="268" y="118" font-family="Archivo,Helvetica,Arial,sans-serif" font-size="78" font-weight="800" textLength="345" lengthAdjust="spacingAndGlyphs" fill="currentColor">LAUREATE</text>
<text x="270" y="176" font-family="Archivo,Helvetica,Arial,sans-serif" font-size="47" font-weight="400" textLength="322" lengthAdjust="spacingAndGlyphs" fill="currentColor">EDUCATION INC</text>
<text x="604" y="150" font-family="Arial,sans-serif" font-size="16" fill="currentColor">®</text></svg>`;
document.querySelectorAll(".logo").forEach(el => { el.innerHTML = LOGO_SVG; el.setAttribute("role", "img"); el.setAttribute("aria-label", "Laureate Education Inc"); });
