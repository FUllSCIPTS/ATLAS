"use strict";
// ATLAS Web Technology lab — browser side.
// The server (FastAPI) is the authority on validation and ride state; this file only
// (1) turns form input into JSON, (2) calls the API with fetch, (3) redraws the DOM safely.

const form = document.querySelector("#booking");
const message = document.querySelector("#message");
const ridesBox = document.querySelector("#rides");
const filter = document.querySelector("#statusFilter");
const countText = document.querySelector("#count");
const moreButton = document.querySelector("#more");
const statsBody = document.querySelector("#stats");
const farePreview = document.querySelector("#fare-preview");

const PAGE = 20;
let shown = 0;
let onlineDrivers = [];

// ---------------------------------------------------------------- HTTP helper
async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (response.status === 204) return { data: null, response };
  const data = await response.json();
  if (!response.ok) {                       // fetch does NOT reject on 4xx/5xx: check yourself
    const detail = data.detail;
    const text = Array.isArray(detail)       // Pydantic 422: a list of {loc, msg}
      ? detail.map((d) => `${d.loc.slice(1).join(".") || "body"}: ${d.msg}`).join("; ")
      : String(detail);
    throw new Error(`${response.status} ${text}`);
  }
  return { data, response };
}

function say(text) { message.textContent = text; }   // textContent never interprets HTML
const euros = (cents) => "€" + (cents / 100).toFixed(2);

// ---------------------------------------------------------------- rendering (safe DOM building)
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;   // NOT innerHTML: user text stays text (no XSS)
  if (className) node.className = className;
  return node;
}

function rideCard(ride) {
  const card = element("article", undefined, "ride");
  card.dataset.status = ride.status;
  card.append(element("strong", `${ride.pickup} → ${ride.destination}`));
  const who = ride.driver_name ? ` · driver ${ride.driver_name}` : "";
  card.append(element("p", `${ride.passenger} · ${ride.status}${who} · ${euros(ride.fare_cents)} · ${ride.distance_km} km`));
  const actions = element("div", undefined, "actions");
  const path = "/api/rides/" + encodeURIComponent(ride.id);

  function button(label, method, body, style) {
    const b = element("button", label, style);
    b.type = "button";
    b.addEventListener("click", async () => {
      try {
        await api(path, { method, body: body ? JSON.stringify(body()) : undefined });
        say(`${label} succeeded.`);
        await refresh();
      } catch (error) { say(`${label} failed: ${error.message}`); }
    });
    actions.append(b);
  }

  if (ride.status === "requested") {
    const select = element("select");
    select.setAttribute("aria-label", "Driver for this ride");
    for (const d of onlineDrivers) {
      const option = element("option", `${d.name} (${d.zone}, ★${d.rating})`);
      option.value = d.id;
      select.append(option);
    }
    actions.append(select);
    button("Assign", "PATCH", () => ({ status: "assigned", driver_id: Number(select.value) }));
  }
  if (ride.status === "assigned") button("Complete", "PATCH", () => ({ status: "completed" }));
  if (ride.status === "requested" || ride.status === "assigned") {
    button("Cancel", "PATCH", () => ({ status: "cancelled" }), "secondary");
  }
  if (ride.status === "requested" || ride.status === "cancelled") button("Delete", "DELETE", null, "danger");
  card.append(actions);
  return card;
}

// ---------------------------------------------------------------- loading data
async function loadRides(append = false) {
  if (!append) { shown = 0; ridesBox.replaceChildren(); }
  const params = new URLSearchParams({ limit: PAGE, offset: shown });
  if (filter.value) params.set("status", filter.value);
  const { data, response } = await api("/api/rides?" + params);
  const total = Number(response.headers.get("X-Total-Count"));
  for (const ride of data) ridesBox.append(rideCard(ride));
  shown += data.length;
  countText.textContent = total ? `Showing ${shown} of ${total}` : "No rides match this view.";
  moreButton.hidden = shown >= total;
}

async function loadStats() {
  const { data } = await api("/api/stats");
  statsBody.replaceChildren(...data.by_status.map((s) => {
    const row = element("tr");
    row.append(element("td", s.status), element("td", String(s.rides)), element("td", euros(s.fare_cents)));
    return row;
  }));
}

async function refresh() {
  try {
    onlineDrivers = (await api("/api/drivers?online=true")).data;
    await Promise.all([loadRides(), loadStats()]);   // two requests in parallel
  } catch (error) { say("Load error: " + error.message); }
}

// ---------------------------------------------------------------- events
form.addEventListener("submit", async (event) => {
  event.preventDefault();                    // stop the browser's own form navigation
  const values = Object.fromEntries(new FormData(form));   // keys come from the name="" attributes
  const payload = {
    passenger: values.passenger,
    pickup: values.pickup,
    destination: values.destination,
    distance_km: Number(values.distance_km),
    request_key: crypto.randomUUID(),        // idempotency key: a retry cannot create a duplicate
  };
  try {
    const { data } = await api("/api/rides", { method: "POST", body: JSON.stringify(payload) });
    say(`Created ride ${data.id.slice(0, 8)} — fare ${euros(data.fare_cents)}`);
    await refresh();
  } catch (error) { say("Booking error: " + error.message); }
});

form.distance_km.addEventListener("input", () => {
  const km = Number(form.distance_km.value);
  farePreview.textContent = km > 0 ? `Estimated fare ${euros(Math.round(250 + 150 * km))} (the server decides)` : "";
});

document.querySelector("#refresh").addEventListener("click", refresh);
filter.addEventListener("change", () => loadRides().catch((e) => say(e.message)));
moreButton.addEventListener("click", () => loadRides(true).catch((e) => say(e.message)));

form.distance_km.dispatchEvent(new Event("input"));
refresh();
