const role = document.body.dataset.role;
const key = document.getElementById("key");
const status = document.getElementById("status");
const result = document.getElementById("result");
let tripId = null;
let lastBooking = null;

async function request(path, method = "GET", data, idempotencyKey) {
  const headers = { Authorization: "Bearer " + key.value };
  if (data) headers["Content-Type"] = "application/json";
  if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;
  const response = await fetch("/v1/" + role + "/" + path, {
    method, headers, body: data ? JSON.stringify(data) : undefined,
  });
  const body = await response.json();
  if (!response.ok) throw Error(typeof body.detail === "string" ? body.detail : "Request validation failed");
  return body;
}

async function refresh() {
  try {
    if (role === "rider") {
      if (!tripId) return;
      const trip = await request("trips/" + tripId);
      status.textContent = trip.status.replaceAll("_", " ");
      result.textContent = JSON.stringify(trip, null, 2);
      return;
    }
    const offers = await request("offers");
    status.textContent = offers.length ? "" : "No active offers.";
    result.replaceChildren(...offers.map((offer) => {
      const section = document.createElement("section");
      const title = document.createElement("strong");
      title.textContent = offer.pickup + " → " + offer.destination;
      section.append(title);
      const next = offer.state === "offered" ? ["Accept", "offers/" + offer.trip_id + "/accept"]
        : offer.status === "assigned" ? ["Pick up", "trips/" + offer.trip_id + "/milestones", { status: "picked_up" }]
        : offer.status === "picked_up" ? ["Complete", "trips/" + offer.trip_id + "/milestones", { status: "completed" }]
        : null;
      if (next) {
        const button = document.createElement("button");
        button.textContent = next[0];
        button.onclick = async () => {
          button.disabled = true;
          try { await request(next[1], "POST", next[2]); await refresh(); }
          catch (error) { status.textContent = error.message; button.disabled = false; }
        };
        section.append(button);
      } else {
        section.append("Waiting for assignment");
      }
      return section;
    }));
  } catch (error) {
    status.textContent = error.message;
  }
}

document.getElementById("booking")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
  const payload = JSON.stringify(data);
  if (lastBooking?.payload !== payload) lastBooking = { payload, key: crypto.randomUUID() };
  try {
    const trip = await request("trips", "POST", data, lastBooking.key);
    tripId = trip.id;
    lastBooking = null;
    await refresh();
  } catch (error) { status.textContent = error.message; }
});

document.getElementById("telemetry")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(event.target);
  try {
    await request("availability", "PUT", { online: data.has("online"),
      distance_km: Number(data.get("distance_km")), speed_kph: Number(data.get("speed_kph")) });
    await refresh();
  } catch (error) { status.textContent = error.message; }
});

refresh();
setInterval(refresh, 1600);
