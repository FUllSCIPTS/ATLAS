const iconPaths = {
  map: '<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3zM9 3v15m6-12v15"/>',
  layers: '<path d="m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5"/>',
  cloud: '<path d="M7 17a4 4 0 1 1 .7-7.94 5.6 5.6 0 0 1 10.7 1.46A3.3 3.3 0 1 1 19 17Z"/>',
  folder: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1Z"/>',
  focus: '<circle cx="12" cy="12" r="3"/><path d="M3 9V4h5m8 0h5v5m0 6v5h-5m-8 0H3v-5"/>',
  user: '<circle cx="12" cy="8" r="3"/><path d="M5 20v-2a5 5 0 0 1 5-5h4a5 5 0 0 1 5 5v2"/>',
  car: '<path d="m5 10 2-5h10l2 5M3 14a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v4H3v-4Zm2 4v2m14-2v2M7 14h1m8 0h1"/>',
  gateway: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18m-13 4 2 2-2 2m5 0h3"/>',
  route: '<circle cx="6" cy="17" r="2"/><circle cx="18" cy="7" r="2"/><path d="M8 17h8a2.5 2.5 0 0 0 0-5H8a2.5 2.5 0 0 1 0-5h8"/>',
  target: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><path d="M12 2v3m10 7h-3m-7 10v-3M2 12h3"/>',
  database: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
  kafka: '<circle cx="6" cy="6" r="2"/><circle cx="6" cy="18" r="2"/><circle cx="18" cy="12" r="2"/><path d="M6 8v8m2-8 8 3m-8 5 8-3"/>',
  activity: '<path d="M2 12h5l3-7 4 14 3-7h5"/>',
  trend: '<path d="M4 4v16h16M7 15l4-4 3 2 6-7m-5 0h5v5"/>',
  brain: '<path d="M12 6a3 3 0 0 0-6 0 3.5 3.5 0 0 0-2 5.8A4 4 0 0 0 7 18a3 3 0 0 0 5 1V6Zm0 0a3 3 0 0 1 6 0 3.5 3.5 0 0 1 2 5.8A4 4 0 0 1 17 18a3 3 0 0 1-5 1M7 10c1.7 0 3 1.3 3 3m7-3c-1.7 0-3 1.3-3 3"/>',
  archive: '<rect x="4" y="4" width="16" height="4" rx="1"/><path d="M5 8v12h14V8m-10 4h6"/>',
  arrow: '<path d="M4 12h15m-6-6 6 6-6 6"/>',
  diagonal: '<path d="M6 18 18 6M7 6h11v11"/>',
  chevron: '<path d="m9 6 6 6-6 6"/>',
  previous: '<path d="m15 6-6 6 6 6"/>',
  play: '<path d="m8 5 12 7-12 7z"/>',
  pause: '<path d="M9 5v14m6-14v14"/>',
  reset: '<path d="M4 10a8 8 0 1 1 1.7 7M4 5v5h5"/>',
  search: '<circle cx="10.5" cy="10.5" r="5.5"/><path d="m15 15 4 4"/>',
  bag: '<path d="M5 8h14l-1.2 12H6.2Z"/><path d="M9 8V6.5a3 3 0 0 1 6 0V8"/>',
  utensils: '<path d="M7 3v7a2 2 0 0 0 2 2m-2-9v18M5 3v5m4-5v5"/><path d="M17 21V3c-2.2 1.4-3 4-3 7v4h3"/>',
  file: '<path d="M6 3h8l4 4v14H6Zm8 0v5h4M9 12h6m-6 4h6"/>',
};

const $ = (id) => document.getElementById(id);
const icon = (name, size = 18) => `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${iconPaths[name]}</svg>`;
const linkById = Object.fromEntries(links.map((link) => [link.id, link]));
const kindLabels = { sync: "Request / state", event: "Kafka event", learn: "Model / policy data" };
const folderById = Object.fromEntries(folders.flatMap((group) => group.children.map((entry) => [entry.id, { ...entry, path: group.root ? "" : group.name + "/" + (entry.name.endsWith("/") ? entry.name : "") }])));
const state = { view: "architecture", selected: "trip", trace: null, step: 0, focus: false, category: "all", query: "", folder: "trip", timer: null };

document.querySelectorAll("[data-icon]").forEach((element) => { element.innerHTML = icon(element.dataset.icon, 17); });

function announce(message) {
  $("announcement").textContent = message;
}

function componentColor(id) {
  return groups[components[id].group].color;
}

function componentMark(id, size = 19) {
  return `<span class="component-icon" style="--accent:${componentColor(id)}">${icon(components[id].icon, size)}</span>`;
}

function viewHeading(kicker, title, detail, badge = "") {
  return `<div class="panel-head"><div><p class="section-kicker">${kicker}</p><h2>${title}</h2><p class="panel-subtitle">${detail}</p></div>${badge}</div>`;
}

function updateControls() {
  $("tracebar").hidden = state.view !== "architecture";
  $("scenarios").innerHTML = `<span class="trace-label">TRACE A FLOW</span>` + Object.entries(scenarios).map(([id, trace]) => `<button type="button" class="scenario" aria-pressed="${state.trace === id}" data-scenario="${id}" data-keep="scenario-${id}">${icon(trace.icon, 16)}${trace.title}</button>`).join("");
  $("dependency-toggle").setAttribute("aria-pressed", String(state.focus));
  for (const button of document.querySelectorAll("[data-view]")) {
    const active = button.dataset.view === state.view;
    button.setAttribute("aria-selected", String(active));
    button.tabIndex = active ? 0 : -1;
  }
  $("workspace").setAttribute("aria-labelledby", "tab-" + state.view);
}

function architectureView() {
  const trace = scenarios[state.trace];
  const currentLink = trace ? linkById[trace.steps[state.step][0]] : null;
  const neighborLinks = new Set(links.filter(({ from, to }) => from === state.selected || to === state.selected));
  const traceLinks = new Set(trace?.steps.map(([id]) => linkById[id]));
  const visibleLinks = trace ? traceLinks : neighborLinks;
  const highlightedNodes = new Set([state.selected, ...[...visibleLinks].flatMap(({ from, to }) => [from, to])]);
  const markers = Object.keys(kindLabels).flatMap((kind) => ["base", "active"].map((tone) =>
    `<marker id="arrow-${kind}-${tone}" markerWidth="6" markerHeight="6" refX="5.3" refY="3" orient="auto" markerUnits="userSpaceOnUse"><path class="marker ${kind} ${tone}" d="M0 0 6 3 0 6 1.5 3Z"/></marker>`)).join("");
  const orderedLinks = [...links].sort((a, b) => Number(visibleLinks.has(a)) - Number(visibleLinks.has(b)) || Number(a === currentLink) - Number(b === currentLink));
  const wiring = orderedLinks.map((link) => {
    const mode = link === currentLink ? "current" : visibleLinks.has(link) ? "related" : state.focus || trace ? "muted" : "idle";
    const marker = mode === "related" || mode === "current" ? "active" : "base";
    return `<path class="wire ${link.kind} ${mode}" data-link="${link.id}" d="${link.path}" marker-end="url(#arrow-${link.kind}-${marker})"><title>${link.label}</title></path>`;
  }).join("");
  const lanes = Object.values(groups).map((group, index) => `<div class="lane" style="left:${(group.x - 9) / 9}%;--accent:${group.color}"><div class="lane-label"><span>0${index + 1}</span> ${group.label}</div></div>`).join("");
  const nodes = Object.entries(components).map(([id, component]) => {
    const muted = (state.focus || trace) && !highlightedNodes.has(id);
    const endpoint = currentLink && (id === currentLink.from || id === currentLink.to);
    return `<button type="button" class="map-node ${muted ? "dimmed" : ""} ${endpoint ? "endpoint" : ""}" data-component="${id}" data-keep="map-${id}" aria-pressed="${id === state.selected}" style="left:${groups[component.group].x / 9}%;top:${component.y / 5}%;--accent:${componentColor(id)}">${componentMark(id)}<span class="map-node-text"><strong>${component.title}</strong><small>${component.tech}</small></span></button>`;
  }).join("");
  const playback = trace ? `<section class="playback" aria-label="Flow playback">
      <div class="step-heading"><span class="step-number">${String(state.step + 1).padStart(2, "0")} / ${String(trace.steps.length).padStart(2, "0")}</span><strong>${components[currentLink.from].title} <span aria-hidden="true">→</span> ${components[currentLink.to].title}</strong></div>
      <p>${trace.steps[state.step][1]}</p>
      <div class="playback-actions">
        <button class="square" type="button" aria-label="Previous step" title="Previous step" data-action="previous" data-keep="previous" ${state.step === 0 ? "disabled" : ""}>${icon("previous", 17)}</button>
        <button class="square play" type="button" aria-label="${state.timer ? "Pause flow" : "Play flow"}" title="${state.timer ? "Pause flow" : "Play flow"}" data-action="play" data-keep="play">${icon(state.timer ? "pause" : "play", 16)}</button>
        <button class="square" type="button" aria-label="Next step" title="Next step" data-action="next" data-keep="next" ${state.step === trace.steps.length - 1 ? "disabled" : ""}>${icon("chevron", 17)}</button>
        <button class="square" type="button" aria-label="Reset flow" title="Reset flow" data-action="restart" data-keep="restart">${icon("reset", 17)}</button>
      </div>
    </section>` : "";
  return viewHeading("SYSTEM MAP", "Architecture", "Select a node to inspect its dependencies, or trace a flow.", `<span class="panel-badge">${Object.keys(components).length} components</span>`)
    + playback + `<div class="map-scroll" tabindex="0" aria-label="Scrollable architecture diagram"><div class="map-canvas">${lanes}<svg class="wires" viewBox="0 0 900 500" aria-hidden="true"><defs>${markers}</defs>${wiring}</svg>${nodes}</div></div>
    <div class="legend" aria-label="Connection legend">${Object.entries(kindLabels).map(([kind, label]) => `<span><i class="legend-line ${kind}"></i>${label}</span>`).join("")}<span class="pan-hint">Scroll to see all layers ${icon("arrow", 13)}</span></div><button class="mobile-inspect" type="button" data-action="inspect">Inspect ${components[state.selected].title} <span aria-hidden="true">↓</span></button>`;
}

function cardsMarkup() {
  const query = state.query.trim().toLowerCase();
  const matches = Object.entries(components).filter(([, component]) => (state.category === "all" || component.group === state.category)
    && [component.title, component.tech, component.summary].some((item) => item.toLowerCase().includes(query)));
  return matches.length ? matches.map(([id, component]) => `<button class="catalog-card" type="button" data-component="${id}" data-keep="card-${id}" aria-pressed="${state.selected === id}" style="--accent:${componentColor(id)}">
    <span class="catalog-top">${componentMark(id)}<span>${groups[component.group].label}</span></span><strong>${component.title}</strong><span class="catalog-tech">${component.tech}</span><span class="card-arrow">${icon("diagonal", 15)}</span>
  </button>`).join("") : '<p class="empty">No components match this filter.</p>';
}

function componentsView() {
  return viewHeading("SERVICE CATALOG", "Components", "Browse the stack by layer or search by name and technology.")
    + `<div class="catalog-controls"><label class="search">${icon("search", 17)}<input id="component-search" data-keep="search" type="search" placeholder="Search components…" aria-label="Search components"></label>
    <label class="group-filter"><span class="sr-only">Filter by layer</span><select id="group-filter" data-keep="filter"><option value="all">All layers</option>${Object.entries(groups).map(([id, group]) => `<option value="${id}">${group.label}</option>`).join("")}</select></label></div>
    <div class="catalog-grid" id="catalog-grid">${cardsMarkup()}</div>`;
}

function deploymentView() {
  return viewHeading("RUNTIME TOPOLOGY", "Deployment", "Suggested runtime boundaries and the components that run in each zone.", '<span class="panel-badge">4 runtime zones</span>')
    + `<div class="zones">${zones.map((zone, index) => `<section class="zone" style="--accent:${groups[zone.group].color}"><div class="zone-top"><span class="component-icon">${icon(zone.icon)}</span><div><p>ZONE 0${index + 1}</p><h3>${zone.title}</h3></div></div><span class="zone-sub">${zone.sub}</span><div class="zone-items">${zone.nodes.map((id) => `<button type="button" data-component="${id}" data-keep="zone-${id}" aria-pressed="${state.selected === id}">${icon(components[id].icon, 15)}${components[id].title}</button>`).join("")}</div><p class="zone-boundary">${zone.boundary}</p></section>`).join("")}</div>
    <div class="deployment-note">${icon("gateway", 18)}<p><strong>Local development</strong><span>Run the linked starter with Docker Compose for PostgreSQL and Kafka, or use its SQLite quickstart for local development.</span></p></div>`;
}

function foldersView() {
  const selected = folderById[state.folder];
  return viewHeading("SOURCE LAYOUT", "Folder structure", "Browse the exact folders and files in the runnable starter. Open a file to read its source on GitHub.")
    + `<div class="repo-layout"><div class="repo-tree" aria-label="Repository folders"><div class="repo-root">${icon("folder", 17)} starter/</div>${folders.map((group) => `<details ${group.children.some((entry) => entry.id === state.folder) || openFolders.has(group.name) ? "open" : ""} data-folder-group="${group.name}"><summary>${icon("chevron", 12)}${icon("folder", 15)}<strong>${group.name}/</strong></summary><div class="branch">${group.children.map((entry) => `<button type="button" data-folder="${entry.id}" data-keep="folder-${entry.id}" aria-pressed="${state.folder === entry.id}">${icon("folder", 13)}${entry.name}</button>`).join("")}</div></details>`).join("")}</div>
    <section class="folder-details"><p class="section-kicker">DIRECTORY</p><h3>starter/${selected.path}</h3><p>${selected.detail}</p><p class="section-kicker file-label">SOURCE FILES</p><ul>${selected.example.map((file) => `<li>${icon("file", 16)}<a href="https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/${selected.path}${file}"><code>${file}</code></a></li>`).join("")}</ul></section></div>`;
}

function inspectorMarkup() {
  const id = state.selected;
  const component = components[id];
  const group = groups[component.group];
  const entry = folderById[component.file];
  const neighbors = [
    { heading: "Receives from", rows: links.filter(({ to }) => to === id), target: "from" },
    { heading: "Sends to", rows: links.filter(({ from }) => from === id), target: "to" },
  ];
  return `<div class="inspector-head"><span>${icon("focus", 16)} COMPONENT INSPECTOR</span><span class="status-dot" aria-hidden="true"></span></div>
    <div class="inspector-body" style="--accent:${group.color}"><div class="inspector-identity">${componentMark(id, 23)}<div><p>${group.label}</p><h2 id="component-title" tabindex="-1">${component.title}</h2></div></div>
    <p class="inspector-summary">${component.summary}</p>
    <div class="io"><div><span>INPUT</span><p>${component.inputs}</p></div><div><span>OUTPUT</span><p>${component.outputs}</p></div></div>
    <div class="connections">${neighbors.filter(({ rows }) => rows.length).map(({ heading, rows, target }) => `<div class="connection-group"><h3>${heading}</h3>${rows.map((link) => `<button type="button" class="connection" data-component="${link[target]}" data-keep="edge-${link.id}"><i class="edge-dot ${link.kind}"></i><span><strong>${components[link[target]].title}</strong><small>${link.label}</small></span>${icon("chevron", 13)}</button>`).join("")}</div>`).join("")}</div>
    <p class="inspector-note"><strong>Implementation note</strong><span>${component.notes}</span></p>
    <button class="source-link" type="button" data-action="source" data-keep="source">${icon("folder", 16)}<code>${entry.path}${entry.example[0]}</code>${icon("diagonal", 14)}</button></div>`;
}

const views = { architecture: architectureView, components: componentsView, deployment: deploymentView, folders: foldersView };
const openFolders = new Set(["apps", "services"]);

function render() {
  const focusKey = document.activeElement?.dataset.keep;
  const previousMap = document.querySelector(".map-scroll");
  const previousInspector = $("inspector").querySelector(".inspector-body");
  updateControls();
  $("view-content").innerHTML = views[state.view]();
  $("inspector").innerHTML = inspectorMarkup();
  const map = document.querySelector(".map-scroll");
  if (map && previousMap) map.scrollLeft = previousMap.scrollLeft;
  const inspectorBody = $("inspector").querySelector(".inspector-body");
  if (previousInspector?.querySelector("#component-title")?.textContent === components[state.selected].title) {
    inspectorBody.scrollTop = previousInspector.scrollTop;
  }
  if (state.view === "components") {
    $("component-search").value = state.query;
    $("group-filter").value = state.category;
  }
  if (focusKey) {
    const replacement = document.querySelector(`[data-keep="${focusKey}"]:not(:disabled)`);
    if (replacement) replacement.focus({ preventScroll: true });
    else if (focusKey === "next" || focusKey === "previous") document.querySelector('[data-keep="play"]')?.focus({ preventScroll: true });
    else if (focusKey.startsWith("edge-")) $("component-title").focus({ preventScroll: true });
  }
}

function stopPlayback() {
  clearInterval(state.timer);
  state.timer = null;
}

function switchView(view) {
  if (state.view !== view) stopPlayback();
  state.view = view;
  render();
}

function applyStep(step) {
  state.step = step;
  const trace = scenarios[state.trace];
  const link = linkById[trace.steps[step][0]];
  state.selected = link.to;
  announce(`${trace.title}, step ${step + 1} of ${trace.steps.length}. ${trace.steps[step][1]}`);
  render();
  const map = document.querySelector(".map-scroll");
  const source = map.querySelector('[data-component="' + link.from + '"]');
  const destination = map.querySelector('[data-component="' + link.to + '"]');
  const left = Math.min(source.offsetLeft, destination.offsetLeft) - 10;
  const right = Math.max(source.offsetLeft, destination.offsetLeft) + destination.offsetWidth + 10;
  if (right - left > map.clientWidth) {
    map.scrollLeft = destination.offsetLeft - 10;
  } else if (left < map.scrollLeft || right > map.scrollLeft + map.clientWidth) {
    map.scrollLeft = left;
  }
}

function setScenario(id) {
  stopPlayback();
  state.focus = false;
  if (state.trace === id) {
    state.trace = null;
    announce("Flow cleared");
    render();
    return;
  }
  state.trace = id;
  applyStep(0);
}

function playTrace() {
  if (state.timer) {
    stopPlayback();
    render();
    return;
  }
  const lastStep = scenarios[state.trace].steps.length - 1;
  state.timer = setInterval(() => {
    const next = state.step + 1;
    if (next === lastStep) stopPlayback();
    applyStep(next);
  }, 2600);
  if (state.step === lastStep) applyStep(0);
  else render();
}

document.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  const { view, scenario, component, folder, action } = button.dataset;
  if (view) switchView(view);
  else if (scenario) setScenario(scenario);
  else if (button.id === "dependency-toggle") {
    const next = !state.focus;
    stopPlayback();
    state.trace = null;
    state.focus = next;
    render();
  } else if (component) {
    stopPlayback();
    state.selected = component;
    announce(`Inspecting ${components[component].title}`);
    render();
  } else if (folder) {
    state.folder = folder;
    const owner = folderById[folder].component || folder;
    if (components[owner]) state.selected = owner;
    render();
  } else if (action === "inspect") {
    $("component-title").focus();
    $("inspector").scrollIntoView({ block: "start" });
  } else if (action === "source") {
    state.folder = components[state.selected].file;
    switchView("folders");
    document.querySelector('[data-keep="folder-' + state.folder + '"]').focus();
  } else if (action === "play") playTrace();
  else if (action && state.trace) {
    stopPlayback();
    if (action === "restart") applyStep(0);
    else applyStep(state.step + (action === "next" ? 1 : -1));
  }
});

document.querySelector('[role="tablist"]').addEventListener("keydown", (event) => {
  const tabs = [...document.querySelectorAll("[data-view]")];
  const index = tabs.indexOf(event.target);
  if (index < 0) return;
  const destinations = { ArrowRight: (index + 1) % tabs.length, ArrowLeft: (index + tabs.length - 1) % tabs.length, Home: 0, End: tabs.length - 1 };
  if (!(event.key in destinations)) return;
  event.preventDefault();
  const target = tabs[destinations[event.key]];
  switchView(target.dataset.view);
  target.focus();
});

$("view-content").addEventListener("input", (event) => {
  if (event.target.id !== "component-search" && event.target.id !== "group-filter") return;
  state.query = $("component-search").value;
  state.category = $("group-filter").value;
  $("catalog-grid").innerHTML = cardsMarkup();
});

$("view-content").addEventListener("toggle", (event) => {
  const group = event.target.dataset.folderGroup;
  if (!group || !event.target.isConnected) return;
  if (event.target.open) openFolders.add(group);
  else openFolders.delete(group);
}, true);

render();
