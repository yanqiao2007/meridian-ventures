import { $, h, connect, toast, fmt, KIND, ROW_TITLE, tokens } from "/static/common.js";
let key = sessionStorage.getItem("meridian:fkey"), code = sessionStorage.getItem("meridian:fcode"), S = null, content = null, recv = 0, conn = null;
const api = async (path, method = "POST") => {
  const r = await fetch(path, { method, headers: { "X-Facilitator-Key": key } });
  if (!r.ok) { const d = await r.json().catch(() => ({})); toast(d.detail || "Request failed"); throw new Error(d.detail); }
  return r;
};
async function login() {
  key = $("#pw").value || key;
  sessionStorage.setItem("meridian:fkey", key);
  const ok = await fetch(code ? `/api/sessions/${code}` : "/healthz", { headers: { "X-Facilitator-Key": key } });
  if (code && !ok.ok) { code = null; sessionStorage.removeItem("meridian:fcode"); }
  if (!code) { const t = await fetch("/api/sessions", { method: "POST", headers: { "X-Facilitator-Key": key } }); if (!t.ok) { $("#lerr").textContent = "Wrong password."; return; } code = (await t.json()).code; sessionStorage.setItem("meridian:fcode", code); }
  $("#login").style.display = "none"; $("#app").style.display = "block";
  conn = connect(`/ws/${code}?key=${encodeURIComponent(key)}`, (m) => { if (m.type === "state") { S = m.state; content = m.content; recv = performance.now(); render(); } });
}
$("#in").onclick = login; $("#pw").addEventListener("keydown", (e) => { if (e.key === "Enter") login(); });
if (key) login();

async function download(name) {
  const r = await api(`/api/sessions/${code}/export/${name}`, "GET");
  const a = h("a", { href: URL.createObjectURL(await r.blob()), download: `${code}_${name}` }); a.click();
}
const act = (a) => () => api(`/api/sessions/${code}/${a}`).catch(() => {});
function render() {
  const joinUrl = `${location.origin}/`;
  const seats = Object.entries(S.seats);
  $("#top").replaceChildren(
    h("h2", {}, "Session"), h("p", {}, "Code: ", h("strong", { style: "font-size:1.6rem;letter-spacing:.15em" }, S.code), `  ·  players join at `, h("strong", {}, joinUrl)),
    h("p", {}, `Round ${S.round} · status: `, h("strong", {}, S.status === "running" ? S.phase : S.status), S.frozen_reason ? ` (${S.frozen_reason})` : ""),
    h("div", { class: "ctl" },
      h("button", { class: "primary", disabled: S.status !== "lobby" || seats.some(([, v]) => !v.filled), onclick: act("start") }, "Start round"),
      h("button", { class: "danger", disabled: S.status !== "running", onclick: () => confirm("Freeze the board now? This ends the round.") && act("freeze")() }, "Freeze board"),
      h("button", { disabled: S.status !== "frozen", onclick: act("advance") }, "Advance to next round"),
      h("button", { onclick: () => download("events.csv") }, "Export events CSV"),
      h("button", { onclick: () => download("final_boards.csv") }, "Export final boards CSV")));
  $("#side").replaceChildren(
    h("div", { class: "panel" }, h("h2", {}, "Seats"), h("table", {}, h("tbody", {}, seats.map(([role, v]) => h("tr", {},
      h("td", {}, role), h("td", {}, v.filled ? v.pid : h("span", { class: "mut" }, "vacant")),
      h("td", {}, v.filled ? h("button", { disabled: S.status === "running", onclick: () => confirm(`Remove ${role} (${v.pid})? A new participant can then join into this role.`) && act("replace/" + encodeURIComponent(role))() }, "Replace") : "")))))),
    h("div", { class: "panel" }, h("h2", {}, "Status"), h("p", {}, `Bank: ${S.bank} chips`), h("p", {}, `Early-finish agreement: ${S.early_finish_votes} of 4`)));
  $("#board").replaceChildren(...["owned", "pipeline", "scouting"].map((row) => h("section", { class: "row" }, h("h2", {}, ROW_TITLE[row]),
    h("div", { class: "cards" }, content.companies.filter((x) => x.row === row).map((x) => h("div", { class: "card" }, h("h3", {}, x.name),
      h("div", { class: "tokens" }, tokens(S.board.chips[x.id] || 0, "chip", "$1M"), tokens(S.board.counters[x.id] || 0, "ctr " + KIND[row], KIND[row][0].toUpperCase()))))))));
  tick();
}
function tick() { const t = $("#timer"); if (!S || !t) return; const r = S.remaining == null ? null : S.remaining - (performance.now() - recv) / 1000; t.textContent = r == null ? "" : fmt(r); }
setInterval(tick, 250);
