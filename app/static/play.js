import { $, h, connect, toast, fmt, KIND, ROW_TITLE, tokens, devIdentity, seatKey } from "/static/common.js";
const code = (new URLSearchParams(location.search).get("code") || "").toUpperCase();
const dev = await devIdentity();
const KEY = seatKey(code, dev);
const saved = JSON.parse(localStorage.getItem(KEY) || "null");
if (!saved) location.href = "/" + (dev ? "?dev_player=" + dev : "");
let V = null, pageShown = false, receivedAt = 0;
const conn = connect(`/ws/${code}?token=${encodeURIComponent(saved.token)}`, (m) => {
  if (m.type === "error") return toast(m.message);
  V = m; receivedAt = performance.now(); render();
}, () => { localStorage.removeItem(KEY); $("#msg").replaceChildren(h("p", { class: "err" }, "Your seat is no longer active. Return to the join page."), h("a", { href: "/" }, "Join page")); });

const phaseLabel = { lobby: "Waiting for facilitator", reading: "Quiet reading", open: "Board open", frozen: "Board frozen" };
function remaining() { const s = V.state; return s.remaining == null ? null : s.remaining - (performance.now() - receivedAt) / 1000; }

function render() {
  const { state: s, content: c, you } = V;
  const open = s.phase === "open";
  $("#bar").replaceChildren(
    h("strong", {}, "Meridian Ventures"), h("span", { class: "pill" }, `Round ${s.round}`), h("span", { class: "pill" }, you.role), dev ? h("span", { class: "pill" }, "DEV " + dev) : null,
    h("span", { class: "pill" }, phaseLabel[s.phase]), h("span", { class: "grow" }),
    h("span", {}, "Bank: ", h("strong", {}, `${s.bank}`), " chips"), h("span", { class: "timer", id: "timer" }, ""));
  tick();
  const msg = [];
  if (s.phase === "frozen") msg.push(h("div", { class: "frozen" }, "The board is frozen. Whatever is on it is the committee's decision."));
  $("#msg").replaceChildren(...msg);

  const board = [];
  for (const row of ["owned", "pipeline", "scouting"]) {
    const cards = c.companies.filter((x) => x.row === row).map((x) => card(x, s, c, open));
    board.push(h("section", { class: "row" }, h("h2", {}, ROW_TITLE[row]), h("div", { class: "cards" }, cards)));
  }
  $("#board").replaceChildren(...board);

  const pl = s.pool_left, kinds = ["support", "research", "scout"];
  const warn = s.bank < c.owed ? h("p", { class: "warn" }, `Bank is below the ${c.owed} chips Meridian owes next round (missed payment).`) : null;
  const side = [
    h("div", { class: "panel" }, h("h2", {}, "Bank & staff"), h("div", { class: "tokens" }, tokens(s.bank, "chip", "$1M")),
      h("p", {}, `${s.bank} of ${c.starting_chips} chips in the bank. Meridian owes ${c.owed} next round.`), warn,
      h("p", {}, kinds.map((k) => h("span", { style: "margin-right:10px" }, h("span", { class: "ctr " + k }, pl[k]), " " + k))), 
      h("p", { class: "mut" }, "Counters left in the pool.")),
    h("div", { class: "panel" }, h("h2", {}, "Finish early"),
      h("p", { class: "mut" }, "Only if all four agree. Any board change resets the votes."),
      h("button", { disabled: !open, onclick: () => conn.send({ type: "early_finish", value: !you.voted_early }) }, you.voted_early ? "Withdraw agreement" : "I agree to finish"),
      h("p", {}, `${s.early_finish_votes} of 4 agree`)),
    privatePanel(),
    h("div", { class: "panel" }, h("h2", {}, "Legend"), h("p", {}, h("em", {}, "Equal members, no chair.")),
      h("p", {}, c.mandate), h("ul", {}, c.rules.map((r) => h("li", {}, r))),
      h("table", {}, h("tbody", {}, c.profit_bands.map((b) => h("tr", {}, h("td", {}, b.band), h("td", {}, b.range)))))),
  ];
  $("#side").replaceChildren(...side);
}

function privatePanel() {
  if (!V.private_page) return h("div", { class: "panel private" }, h("h2", {}, "Your private page"), h("p", { class: "mut" }, "Available when the round starts."));
  if (!pageShown) return h("div", { class: "panel private" }, h("h2", {}, "Your private page"),
    h("p", { class: "mut" }, "Only you can see this. Share what it says in your own words."),
    h("button", { class: "primary", onclick: () => { pageShown = true; conn.send({ type: "page_opened" }); render(); } }, "Open private page"));
  return h("div", { class: "panel private" }, h("h2", {}, `Private · ${V.you.role}`),
    h("p", { class: "mut" }, "Your say is equal to everyone else's. Share any of this in your own words."), V.private_page.map((p) => h("p", {}, p)));
}

function card(x, s, c, open) {
  const chips = s.board.chips[x.id] || 0, ctr = s.board.counters[x.id] || 0, kind = KIND[x.row];
  const meta = x.row === "owned" ? `Needs ${x.cost} chips · estimated profit $${x.est_profit}M`
    : x.row === "pipeline" ? `Asking $${x.ask_low}–${x.ask_high}M · invest now: ${x.cost} chips · profit unknown` : "Price and profit unknown · no chips";
  const ctl = [];
  if (x.row !== "scouting") ctl.push(h("button", { disabled: !open, onclick: () => conn.send({ type: "set_funded", company: x.id, value: !chips }) }, chips ? `Remove ${chips} chips` : `Put ${x.cost} chips`));
  ctl.push(h("span", { class: "mut" }, kind), h("button", { disabled: !open || ctr <= 0, onclick: () => conn.send({ type: "set_counters", company: x.id, value: ctr - 1 }) }, "−"),
    h("button", { disabled: !open || ctr >= c.max_per_company, onclick: () => conn.send({ type: "set_counters", company: x.id, value: ctr + 1 }) }, "+"));
  return h("div", { class: "card" }, h("h3", {}, x.name), h("div", { class: "line" }, x.line), h("div", { class: "meta" }, meta), h("div", { class: "sum" }, x.summary),
    h("div", { class: "tokens" }, tokens(chips, "chip", "$1M"), tokens(ctr, "ctr " + kind, kind[0].toUpperCase())), h("div", { class: "ctl" }, ctl));
}

function tick() { if (!V) return; const t = $("#timer"), r = remaining(); if (t) t.textContent = r == null ? (V.state.phase === "frozen" ? "0:00" : "") : fmt(r); }
setInterval(tick, 250);
