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
