"use strict";
// browser DOM + Fetch: the Python API is authoritative about validation and state.
const form = document.querySelector("#booking");
const msg = document.querySelector("#message");
const rides = document.querySelector("#rides");
const filter = document.querySelector("#statusFilter");

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (response.status === 204) return null;
  const body = await response.json();
  if (!response.ok) {
    const detail = body.detail;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return body;
}
function say(text) { msg.textContent = text; }
async function load() {
  try {
    const suffix = filter.value ? "?status=" + encodeURIComponent(filter.value) : "";
    const data = await api("/api/rides" + suffix);
    rides.replaceChildren(); // Do NOT use innerHTML with user-provided data.
    if (!data.length) { rides.textContent = "No rides match this view."; return; }
    for (const item of data) {
      const section = document.createElement("article");
      section.className = "ride";
      const title = document.createElement("strong");
      title.textContent = item.pickup + " → " + item.destination;
      const details = document.createElement("p");
      details.textContent = item.passenger + " · " + item.status + " · €" + (item.fare_cents / 100).toFixed(2);
      const actions = document.createElement("div");
      actions.className = "actions";
      function action(label, method, path, payload) {
        const button = document.createElement("button");
        button.type = "button"; button.textContent = label;
        button.addEventListener("click", async () => {
          try {
            await api(path, { method, body: payload ? JSON.stringify(payload) : undefined });
            say(label + " succeeded."); await load();
          } catch (error) { say(error.message); }
        });
        actions.append(button);
      }
      if (item.status === "requested") {
        action("Assign", "PATCH", "/api/rides/" + encodeURIComponent(item.id), {status:"assigned"});
        action("Delete", "DELETE", "/api/rides/" + encodeURIComponent(item.id));
      }
      if (item.status === "assigned") {
        action("Complete", "PATCH", "/api/rides/" + encodeURIComponent(item.id), {status:"completed"});
      }
      if (item.status === "assigned" || item.status === "requested") {
        action("Cancel", "PATCH", "/api/rides/" + encodeURIComponent(item.id), {status:"cancelled"});
      }
      if (item.status === "cancelled") action("Delete", "DELETE", "/api/rides/" + encodeURIComponent(item.id));
      section.append(title, details, actions);
      rides.append(section);
    }
  } catch (error) { say("Load error: " + error.message); }
}
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(form));
  try {
    const payload = {
      passenger: values.passenger, pickup: values.pickup,
      destination: values.destination, distance_km: Number(values.distance_km),
      request_key: crypto.randomUUID(),
    };
    const saved = await api("/api/rides", {method:"POST", body:JSON.stringify(payload)});
    say("Created demonstration ride " + saved.id.slice(0, 8));
    await load();
  } catch (error) { say("Booking error: " + error.message); }
});
document.querySelector("#refresh").addEventListener("click", load);
filter.addEventListener("change", load);
load();
