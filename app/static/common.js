export const $ = (s, el = document) => el.querySelector(s);
export function h(tag, attrs = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (v === true) e.setAttribute(k, "");
    else if (v !== false && v != null) e.setAttribute(k, v);
  }
  for (const k of [].concat(...kids)) if (k != null && k !== false) e.append(k.nodeType ? k : document.createTextNode(k));
  return e;
}
export const wsUrl = (path) => `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}${path}`;
export function toast(msg) {
  const t = $("#toast"); t.textContent = msg; t.style.display = "block";
  clearTimeout(toast.t); toast.t = setTimeout(() => (t.style.display = "none"), 3500);
}
export const fmt = (s) => { s = Math.max(0, Math.ceil(s)); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; };
export const KIND = { owned: "support", pipeline: "research", scouting: "scout" };
export const ROW_TITLE = { owned: "Owned", pipeline: "Pipeline", scouting: "Scouting" };
export function tokens(n, cls, label) { return Array.from({ length: n }, () => h("span", { class: cls }, label)); }
export function connect(path, onMsg, onClose) {
  let ws, closed = false;
  const open = () => {
    ws = new WebSocket(wsUrl(path));
    ws.onmessage = (e) => onMsg(JSON.parse(e.data));
    ws.onclose = (e) => { if (e.code === 4401) { onClose && onClose(); return; } if (!closed) setTimeout(open, 1500); };
  };
  open();
  return { send: (m) => ws && ws.readyState === 1 && ws.send(JSON.stringify(m)), close: () => { closed = true; ws.close(); } };
}

// Where this tab remembers its seat. In development mode each ?dev_player=P1..P4 identity gets its own slot,
// so four tabs of one browser can be four participants. Otherwise one seat per session code per device.
export async function devIdentity() {
  try {
    const cfg = await (await fetch("/api/config")).json();
    const id = new URLSearchParams(location.search).get("dev_player");
    return cfg.development_mode && /^P[1-4]$/.test(id || "") ? id : null;
  } catch { return null; }
}
export const seatKey = (code, dev) => "meridian:" + code + (dev ? ":" + dev : "");
export async function devMode() {
  try { return (await (await fetch("/api/config")).json()).development_mode; } catch { return false; }
}
