// ATLAS Architecture Explorer — Data structures & algorithms view.
// Loaded after security.js (secEsc, secCode, secTable, secLink, secSection, umlChip, umlSection, umlTopicsSection,
// umlInspector) and ml.js (mlChart, mlLegend, mlRng), and before explorer.js. Every structure below is a real
// pointer-based implementation that mirrors dsa_lab/experiments.py on main; the drawings are produced by walking the
// actual next/prev pointers, so what you see is the structure, not a picture of it.

const dsaIcons = {
  nodes: '<rect x="2" y="9" width="6" height="6" rx="1"/><rect x="16" y="9" width="6" height="6" rx="1"/><path d="M8 12h8m-2-2 2 2-2 2"/>',
  ring: '<circle cx="12" cy="12" r="7"/><path d="M12 5V2m7 10h3m-10 7v3M2 12h3"/><path d="m16 6 2-1-1 2"/>',
  stack: '<rect x="5" y="4" width="14" height="4" rx="1"/><rect x="5" y="10" width="14" height="4" rx="1"/><rect x="5" y="16" width="14" height="4" rx="1"/>',
  hashgrid: '<path d="M4 6h16M4 12h16M4 18h16"/><circle cx="8" cy="6" r="1.4"/><circle cx="13" cy="12" r="1.4"/><circle cx="17" cy="18" r="1.4"/>',
  graph: '<circle cx="5" cy="6" r="2"/><circle cx="19" cy="7" r="2"/><circle cx="12" cy="18" r="2"/><circle cx="12" cy="10" r="1.6"/><path d="M7 6.5 10.5 9.4m3-.4 3.8-1.6M12 11.6V16m-5.3-8.6 4.1 9"/>',
  sortbars: '<path d="M5 20V15m5 5V11m5 9V7m5 13V3"/>',
  puzzle: '<path d="M4 4h6v3a2 2 0 1 0 4 0V4h6v6h-3a2 2 0 1 0 0 4h3v6h-6v-3a2 2 0 1 0-4 0v3H4z"/>',
  gauge: '<path d="M4 18a8 8 0 1 1 16 0"/><path d="m12 18 4-6"/>',
  book: '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2Zm0 0v16m4-14h7"/>',
};

const DSA_MAIN = "https://github.com/FUllSCIPTS/ATLAS/blob/main/";
const DSA_GUIDE = DSA_MAIN + "docs/DATA_STRUCTURES_ALGORITHMS.md";
const DSA_LAB = DSA_MAIN + "dsa_lab/experiments.py";
const DSA_README = DSA_MAIN + "dsa_lab/README.md";
const DSA_COLAB = "https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/dsa_lab/DSA_Colab_Labs.ipynb";
const DSA_APP = DSA_MAIN + "android-app/atlas_go/";

// Lesson titles exactly as in the guide; the anchor is GitHub's heading slug.
const DSA_LESSONS = [
  "Problems, algorithms, data structures and ADTs", "Counting operations and measuring honestly",
  "Asymptotic notation, cases, amortised cost and recurrences", "Arrays, dynamic arrays, multi-dimensional indexing and strings",
  "Singly linked lists", "Doubly linked lists", "Circular singly linked lists",
  "Circular doubly linked lists, sentinels, LRU caches and cycle detection", "Stacks",
  "Queues, deques and ring buffers (circular arrays)", "Hash tables: chaining, open addressing, load factor and resizing",
  "Trees and the four traversals", "Binary search trees: search, insert and the three deletion cases",
  "AVL trees and the four rotations", "Binary heaps, priority queues and heap sort", "Tries (prefix trees)",
  "Graphs: representations, BFS and DFS", "Shortest paths, topological order, union-find and spanning trees", "Searching",
  "Sorting, stability and the n log n lower bound", "Recursion and divide-and-conquer",
  "Greedy algorithms, dynamic programming and backtracking", "Proving correctness and testing invariants",
  "Laboratory protocol and the 30 experiments",
];
const dsaSlug = (n) => `lesson-${n}--` + DSA_LESSONS[n - 1].toLowerCase().replace(/[^\w\- ]/g, "").replace(/ /g, "-");
const dsaLesson = (n, label = `Lesson ${n}`) => `<a class="sec-inline-link" href="${DSA_GUIDE}#${dsaSlug(n)}">${label}</a>`;
const dsaLessons = (...ns) => ns.map((n) => dsaLesson(n)).join(" · ");

const dsaStatus = {
  impl: { label: "In ATLAS Go", tone: "impl", text: "The idea runs in today's app (android-app/atlas_go)" },
  related: { label: "Related", tone: "demo", text: "The app does something similar without this exact structure" },
  teach: { label: "Teaching", tone: "teach", text: "Lives only in dsa_lab/experiments.py and this explorer" },
};

const dsaTopics = [
  { id: "overview", title: "DSA map", icon: "book", status: null, lessons: [1, 24] },
  { id: "complexity", title: "Complexity", icon: "gauge", status: "impl", lessons: [2, 3, 4] },
  { id: "lists", title: "Linked lists", icon: "nodes", status: "teach", lessons: [5, 6, 7, 8] },
  { id: "queues", title: "Stacks, queues & LRU", icon: "ring", status: "impl", lessons: [8, 9, 10] },
  { id: "hashing", title: "Hash tables", icon: "hashgrid", status: "impl", lessons: [11] },
  { id: "trees", title: "Trees & heaps", icon: "tree", status: "teach", lessons: [12, 13, 14, 15, 16] },
  { id: "graphs", title: "Graphs", icon: "graph", status: "teach", lessons: [17, 18] },
  { id: "sorting", title: "Sorting & searching", icon: "sortbars", status: "impl", lessons: [19, 20] },
  { id: "design", title: "Algorithm design", icon: "puzzle", status: "teach", lessons: [21, 22, 23] },
  { id: "gaps", title: "Experiments & exercises", icon: "bug", status: null, lessons: [24] },
];
const dsaTopicById = Object.fromEntries(dsaTopics.map((t) => [t.id, t]));

function dsaChip(status) {
  if (!status) return "";
  const s = dsaStatus[status];
  return `<span class="sec-chip ${s.tone}" title="${s.text}">${s.label}</span>`;
}

function dsaButton(action, label, { primary = false, iconName = "", disabled = false } = {}) {
  return `<button type="button" class="sec-btn${primary ? " primary" : ""}" data-dsa-action="${action}" data-keep="dsa-${action}"${disabled ? " disabled" : ""}>${iconName ? icon(iconName, 15) : ""}${label}</button>`;
}

function dsaSelect(name, label, options, value) {
  return `<label class="sec-field compact"><span>${label}</span><select data-dsa-select="${name}" data-keep="dsa-sel-${name}">${options.map(([v, l]) => `<option value="${secEsc(v)}"${String(v) === String(value) ? " selected" : ""}>${secEsc(l)}</option>`).join("")}</select></label>`;
}

function dsaRange(name, label, min, max, step, value) {
  return `<label class="sec-field ml-range"><span>${label} <b id="dsa-out-${name}">${value}</b></span><input type="range" data-dsa-range="${name}" data-keep="dsa-rg-${name}" min="${min}" max="${max}" step="${step}" value="${value}"></label>`;
}

function dsaPills(items) {
  return `<div class="sec-status-row">${items.map(([text, tone = ""]) => `<span class="sec-pill ${tone}">${text}</span>`).join("")}</div>`;
}

function dsaOps(lines) { // pointer writes performed by the last operation
  return lines.length ? `<pre class="sec-code dsa-ops"><code>${lines.map((l) => secEsc(l)).join("\n")}</code></pre>` : "";
}

function dsaLog(entries) {
  if (!entries.length) return "";
  return `<ol class="dsa-log">${entries.slice(-6).reverse().map((e) => `<li><code>${secEsc(e.op)}</code><span>${e.text}</span>${e.cost ? `<b>${e.cost}</b>` : ""}</li>`).join("")}</ol>`;
}

// Shared SVG pieces.
const DSA_DEFS = `<defs><marker id="dsa-ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 10 5 0 10z" fill="#90bfe8"/></marker><marker id="dsa-ah2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 10 5 0 10z" fill="#ffc983"/></marker><marker id="dsa-ah3" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 10 5 0 10z" fill="#c2f77a"/></marker></defs>`;
const dsaSvg = (w, h, label, body, cls = "") => `<svg class="dsa-svg ${cls}" viewBox="0 0 ${w} ${h}" role="img" aria-label="${secEsc(label)}">${DSA_DEFS}${body}</svg>`;
const dsaText = (x, y, t, cls = "", anchor = "middle") => `<text class="${cls}" x="${x}" y="${y}" text-anchor="${anchor}">${secEsc(String(t))}</text>`;

const dsa = {
  topic: "overview",
  cx: { n: 1024 },
  list: null, listKind: "csll", listLast: null, listLog: [], listNext: 1,
  jos: null, josN: 7, josK: 3,
  ring: null, ringGrow: false, lru: null,
  hash: null, hashMode: "chain", hashM: 7, hashResize: true,
  tree: null, treeInput: "sorted", heap: null,
  graph: null, graphAlgo: "dijkstra", graphSrc: 15, graphDst: 12,
  sort: null, sortN: 128, sortOrder: "random", trace: null, traceAlgo: "insertion", search: null, searchTarget: 6,
  design: { fib: 20, cap: 10, queens: 6 },
};

// ================================================================== overview
const dsaMap = [
  ["complexity", "gauge", "Complexity & counting", "impl", "Count the operations that matter; linear scans, minimum selection and 2-D lookups in the app", "store.online_drivers · geo.nearest_place"],
  ["lists", "nodes", "Linked lists — all four kinds", "teach", "Singly, doubly, circular singly (tail only) and circular doubly with a sentinel; Josephus on a ring", "dsa_lab/experiments.py"],
  ["queues", "ring", "Stacks, queues & LRU", "impl", "Ring buffer on a circular array; LRU cache = hash map + circular doubly list — the map's tile cache", "livemap.TileLoader"],
  ["hashing", "hashgrid", "Hash tables", "impl", "Chaining vs linear probing on the app's dish ids; load factor, resizing, tombstones", "domain.DISHES · Cart.items"],
  ["trees", "tree", "Trees & heaps", "teach", "BST vs AVL on the same keys; a min-heap of the app's drivers by pickup time", "intelligence.DRIVER_POOLS"],
  ["graphs", "graph", "Graphs", "teach", "BFS, DFS, Dijkstra and Prim on a graph of the app's sixteen Cork zones", "geo.ZONE_COORDS · haversine_km"],
  ["sorting", "sortbars", "Sorting & searching", "impl", "Six sorts counted on the same input; stability on the app's candidates; binary search", "intelligence.rank (sorted)"],
  ["design", "puzzle", "Algorithm design", "teach", "Recursion and memoisation, a DP knapsack for a courier's bag, greedy counterexamples, backtracking", "domain.MENU"],
];

const DSA_ATLAS = [
  ["ADT operations", "impl", "<code>LocalStore.book</code>, <code>checkout</code>, <code>commit</code>", "store.py"],
  ["Linear scans and filtering", "impl", "<code>LocalStore.online_drivers</code>, <code>my_history</code>; <code>Catalog.menu</code>", "store.py · domain.py"],
  ["2-D table lookup", "impl", "<code>domain.DISTANCES[pickup][destination]</code> inside <code>distance()</code>", "domain.py"],
  ["Dictionaries (hashing)", "impl", "<code>Cart.items</code>, <code>Catalog.dishes</code>, <code>DISHES</code> — Python <code>dict</code> uses open addressing", "domain.py · store.py"],
  ["Sorting and ranking", "impl", "<code>intelligence.rank</code> sorts candidates with <code>sorted</code>; <code>choose</code> takes the best", "intelligence.py"],
  ["Minimum selection", "impl", "<code>geo.nearest_place</code> takes the minimum Haversine distance", "geo.py"],
  ["LRU cache", "impl", "<code>TileLoader</code>: an <code>OrderedDict</code> of map tiles, <code>move_to_end</code> on a hit, <code>popitem(last=False)</code> past 160 entries", "livemap.py"],
  ["Grid indexing", "impl", "<code>geo.world_px</code>, <code>tile_range</code>, <code>LiveMap.visible_tiles</code>", "geo.py · livemap.py"],
  ["LIFO work queue", "impl", "<code>TileLoader.requests = queue.LifoQueue()</code>: the newest tile request is fetched first", "livemap.py"],
  ["State machines", "related", "<code>LocalStore.advance_ride</code>, <code>advance_order</code> move a ride or order through states", "store.py"],
  ["Correctness checks", "impl", "<code>LocalStore.validate</code>, <code>snapshot</code>, <code>commit</code>; <code>intelligence.self_test</code>", "store.py · intelligence.py"],
  ["Linked lists, ring buffer, BST/AVL, heap, trie, graph algorithms, union-find, DP", "teach", "<code>dsa_lab/experiments.py</code> and the labs on this tab", "dsa_lab/"],
];

function dsaOverview() {
  return `<div class="sec-intro"><p>Every program is a choice of <strong>data structures</strong> and the <strong>algorithms</strong> that walk them. This tab is the interactive half of the 24-lesson course in <a class="sec-inline-link" href="${DSA_GUIDE}">docs/DATA_STRUCTURES_ALGORITHMS.md</a>: each card opens a lab that runs a real implementation in your browser, draws it by following its own pointers, and counts the operations it performed. Where ATLAS Go uses the idea, the lab says exactly where; where it does not, it says so.</p>
    <div class="sec-legend">${Object.keys(dsaStatus).map((k) => `<span>${dsaChip(k)}<small>${dsaStatus[k].text}</small></span>`).join("")}</div></div>
    <div class="sec-grid">${dsaMap.map(([topic, ic, title, status, text, where]) => `<button type="button" class="sec-card" data-dsa-topic="${topic}" data-keep="dsa-card-${topic}"><span class="sec-card-top">${icon(ic, 18)}${dsaChip(status)}</span><strong>${title}</strong><span>${text}</span><code>${where}</code></button>`).join("")}</div>
    ${secSection("ATLAS GO", "Where the app uses these ideas (strict status)", secTable(["Idea", "Status", "Exact code", "File"], DSA_ATLAS.map(([idea, st, code, file]) => [idea, dsaChip(st), code, `<code>${file}</code>`])))}
    ${secSection("COURSE", "The 24 lessons and where to practise each one", secTable(["#", "Lesson", "Lab on this tab"], DSA_LESSONS.map((title, i) => {
      const topic = dsaTopics.find((t) => t.id !== "overview" && t.lessons.includes(i + 1));
      return [String(i + 1), dsaLesson(i + 1, title), topic ? `<button type="button" class="dsa-link" data-dsa-topic="${topic.id}" data-keep="dsa-l-${i}">${icon(topic.icon, 13)}${topic.title}</button>` : "—"];
    })))}
    <p class="sec-note">${icon("file", 14)}<span class="dsa-t">Python versions of every structure: <a class="sec-inline-link" href="${DSA_LAB}">dsa_lab/experiments.py</a> · 30 experiments: <a class="sec-inline-link" href="${DSA_README}">lab manual</a> · <a class="sec-inline-link" href="${DSA_COLAB}">open the notebook in Colab</a></span></p>`;
}

// ================================================================== complexity
function dsaCountSearch(n) {
  const a = Array.from({ length: n }, (_, i) => 2 * i); // sorted evens; search for an odd number = worst case
  let lin = 0;
  for (const v of a) { lin += 1; if (v === 2 * n + 1) break; }
  let bin = 0, lo = 0, hi = n - 1;
  const x = 2 * n + 1;
  while (lo <= hi) { const mid = (lo + hi) >> 1; bin += 1; if (a[mid] === x) break; if (a[mid] < x) lo = mid + 1; else hi = mid - 1; }
  return { lin, bin };
}

function dsaDuration(sec) {
  if (!isFinite(sec) || sec > 4.4e17) return "longer than the age of the universe";
  const units = [[3.156e7, "years"], [86400, "days"], [3600, "hours"], [60, "minutes"], [1, "s"], [1e-3, "ms"], [1e-6, "µs"], [1e-9, "ns"]];
  const [u, name] = units.find(([d]) => sec >= d) || units[units.length - 1];
  const v = sec / u; return (v >= 100 ? Math.round(v).toLocaleString() : v.toPrecision(3)) + " " + name;
}

function dsaComplexity() {
  const sizes = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096];
  const rows = sizes.map((n) => {
    const g = mlRng(n);
    const data = Array.from({ length: n }, () => g.int(n * 4));
    const ins = dsaSortCount("insertion", data), mer = dsaSortCount("merge", data);
    const s = dsaCountSearch(n);
    return { n, lin: s.lin, bin: s.bin, ins: ins.cmp, mer: mer.cmp };
  });
  const n = dsa.cx.n, log2 = Math.log2(n);
  const growth = [["1", 1], ["log₂ n", log2], ["n", n], ["n log₂ n", n * log2], ["n²", n * n], ["2ⁿ", n <= 64 ? 2 ** n : Infinity]];
  const fmt = (v) => (!isFinite(v) ? "astronomical" : v >= 1e6 ? v.toExponential(2).replace("e+", " × 10^") : Math.round(v).toLocaleString());
  return `<div class="sec-intro"><p>We describe an algorithm by <strong>how the count of its basic operations grows</strong> with the input size <em>n</em>, not by seconds: seconds depend on the machine, counts do not (${dsaLessons(2, 3)}). Below, real searches and sorts run on seeded random data and report their comparison counts.</p></div>
    ${secSection("LIVE", "Count comparisons as n doubles", `${mlChart([
      { points: rows.map((r) => [r.n, r.bin]), cls: "s3" },
      { points: rows.map((r) => [r.n, r.lin]), cls: "s0" },
      { points: rows.map((r) => [r.n, r.mer]), cls: "s2" },
      { points: rows.map((r) => [r.n, r.ins]), cls: "s1" },
    ], { logX: true, logY: true, xLabel: "input size n (log scale)", yLabel: "comparisons (log scale)", height: 200 })}
      ${mlLegend([["s3", "binary search ~ log₂ n"], ["s0", "linear search ~ n"], ["s2", "merge sort ~ n log₂ n"], ["s1", "insertion sort ~ n²/4"]])}
      ${secTable(["n", "Binary search", "Linear search", "Merge sort", "Insertion sort"], rows.filter((r, i) => i % 3 === 0 || r.n === 4096).map((r) => [r.n.toLocaleString(), r.bin, r.lin.toLocaleString(), r.mer.toLocaleString(), r.ins.toLocaleString()]), "ml-table")}
      <p class="sec-note">${icon("trend", 14)}<span class="dsa-t">On log–log axes a power law is a straight line whose slope is the exponent: binary search is almost flat, linear search has slope 1, insertion sort slope 2. Doubling n adds one comparison to binary search and roughly quadruples insertion sort.</span></p>`)}
    ${secSection("FEEL IT", "How big is each growth rate at your n?", `<div class="sec-row">${dsaRange("cxn", "n", 2, 4096, 2, n)}</div>
      ${secTable(["Growth", "Operations at this n", "At 10⁹ simple operations per second"], growth.map(([name, v]) => [name, fmt(v), dsaDuration(v / 1e9)]))}`)}
    ${secSection("ATLAS GO", "What the app actually does, and its cost", secTable(["Code", "Operation", "Cost", "Why it is fine"], [
      ["<code>LocalStore.online_drivers</code>", "filter every account", "Θ(accounts)", "one device holds a handful of accounts"],
      ["<code>geo.nearest_place</code>", "minimum over the saved places", "Θ(places) = Θ(4)", "constant in practice; a k-d tree pays off only for thousands of points"],
      ["<code>domain.DISTANCES[p][d]</code>", "2-D tuple lookup", "Θ(1)", "row-major indexing, no search at all"],
      ["<code>intelligence.rank</code>", "softmax + <code>sorted</code>", "Θ(k log k), k = 4–6 drivers", "sorting is overkill for the top one — <code>choose</code> could use <code>max</code> (Θ(k))"],
      ["<code>LocalStore.my_history</code>", "filter the ride history", "Θ(history)", "grows forever: an index by user would make it Θ(results)"],
    ]))}`;
}

// ================================================================== linked lists (ports of experiments.py)
class DsaNode { constructor(v) { this.v = v; this.next = null; this.prev = null; } }

// SinglyLinkedList: head + tail
class DsaSingly {
  constructor() { this.head = this.tail = null; this.size = 0; }
  pushFront(v) { const n = new DsaNode(v); n.next = this.head; this.head = n; const ops = ["node.next = head", "head = node"]; if (!this.tail) { this.tail = n; ops.push("tail = node        # was empty"); } this.size += 1; return { node: n, ops, hops: 0, cost: "O(1)" }; }
  pushBack(v) { const n = new DsaNode(v); let ops; if (!this.tail) { this.head = this.tail = n; ops = ["head = tail = node  # was empty"]; } else { this.tail.next = n; this.tail = n; ops = ["tail.next = node", "tail = node"]; } this.size += 1; return { node: n, ops, hops: 0, cost: "O(1)" }; }
  popFront() { const n = this.head; this.head = n.next; const ops = ["head = head.next"]; if (!this.head) { this.tail = null; ops.push("tail = None        # now empty"); } this.size -= 1; return { value: n.v, ops, hops: 0, cost: "O(1)" }; }
  popBack() {
    if (this.size === 1) { const v = this.head.v; this.head = this.tail = null; this.size = 0; return { value: v, ops: ["head = tail = None"], hops: 0, cost: "O(1)" }; }
    let p = this.head, hops = 0; while (p.next !== this.tail) { p = p.next; hops += 1; }
    const v = this.tail.v; p.next = null; this.tail = p; this.size -= 1;
    return { value: v, ops: [`walk ${hops} step(s) from head to the node before tail`, "pred.next = None", "tail = pred"], hops, cost: "O(n)", node: p };
  }
  nodes() { const out = []; for (let p = this.head; p; p = p.next) out.push(p); return out; }
  validate() { let c = 0, last = null; for (let p = this.head; p; p = p.next) { c += 1; last = p; if (c > this.size) return false; } return c === this.size && last === this.tail && (!this.tail || this.tail.next === null); }
}

// DoublyLinkedList
class DsaDoubly {
  constructor() { this.head = this.tail = null; this.size = 0; }
  pushFront(v) { const n = new DsaNode(v); let ops; if (!this.head) { this.head = this.tail = n; ops = ["head = tail = node"]; } else { n.next = this.head; this.head.prev = n; this.head = n; ops = ["node.next = head", "head.prev = node", "head = node"]; } this.size += 1; return { node: n, ops, hops: 0, cost: "O(1)" }; }
  pushBack(v) { const n = new DsaNode(v); let ops; if (!this.tail) { this.head = this.tail = n; ops = ["head = tail = node"]; } else { n.prev = this.tail; this.tail.next = n; this.tail = n; ops = ["node.prev = tail", "tail.next = node", "tail = node"]; } this.size += 1; return { node: n, ops, hops: 0, cost: "O(1)" }; }
  popFront() { const n = this.head; this.head = n.next; let ops = ["head = head.next"]; if (this.head) { this.head.prev = null; ops.push("head.prev = None"); } else { this.tail = null; ops.push("tail = None"); } this.size -= 1; return { value: n.v, ops, hops: 0, cost: "O(1)" }; }
  popBack() { const n = this.tail; this.tail = n.prev; let ops = ["tail = tail.prev     # no walk: prev is stored"]; if (this.tail) { this.tail.next = null; ops.push("tail.next = None"); } else { this.head = null; ops.push("head = None"); } this.size -= 1; return { value: n.v, ops, hops: 0, cost: "O(1)" }; }
  nodes() { const out = []; for (let p = this.head; p; p = p.next) out.push(p); return out; }
  validate() { let c = 0, prev = null; for (let p = this.head; p; p = p.next) { if (p.prev !== prev) return false; prev = p; c += 1; if (c > this.size) return false; } return c === this.size && prev === this.tail; }
}

// CircularSinglyLinkedList: only tail is stored; head = tail.next
class DsaCircularSingly {
  constructor() { this.tail = null; this.size = 0; }
  get head() { return this.tail ? this.tail.next : null; }
  pushFront(v) { const n = new DsaNode(v); let ops; if (!this.tail) { n.next = n; this.tail = n; ops = ["node.next = node     # a one-node ring points to itself", "tail = node"]; } else { n.next = this.tail.next; this.tail.next = n; ops = ["node.next = tail.next", "tail.next = node"]; } this.size += 1; return { node: n, ops, hops: 0, cost: "O(1)" }; }
  pushBack(v) { const r = this.pushFront(v); this.tail = this.tail.next; r.ops.push("tail = tail.next     # the new front becomes the new tail"); return r; }
  popFront() { const first = this.tail.next; let ops; if (first === this.tail) { this.tail = null; ops = ["tail = None          # the ring was one node"]; } else { this.tail.next = first.next; ops = ["first = tail.next", "tail.next = first.next"]; } this.size -= 1; return { value: first.v, ops, hops: 0, cost: "O(1)" }; }
  popBack() {
    const old = this.tail;
    if (old.next === old) { this.tail = null; this.size = 0; return { value: old.v, ops: ["tail = None"], hops: 0, cost: "O(1)" }; }
    let p = old.next, hops = 0; while (p.next !== old) { p = p.next; hops += 1; }
    p.next = old.next; this.tail = p; this.size -= 1;
    return { value: old.v, ops: [`walk ${hops} step(s) round the ring to the node before tail`, "pred.next = tail.next", "tail = pred"], hops, cost: "O(n)", node: p };
  }
  rotate(k) { let hops = 0; for (let i = 0; i < k % this.size; i++) { this.tail = this.tail.next; hops += 1; } return { ops: [`tail = tail.next   # × ${hops}`], hops, cost: "O(k)" }; }
  nodes() { const out = []; if (!this.tail) return out; let p = this.tail.next; for (let i = 0; i < this.size; i++) { out.push(p); p = p.next; } return out; }
  validate() { if (!this.tail) return this.size === 0; let p = this.tail.next; for (let i = 0; i < this.size - 1; i++) { if (p === this.tail) return false; p = p.next; } return p === this.tail; }
}

// CircularDoublyLinkedList with a sentinel
class DsaCircularDoubly {
  constructor() { this.s = new DsaNode("S"); this.s.next = this.s.prev = this.s; this.size = 0; }
  insertAfter(node, v, where) { const n = new DsaNode(v); n.prev = node; n.next = node.next; node.next.prev = n; node.next = n; this.size += 1; return { node: n, ops: [`node.prev, node.next = ${where}, ${where}.next`, `${where}.next.prev = node`, `${where}.next = node`], hops: 0, cost: "O(1)" }; }
  unlink(node) { node.prev.next = node.next; node.next.prev = node.prev; this.size -= 1; return { value: node.v, ops: ["node.prev.next = node.next", "node.next.prev = node.prev"], hops: 0, cost: "O(1)" }; }
  pushFront(v) { return this.insertAfter(this.s, v, "sentinel"); }
  pushBack(v) { return this.insertAfter(this.s.prev, v, "sentinel.prev"); }
  popFront() { return this.unlink(this.s.next); }
  popBack() { return this.unlink(this.s.prev); }
  rotate(k) { // advance the start by k: move the sentinel, shorter direction
    const n = this.size, kk = ((-k % n) + n) % n; if (!kk) return { ops: [], hops: 0, cost: "O(1)" };
    const s = this.s, first = s.next; s.prev.next = first; first.prev = s.prev; let anchor = s.prev, hops;
    if (kk <= n - kk) { for (let i = 0; i < kk; i++) anchor = anchor.prev; hops = kk; } else { for (let i = 0; i < n - kk; i++) anchor = anchor.next; hops = n - kk; }
    s.prev = anchor; s.next = anchor.next; anchor.next.prev = s; anchor.next = s;
    return { ops: ["unlink the sentinel (close the ring without it)", `walk ${hops} step(s) the shorter way`, "re-insert the sentinel there"], hops, cost: "O(min(k, n−k))" };
  }
  nodes() { const out = []; for (let p = this.s.next; p !== this.s; p = p.next) out.push(p); return out; }
  validate() { let c = 0, p = this.s; for (;;) { if (p.next.prev !== p) return false; p = p.next; if (p === this.s) break; c += 1; if (c > this.size) return false; } return c === this.size; }
}

const DSA_KINDS = {
  sll: { label: "Singly (head + tail)", make: () => new DsaSingly(), rotate: false, lesson: 5 },
  dll: { label: "Doubly (head + tail)", make: () => new DsaDoubly(), rotate: false, lesson: 6 },
  csll: { label: "Circular singly (tail only)", make: () => new DsaCircularSingly(), rotate: true, lesson: 7 },
  cdll: { label: "Circular doubly + sentinel", make: () => new DsaCircularDoubly(), rotate: true, lesson: 8 },
};

function dsaListNew(kind = dsa.listKind) {
  dsa.listKind = kind; dsa.list = DSA_KINDS[kind].make(); dsa.listLog = []; dsa.listLast = null; dsa.listNext = 1;
  for (let i = 0; i < 4; i++) dsa.list.pushBack(10 * dsa.listNext++);
}

// Draw by walking the real pointers. Boxes: value | next (and prev for doubly kinds).
function dsaListSvg(L, kind, mark) {
  const nodes = L.nodes(), sentinel = kind === "cdll", doubly = kind === "dll" || kind === "cdll", circular = kind === "csll" || kind === "cdll";
  const W = 74, H = 34, G = 42, X0 = 26, Y = 58;
  const cells = sentinel ? [L.s, ...nodes] : nodes;
  const xs = cells.map((_, i) => X0 + i * (W + G));
  const width = Math.max(640, X0 * 2 + cells.length * (W + G) - G + (kind === "sll" || kind === "dll" ? 50 : 0));
  const height = circular ? 158 : 118;
  const at = new Map(cells.map((c, i) => [c, xs[i]]));
  let body = "";
  const arrow = (x1, y1, x2, y2, cls = "", m = "dsa-ah") => `<line class="dsa-edge ${cls}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" marker-end="url(#${m})"/>`;
  cells.forEach((c, i) => {
    const x = xs[i], isS = sentinel && i === 0, hot = mark && c === mark;
    body += `<g class="dsa-node${isS ? " sentinel" : ""}${hot ? " hot" : ""}"><rect x="${x}" y="${Y}" width="${W}" height="${H}" rx="5"/>`;
    body += doubly ? `<line x1="${x + 16}" y1="${Y}" x2="${x + 16}" y2="${Y + H}"/><line x1="${x + W - 16}" y1="${Y}" x2="${x + W - 16}" y2="${Y + H}"/>${dsaText(x + W / 2, Y + 21, isS ? "S" : c.v, "dsa-val")}`
      : `<line x1="${x + W - 18}" y1="${Y}" x2="${x + W - 18}" y2="${Y + H}"/>${dsaText(x + (W - 18) / 2, Y + 21, c.v, "dsa-val")}`;
    body += `</g>`;
  });
  // next pointers (upper lane for doubly), prev pointers (lower lane)
  cells.forEach((c, i) => {
    const x = xs[i], nx = c.next ? at.get(c.next) : null;
    const yN = doubly ? Y + 11 : Y + H / 2, yP = Y + H - 11;
    if (c.next && nx !== undefined && nx > x) body += arrow(x + W - 8, yN, nx - 2, yN);
    if (doubly && c.prev && at.get(c.prev) !== undefined && at.get(c.prev) < x) body += arrow(x + 8, yP, at.get(c.prev) + W + 2, yP, "prev", "dsa-ah2");
  });
  const last = cells[cells.length - 1], first = cells[0];
  if (!cells.length) body += dsaText(X0, Y + 21, kind === "csll" ? "tail = None (empty ring)" : "head = None (empty list)", "dsa-note", "start");
  if (cells.length && !circular) { // null terminators
    body += arrow(at.get(last) + W - 8, doubly ? Y + 11 : Y + H / 2, at.get(last) + W + 24, doubly ? Y + 11 : Y + H / 2) + dsaText(at.get(last) + W + 36, (doubly ? Y + 11 : Y + H / 2) + 4, "∅", "dsa-null");
    if (doubly) body += arrow(at.get(first) + 8, Y + H - 11, at.get(first) - 18, Y + H - 11, "prev", "dsa-ah2") + dsaText(at.get(first) - 22, Y + H - 7, "∅", "dsa-null", "end");
  }
  if (cells.length && circular) { // the wrap-around pointers
    const xl = at.get(last), xf = at.get(first);
    if (cells.length === 1) body += `<path class="dsa-edge wrap" d="M ${xl + W - 8} ${Y + H} C ${xl + W + 30} ${Y + H + 40}, ${xl - 30} ${Y + H + 40}, ${xl + 10} ${Y + H + 2}" marker-end="url(#dsa-ah3)"/>`;
    else body += `<path class="dsa-edge wrap" d="M ${xl + W / 2 + 8} ${Y + H} C ${xl + W / 2 + 8} ${Y + H + 46}, ${xf + W / 2 - 8} ${Y + H + 46}, ${xf + W / 2 - 8} ${Y + H + 3}" marker-end="url(#dsa-ah3)"/>` + dsaText((xl + xf + W) / 2, Y + H + 50, kind === "csll" ? "tail.next = head (the ring)" : "last.next = sentinel", "dsa-wrap-label");
    if (kind === "cdll" && cells.length > 1) body += `<path class="dsa-edge prev" d="M ${xf + W / 2 + 8} ${Y + H} C ${xf + W / 2 + 8} ${Y + H + 30}, ${xl + W / 2 - 8} ${Y + H + 30}, ${xl + W / 2 - 8} ${Y + H + 3}" marker-end="url(#dsa-ah2)"/>` + dsaText((xl + xf + W) / 2, Y + H + 14, "sentinel.prev = last", "dsa-wrap-label prev");
  }
  // named pointers above the boxes
  const label = (node, text, dy = 0) => { const x = at.get(node); if (x === undefined) return ""; return dsaText(x + W / 2, 24 + dy, text, "dsa-ptr") + arrow(x + W / 2, 30 + dy, x + W / 2, Y - 3, "ptr", "dsa-ah3"); };
  if (cells.length) {
    if (kind === "sll" || kind === "dll") body += label(L.head, "head") + (L.tail === L.head ? dsaText(at.get(L.tail) + W / 2, 12, "tail", "dsa-ptr") : label(L.tail, "tail"));
    if (kind === "csll") body += label(L.tail, "tail") + (L.head !== L.tail ? dsaText(at.get(L.head) + W / 2, 24, "head = tail.next", "dsa-ptr dim") : "");
    if (kind === "cdll") body += label(L.s, "sentinel") + (nodes.length ? dsaText(at.get(L.s.next) + W / 2, 24, "first", "dsa-ptr dim") : "");
  }
  return dsaSvg(width, height, `${DSA_KINDS[kind].label} with ${L.size} nodes`, body, "dsa-list");
}

function dsaListOp(op) {
  const L = dsa.list, kind = dsa.listKind;
  let r = null, text = "";
  if (op === "push-front" || op === "push-back") {
    if (L.size >= 8) { dsa.listLog.push({ op, text: "the drawing holds 8 nodes — pop one first" }); return; }
    const v = 10 * dsa.listNext++;
    r = op === "push-front" ? L.pushFront(v) : L.pushBack(v);
    text = `inserted ${v}`;
  } else if (op === "pop-front" || op === "pop-back") {
    if (!L.size) { dsa.listLog.push({ op, text: "empty — IndexError in Python" }); return; }
    r = op === "pop-front" ? L.popFront() : L.popBack();
    text = `removed ${r.value}` + (r.hops ? ` after ${r.hops} pointer step(s)` : "");
  } else if (op.startsWith("rotate-")) {
    if (!L.size) return;
    const k = Number(op.slice(7));
    r = L.rotate(k);
    text = `start advanced by ${k}; ${r.hops} pointer move(s), no values copied`;
  }
  dsa.listLast = r;
  dsa.listLog.push({ op: op.replace("-", "_") + (op.startsWith("rotate") ? "" : "()"), text, cost: r?.cost || "" });
  announce(`${DSA_KINDS[kind].label}: ${text}`);
}

// Josephus on a circular singly list (josephus_circular): prev walks k−1 steps, then prev.next leaves.
function dsaJosNew() {
  const ring = new DsaCircularSingly();
  for (let i = 1; i <= dsa.josN; i++) ring.pushBack(i);
  dsa.jos = { ring, prev: ring.tail, order: [], moves: 0, last: null };
}
function dsaJosStep() {
  const J = dsa.jos, R = J.ring;
  if (!R.size) return;
  for (let i = 0; i < dsa.josK - 1; i++) { J.prev = J.prev.next; J.moves += 1; }
  const victim = J.prev.next;
  J.order.push(victim.v); J.last = victim.v;
  if (victim === J.prev) R.tail = null;
  else { J.prev.next = victim.next; if (victim === R.tail) R.tail = J.prev; }
  R.size -= 1;
}
function dsaJosFormula(n, k) { let r = 0; for (let i = 2; i <= n; i++) r = (r + k) % i; return r + 1; }
function dsaJosListShifts(n, k) { const p = Array.from({ length: n }, (_, i) => i + 1); let s = 0, i = 0; while (p.length) { i = (i + k - 1) % p.length; s += p.length - i - 1; p.splice(i, 1); } return s; }

function dsaJosSvg() {
  const J = dsa.jos, n = dsa.josN, R = 92, C = 120, alive = new Set(J.ring.nodes().map((x) => x.v));
  const pos = (v) => { const a = -Math.PI / 2 + ((v - 1) / n) * 2 * Math.PI; return [C + R * Math.cos(a), C + R * Math.sin(a)]; };
  let body = `<circle class="dsa-orbit" cx="${C}" cy="${C}" r="${R}"/>`;
  const live = J.ring.nodes();
  live.forEach((node) => { if (live.length < 2) return; const [x1, y1] = pos(node.v), [x2, y2] = pos(node.next.v); const d = Math.hypot(x2 - x1, y2 - y1), ux = (x2 - x1) / d, uy = (y2 - y1) / d; body += `<line class="dsa-edge" x1="${x1 + ux * 15}" y1="${y1 + uy * 15}" x2="${x2 - ux * 16}" y2="${y2 - uy * 16}" marker-end="url(#dsa-ah)"/>`; });
  for (let v = 1; v <= n; v++) {
    const [x, y] = pos(v), out = !alive.has(v), idx = J.order.indexOf(v), isPrev = J.ring.size && J.prev.v === v;
    body += `<g class="dsa-person${out ? " out" : ""}${isPrev ? " prev" : ""}${J.last === v ? " last" : ""}"><circle cx="${x}" cy="${y}" r="14"/>${dsaText(x, y + 4, v)}${out ? dsaText(x, y + 27, "#" + (idx + 1), "dsa-out-n") : ""}</g>`;
  }
  body += dsaText(C, C - 4, J.ring.size ? `${J.ring.size} left` : `survivor ${J.order[J.order.length - 1]}`, "dsa-center") + dsaText(C, C + 13, `k = ${dsa.josK}`, "dsa-center dim");
  return dsaSvg(240, 240, `Josephus ring, n = ${n}, k = ${dsa.josK}`, body, "dsa-jos");
}

const DSA_LIST_COSTS = [
  ["push_front", "O(1)", "O(1)", "O(1) — insert after tail", "O(1) — insert after sentinel"],
  ["push_back", "O(1) with a tail pointer", "O(1)", "O(1) — insert after tail, advance tail", "O(1) — insert after sentinel.prev"],
  ["pop_front", "O(1)", "O(1)", "O(1)", "O(1)"],
  ["pop_back", "<b>O(n)</b> — walk to the predecessor", "O(1) — tail.prev", "<b>O(n)</b> — walk round the ring", "O(1) — sentinel.prev"],
  ["remove(known node)", "O(n) — need its predecessor", "O(1) — unlink", "O(n)", "O(1) — unlink"],
  ["rotate(k)", "O(n) — relink head and tail", "O(n)", "O(k) — move tail only", "O(min(k, n−k)) — move the sentinel"],
  ["Special cases", "empty list, one node, head = tail", "empty, one node, four pointer updates", "one-node ring points to itself", "none — the sentinel is always there"],
];

function dsaLists() {
  if (!dsa.list) dsaListNew();
  if (!dsa.jos) dsaJosNew();
  const L = dsa.list, kind = dsa.listKind, k = DSA_KINDS[kind], ok = L.validate(), J = dsa.jos;
  const values = L.nodes().map((x) => x.v);
  const forward = kind === "cdll" || kind === "dll" ? `forward [${values.join(", ")}] · backward [${[...values].reverse().join(", ")}]` : `[${values.join(", ")}]`;
  return `<div class="sec-intro"><p>A linked list stores each value in a <strong>node</strong> that points to the next one, so inserting or removing at a known place means changing a few pointers instead of shifting an array. The four kinds differ in <em>which</em> pointers they keep, and that decides which operations are O(1) (${dsaLessons(5, 6, 7, 8)}). Pick a kind and operate on it: the picture is drawn by following the structure's own <code>next</code>/<code>prev</code> pointers.</p></div>
    ${secSection("LIVE", "Operate on a real linked list", `<div class="sec-row">${dsaSelect("kind", "List kind", Object.entries(DSA_KINDS).map(([id, x]) => [id, x.label]), kind)}</div>
      <div class="sec-actions">${dsaButton("push-front", "push_front", { iconName: "previous" })}${dsaButton("push-back", "push_back", { iconName: "chevron" })}${dsaButton("pop-front", "pop_front")}${dsaButton("pop-back", "pop_back")}${k.rotate ? dsaButton("rotate-1", "rotate(1)", { iconName: "reset" }) + dsaButton("rotate-3", "rotate(3)") : ""}${dsaButton("list-reset", "Reset", { iconName: "reset" })}</div>
      <div class="dsa-canvas">${dsaListSvg(L, kind, dsa.listLast?.node)}</div>
      ${dsaPills([[`size ${L.size}`], [forward], [ok ? "invariant holds (validate())" : "INVARIANT BROKEN", ok ? "good" : "bad"]])}
      ${dsa.listLast ? `<p class="sec-label">Pointer writes in the last operation (${dsa.listLast.cost}${dsa.listLast.hops ? `, ${dsa.listLast.hops} step(s) walked` : ""})</p>${dsaOps(dsa.listLast.ops)}` : ""}
      ${dsaLog(dsa.listLog)}
      <p class="sec-note">${icon("nodes", 14)}<span class="dsa-t">${kind === "csll" ? "Only <code>tail</code> is stored: the head is <code>tail.next</code>, so both ends are reachable in one step. Try <b>pop_back</b> — it must walk all the way round to find the node before the tail." : kind === "cdll" ? "The sentinel never holds data; an empty list is a sentinel pointing to itself, so <code>insert_after</code> and <code>unlink</code> are the only two primitives and have no special cases. <b>rotate</b> moves only the sentinel." : kind === "dll" ? "Every node knows its predecessor, so <b>pop_back</b> and unlinking a known node are O(1) — at the cost of one extra pointer per node and four pointer updates per insert." : "With only <code>next</code> pointers, removing the last node needs its predecessor: <b>pop_back</b> walks the whole list."} ${dsaLesson(k.lesson, "Read the lesson")}.</span></p>`)}
    ${secSection("COMPARE", "The same operations on all four kinds", secTable(["Operation", "Singly", "Doubly", "Circular singly", "Circular doubly + sentinel"], DSA_LIST_COSTS))}
    ${secSection("RING", "Josephus problem on a circular singly linked list (josephus_circular)", `<p class="sec-text">n people stand in a circle; counting starts at person 1 and every k-th person leaves. On a ring the pointer <code>prev</code> simply walks k − 1 steps and unlinks <code>prev.next</code> — no index arithmetic, no shifting.</p>
      <div class="sec-row">${dsaSelect("josn", "People n", [5, 6, 7, 8, 9, 10, 12, 16].map((v) => [v, v]), dsa.josN)}${dsaSelect("josk", "Every k-th", [2, 3, 4, 5].map((v) => [v, v]), dsa.josK)}</div>
      <div class="sec-actions">${dsaButton("jos-step", "Eliminate next", { primary: true, iconName: "play", disabled: !J.ring.size })}${dsaButton("jos-run", "Run to the end", { disabled: !J.ring.size })}${dsaButton("jos-reset", "Reset", { iconName: "reset" })}</div>
      <div class="dsa-two"><div class="dsa-canvas small">${dsaJosSvg()}</div>
      <div>${secTable(["Quantity", "Value"], [
        ["Elimination order", J.order.length ? J.order.join(" → ") : "—"],
        ["Pointer moves so far", J.moves],
        ["Survivor (formula J(n,k), O(n))", dsaJosFormula(dsa.josN, dsa.josK)],
        ["Pointer moves, whole run (ring)", `${dsa.josN * (dsa.josK - 1)} = n(k − 1)`],
        ["Elements shifted by list.pop(i)", dsaJosListShifts(dsa.josN, dsa.josK)],
      ])}</div></div>
      <p class="sec-note">${icon("ring", 14)}<span class="dsa-t">Experiment E21 runs this for n up to 20 000: the ring does exactly n(k − 1) pointer moves, while the array version shifts ~n²/2 elements — but C's <code>memmove</code> is so fast that the array still wins for small n. Counts and times answer different questions.</span></p>`)}`;
}

// Floyd's tortoise and hare on a rho-shaped list: mu nodes before the cycle, lambda nodes on it (floyd_cycle).
function dsaFloydNew(mu = dsa.floyd?.mu ?? 3, lam = dsa.floyd?.lam ?? 5) {
  const nodes = Array.from({ length: mu + lam }, (_, i) => new DsaNode(i));
  nodes.forEach((n, i) => { n.next = nodes[i + 1] || nodes[mu]; });
  dsa.floyd = { mu, lam, nodes, slow: nodes[0], fast: nodes[0], phase: 1, steps: 0, found: null, log: ["slow = fast = head"] };
}
function dsaFloydStep() {
  const F = dsa.floyd;
  if (F.phase === 1) {
    F.slow = F.slow.next; F.fast = F.fast.next.next; F.steps += 1;
    F.log.push(`phase 1, step ${F.steps}: slow → ${F.slow.v}, fast → ${F.fast.v}`);
    if (F.slow === F.fast) { F.phase = 2; F.slow = F.nodes[0]; F.m = 0; F.log.push(`they meet at node ${F.fast.v}: a cycle exists. Reset slow to head.`); }
  } else if (F.phase === 2) {
    if (F.slow === F.fast) { F.phase = 3; F.found = { mu: F.m, start: F.slow.v }; F.lamCount = 1; F.probe = F.slow.next; F.log.push(`slow and fast meet at node ${F.slow.v}: the cycle starts μ = ${F.m} steps from head.`); }
    else { F.slow = F.slow.next; F.fast = F.fast.next; F.m += 1; F.log.push(`phase 2: both move one step → ${F.slow.v}, ${F.fast.v}`); }
  } else if (F.phase === 3) {
    if (F.probe === F.slow) { F.phase = 4; F.found.lam = F.lamCount; F.log.push(`walked once round the loop: λ = ${F.lamCount}.`); }
    else { F.probe = F.probe.next; F.lamCount += 1; }
  }
}
function dsaFloydSvg() {
  const F = dsa.floyd, R = Math.max(34, F.lam * 11), Y = R + 34, cx = 40 + F.mu * 52 + R + 10;
  const pos = (i) => (i < F.mu ? [30 + i * 52, Y] : (() => { const a = Math.PI + ((i - F.mu) / F.lam) * 2 * Math.PI; return [cx + R * Math.cos(a), Y + R * Math.sin(a)]; })());
  let body = "";
  F.nodes.forEach((n) => { const [x1, y1] = pos(n.v), [x2, y2] = pos(n.next.v); const d = Math.hypot(x2 - x1, y2 - y1) || 1, ux = (x2 - x1) / d, uy = (y2 - y1) / d; body += `<line class="dsa-edge" x1="${x1 + ux * 13}" y1="${y1 + uy * 13}" x2="${x2 - ux * 15}" y2="${y2 - uy * 15}" marker-end="url(#dsa-ah)"/>`; });
  F.nodes.forEach((n) => { const [x, y] = pos(n.v), cls = [n === F.slow ? "slow" : "", n === F.fast ? "fast" : "", n.v === F.mu ? "entry" : ""].join(" "); body += `<g class="dsa-person ${cls}"><circle cx="${x}" cy="${y}" r="12"/>${dsaText(x, y + 4, n.v)}</g>`; });
  const tag = (node, t, dy, cls) => { const [x, y] = pos(node.v); return dsaText(x, y + dy, t, `dsa-ptr ${cls}`); };
  body += tag(F.slow, "slow", -20, "slow") + tag(F.fast, "fast", F.slow === F.fast ? -32 : 28, "fast");
  return dsaSvg(cx + R + 30, Y + R + 30, `List with a cycle: mu ${F.mu}, lambda ${F.lam}`, body, "dsa-floyd");
}
function dsaFloyd() {
  if (!dsa.floyd) dsaFloydNew();
  const F = dsa.floyd;
  return secSection("CYCLES", "Floyd's tortoise and hare (floyd_cycle)", `<p class="sec-text">A corrupted list can loop back on itself, and a plain traversal never ends. Two pointers walk at speeds 1 and 2; if there is a cycle they must meet inside it. Resetting one to the head and moving both one step at a time then finds where the cycle starts (μ), and one more lap measures its length (λ) — in O(μ + λ) time and O(1) extra memory.</p>
    <div class="sec-row">${dsaSelect("fmu", "Tail length μ", [0, 1, 2, 3, 4, 5].map((v) => [v, v]), F.mu)}${dsaSelect("flam", "Cycle length λ", [1, 2, 3, 4, 5, 6, 7].map((v) => [v, v]), F.lam)}</div>
    <div class="sec-actions">${dsaButton("floyd-step", "Step", { primary: true, iconName: "play", disabled: F.phase === 4 })}${dsaButton("floyd-run", "Run to the end", { disabled: F.phase === 4 })}${dsaButton("floyd-reset", "Reset", { iconName: "reset" })}</div>
    <div class="dsa-canvas">${dsaFloydSvg()}</div>
    ${dsaPills([[`phase ${Math.min(F.phase, 3)} of 3`], [`steps ${F.steps}`], F.found ? [`μ = ${F.found.mu}${F.found.lam ? `, λ = ${F.found.lam}` : ""}`, "good"] : ["searching…"]])}
    <ol class="dsa-log">${F.log.slice(-4).reverse().map((l) => `<li><span>${secEsc(l)}</span></li>`).join("")}</ol>`);
}

// ================================================================== stacks, queues, ring buffer, LRU
// A stack evaluates the app's fare rule in postfix: fare = (350 + km × 170) × 130 // 100 (comfort), domain.fare.
const DSA_POSTFIX = ["350", "3", "170", "*", "+", "130", "*", "100", "//"];
function dsaPostfixTrace() {
  const st = [], frames = [];
  for (const t of DSA_POSTFIX) {
    if (/^\d+$/.test(t)) { st.push(Number(t)); frames.push([t, `push ${t}`, [...st]]); }
    else { const b = st.pop(), a = st.pop(), r = t === "+" ? a + b : t === "*" ? a * b : Math.floor(a / b); st.push(r); frames.push([t, `pop ${b}, pop ${a}, push ${a} ${t} ${b} = ${r}`, [...st]]); }
  }
  return frames;
}

function dsaRingNew(cap = 8) { dsa.ring = { cap, buf: Array(cap).fill(null), front: 0, count: 0, next: 1, log: [], copies: 0 }; for (let i = 0; i < 5; i++) dsaRingOp("enq"); dsaRingOp("deq"); dsaRingOp("deq"); dsa.ring.log = []; }
function dsaRingOp(op) {
  const R = dsa.ring;
  if (op === "enq") {
    if (R.count === R.cap) {
      if (!dsa.ringGrow) { R.log.push({ op: "enqueue()", text: "full — overflow (a bounded queue rejects, or a growable one doubles)", cost: "" }); return; }
      const old = R.cap, nb = Array(old * 2).fill(null); for (let i = 0; i < R.count; i++) nb[i] = R.buf[(R.front + i) % old];
      R.buf = nb; R.cap = old * 2; R.front = 0; R.copies += R.count;
      R.log.push({ op: "_resize()", text: `doubled ${old} → ${R.cap}: copied ${R.count} items in queue order, front reset to 0`, cost: "O(n), amortised O(1)" });
    }
    const at = (R.front + R.count) % R.cap, v = R.next++;
    R.buf[at] = v; R.count += 1;
    R.log.push({ op: "enqueue()", text: `wrote ${v} at (front + count) % capacity = (${R.front} + ${R.count - 1}) % ${R.cap} = ${at}`, cost: "O(1)" });
  } else {
    if (!R.count) { R.log.push({ op: "dequeue()", text: "empty — underflow", cost: "" }); return; }
    const v = R.buf[R.front]; R.buf[R.front] = null; const old = R.front; R.front = (R.front + 1) % R.cap; R.count -= 1;
    R.log.push({ op: "dequeue()", text: `read ${v} at front = ${old}; front = (${old} + 1) % ${R.cap} = ${R.front}`, cost: "O(1)" });
  }
}
function dsaRingSvg() {
  const R = dsa.ring, n = R.cap, C = 120, r1 = 96, r0 = 58, back = (R.front + R.count) % n;
  let body = "";
  for (let i = 0; i < n; i++) {
    const a0 = -Math.PI / 2 + (i / n) * 2 * Math.PI + 0.02, a1 = -Math.PI / 2 + ((i + 1) / n) * 2 * Math.PI - 0.02, am = (a0 + a1) / 2;
    const p = (r, a) => `${(C + r * Math.cos(a)).toFixed(1)} ${(C + r * Math.sin(a)).toFixed(1)}`;
    const used = R.buf[i] !== null, large = a1 - a0 > Math.PI ? 1 : 0;
    body += `<path class="dsa-cell${used ? " used" : ""}${i === R.front && R.count ? " front" : ""}" d="M ${p(r0, a0)} L ${p(r1, a0)} A ${r1} ${r1} 0 ${large} 1 ${p(r1, a1)} L ${p(r0, a1)} A ${r0} ${r0} 0 ${large} 0 ${p(r0, a0)} Z"/>`;
    body += dsaText(C + ((r0 + r1) / 2) * Math.cos(am), C + ((r0 + r1) / 2) * Math.sin(am) + 4, used ? R.buf[i] : "·", "dsa-val");
    if (n <= 16) body += dsaText(C + (r1 + 11) * Math.cos(am), C + (r1 + 11) * Math.sin(am) + 3, i, "dsa-idx");
  }
  const mark = (i, t, cls, rr) => { const am = -Math.PI / 2 + ((i + 0.5) / n) * 2 * Math.PI; return `<line class="dsa-edge ${cls}" x1="${C + 30 * Math.cos(am)}" y1="${C + 30 * Math.sin(am)}" x2="${C + (r0 - 4) * Math.cos(am)}" y2="${C + (r0 - 4) * Math.sin(am)}" marker-end="url(#${cls === "front" ? "dsa-ah3" : "dsa-ah2"})"/>` + dsaText(C + rr * Math.cos(am), C + rr * Math.sin(am) + 3, t, `dsa-ptr ${cls}`); };
  if (R.count) body += mark(R.front, "front", "front", 17);
  body += mark(back, "back", "back", R.count && back === R.front ? 5 : 17);
  return dsaSvg(240, 240, `Ring buffer, capacity ${n}, ${R.count} items`, body, "dsa-ringbuf");
}

const DSA_TILES = ["UCC", "Mardyke", "City", "Kent", "Douglas", "Airport"];
function dsaLruNew() { dsa.lru = { cap: 4, list: new DsaCircularDoubly(), map: new Map(), hits: 0, misses: 0, log: [], last: null }; ["UCC", "City", "Kent"].forEach(dsaLruGet); Object.assign(dsa.lru, { hits: 0, misses: 0, log: [], last: null }); }
function dsaLruGet(key) {
  const C = dsa.lru, node = C.map.get(key);
  if (node) { // move_to_front
    C.hits += 1; node.prev.next = node.next; node.next.prev = node.prev; node.prev = C.list.s; node.next = C.list.s.next; C.list.s.next.prev = node; C.list.s.next = node;
    C.last = node; C.log.push({ op: `get(${key})`, text: "hit — move_to_front: 4 pointer writes, no search", cost: "O(1)" });
    return;
  }
  C.misses += 1; let text = "miss — load the tile, push_front";
  if (C.map.size === C.cap) { const old = C.list.s.prev; C.list.unlink(old); C.map.delete(old.v); text += `; evicted least recent ${old.v} (pop_back)`; }
  C.last = C.list.pushFront(key).node; C.map.set(key, C.last);
  C.log.push({ op: `get(${key})`, text, cost: "O(1)" });
}

function dsaQueues() {
  if (!dsa.ring) dsaRingNew();
  if (!dsa.lru) dsaLruNew();
  const R = dsa.ring, C = dsa.lru, frames = dsaPostfixTrace();
  const queue = Array.from({ length: R.count }, (_, i) => R.buf[(R.front + i) % R.cap]);
  const lruKeys = C.list.nodes().map((x) => x.v);
  return `<div class="sec-intro"><p>A <strong>stack</strong> (last in, first out) and a <strong>queue</strong> (first in, first out) are defined by their operations, not their storage (${dsaLessons(9, 10)}). A queue on a plain array wastes O(n) per dequeue shifting elements; a <strong>ring buffer</strong> lets the indices wrap round instead. An <strong>LRU cache</strong> combines a hash map with a circular doubly linked list — and the app's map uses one (${dsaLesson(8)}).</p></div>
    ${secSection("STACK", "Evaluate the app's comfort fare with a stack (domain.fare, 3 km)", `${secCode("fare = (350 + km × 170) × 130 // 100      postfix:  " + DSA_POSTFIX.join(" "))}
      ${secTable(["Token", "Action", "Stack after (bottom → top)"], frames.map(([t, a, s]) => [`<code>${t}</code>`, a, `<code>[${s.join(", ")}]</code>`]))}
      <p class="sec-note">${icon("stack", 14)}<span class="dsa-t">The final stack holds 1118 cents = <b>€11.18</b>, exactly what <code>domain.fare(0, 1, comfort=True)</code> returns for UCC → City Centre. The app's tile loader also uses a stack: <code>queue.LifoQueue()</code> fetches the most recently requested tile first, so the part of the map you just scrolled to appears before stale requests.</span></p>`)}
    ${secSection("RING BUFFER", "Queue on a circular array (RingBuffer)", `<div class="sec-actions">${dsaButton("ring-enq", "enqueue", { primary: true, iconName: "chevron" })}${dsaButton("ring-deq", "dequeue", { iconName: "previous" })}${dsaButton("ring-enq3", "enqueue × 3")}${dsaButton("ring-grow", dsa.ringGrow ? "Growable: on" : "Growable: off")}${dsaButton("ring-reset", "Reset", { iconName: "reset" })}</div>
      <div class="dsa-two"><div class="dsa-canvas small">${dsaRingSvg()}</div><div>
      ${secCode(`back  = (front + count) % capacity
enqueue:  buf[back] = x;  count += 1
dequeue:  x = buf[front];  front = (front + 1) % capacity;  count -= 1`)}
      ${dsaPills([[`capacity ${R.cap}`], [`count ${R.count}`], [`front ${R.front}`], [`queue [${queue.join(", ")}]`], [`items copied by resizing ${R.copies}`]])}
      ${dsaLog(R.log)}</div></div>
      <p class="sec-note">${icon("ring", 14)}<span class="dsa-t">No element ever moves on enqueue or dequeue — only two indices change. Keep dequeuing and enqueuing and watch <code>back</code> wrap past index ${R.cap - 1} to 0. Experiment E23: <code>list.pop(0)</code> is O(n) per dequeue; the ring and <code>collections.deque</code> are O(1).</span></p>`)}
    ${secSection("LRU CACHE", "Least-recently-used cache = dict + circular doubly linked list (LRUCache)", `<p class="sec-text">Capacity ${C.cap}. Request map tiles; the most recent is at the front, the least recent sits just before the sentinel and is evicted when the cache is full.</p>
      <div class="sec-actions">${DSA_TILES.map((k) => dsaButton("lru-" + k, "get " + k, { iconName: "map" })).join("")}${dsaButton("lru-reset", "Reset", { iconName: "reset" })}</div>
      <div class="dsa-canvas">${dsaListSvg(C.list, "cdll", C.last)}</div>
      ${dsaPills([[`order (most → least recent) [${lruKeys.join(", ")}]`], [`dict keys {${[...C.map.keys()].join(", ")}}`], [`hits ${C.hits}`, "good"], [`misses ${C.misses}`, C.misses ? "bad" : ""]])}
      ${dsaLog(C.log)}
      ${secTable(["", "Course LRUCache", "ATLAS Go TileLoader (livemap.py)"], [
        ["Lookup", "<code>self.nodes[key]</code> (dict)", "<code>self.textures.get(key)</code> (OrderedDict)"],
        ["On a hit", "<code>move_to_front(node)</code>", "<code>self.textures.move_to_end(key)</code>"],
        ["On overflow", "<code>pop_back()</code> — least recent", "<code>popitem(last=False)</code> while more than 160 tiles"],
        ["Recency order", "front = most recent", "end = most recent"],
        ["Underneath", "dict + circular doubly list with a sentinel", "dict + a doubly linked list (the pure-Python <code>OrderedDict</code> uses a circular one with a sentinel root)"],
      ])}`)}
    ${secSection("CHOOSE", "Which structure for which job?", secTable(["Need", "Use", "Why"], [
      ["Undo, recursion, bracket matching, postfix", "stack (<code>list.append</code>/<code>pop</code>)", "only the top is touched: O(1)"],
      ["FIFO with unbounded growth", "<code>collections.deque</code>", "O(1) at both ends"],
      ["FIFO with a fixed memory budget (telemetry, audio)", "ring buffer", "no allocation after start; overwrite or reject when full"],
      ["Bounded cache with recency eviction", "OrderedDict / dict + doubly list", "O(1) lookup, O(1) recency update, O(1) eviction"],
      ["Newest-first work queue", "LIFO queue", "what the map tile loader does"],
    ]))}`;
}

// ================================================================== hash tables
const DSA_KEYS = ["bowl", "wrap", "juice", "pizza", "garlic", "water", "curry", "dosa", "lassi", "UCC Campus", "Cork City Centre", "Kent Station", "Cork Airport", "Mardyke", "Douglas", "Blackpool"];
const dsaHashOf = (key) => { let h = 0; for (const ch of key) h = (Math.imul(h, 31) + ch.codePointAt(0)) >>> 0; return h; }; // Java-style polynomial hash

function dsaHashNew() { const H = dsa.hash = { m: dsa.hashM, chains: Array.from({ length: dsa.hashM }, () => []), slots: Array(dsa.hashM).fill(null), size: 0, next: 0, log: [], resizes: 0, last: null }; for (let i = 0; i < 4; i++) dsaHashPut(H, DSA_KEYS[H.next++], true); }
function dsaHashResize(H, m) {
  const keys = dsa.hashMode === "chain" ? H.chains.flat() : H.slots.filter((s) => s && s !== "⌫");
  H.m = m; H.chains = Array.from({ length: m }, () => []); H.slots = Array(m).fill(null); H.size = 0; H.resizes += 1;
  for (const k of keys) dsaHashPut(H, k, true);
}
function dsaHashPut(H, key, quiet = false) {
  const h = dsaHashOf(key), i = h % H.m;
  if (dsa.hashMode === "chain") {
    const chain = H.chains[i], steps = chain.length; chain.push(key); H.size += 1; H.last = key;
    if (!quiet) H.log.push({ op: `put("${key}")`, text: `hash ${h} mod ${H.m} = ${i}; walked a chain of ${steps}`, cost: `${steps + 1} probe(s)` });
    if (dsa.hashResize && H.size / H.m > 1.0 && !quiet) { const m = 2 * H.m + 1; dsaHashResize(H, m); H.log.push({ op: "_resize()", text: `load factor passed 1.0 → rehashed every key into ${m} buckets`, cost: "O(n)" }); }
  } else {
    let j = i, probes = 1, tomb = -1;
    while (H.slots[j] !== null) { if (H.slots[j] === "⌫" && tomb < 0) tomb = j; j = (j + 1) % H.m; probes += 1; if (probes > H.m) break; }
    const at = tomb >= 0 ? tomb : j; H.slots[at] = key; H.size += 1; H.last = key;
    if (!quiet) H.log.push({ op: `put("${key}")`, text: `hash ${h} mod ${H.m} = ${i}; ${probes > 1 ? `collided, probed to slot ${at}` : "slot was free"}`, cost: `${probes} probe(s)` });
    if (dsa.hashResize && H.size / H.m > 0.7 && !quiet) { const m = 2 * H.m + 1; dsaHashResize(H, m); H.log.push({ op: "_resize()", text: `load factor passed 0.7 → rehashed into ${m} slots (tombstones dropped)`, cost: "O(n)" }); }
  }
}
function dsaHashDelete(H) {
  const keys = dsa.hashMode === "chain" ? H.chains.flat() : H.slots.filter((s) => s && s !== "⌫");
  if (!keys.length) return;
  const key = keys[0], i = dsaHashOf(key) % H.m;
  if (dsa.hashMode === "chain") { H.chains[i].splice(H.chains[i].indexOf(key), 1); H.log.push({ op: `delete("${key}")`, text: `unlinked it from chain ${i}`, cost: "O(1 + chain)" }); }
  else { const j = H.slots.indexOf(key); H.slots[j] = "⌫"; H.log.push({ op: `delete("${key}")`, text: `slot ${j} becomes a tombstone ⌫ — emptying it would break the probe sequence of keys after it`, cost: "O(1 + probes)" }); }
  H.size -= 1;
}
function dsaHashStats(H) {
  const keys = dsa.hashMode === "chain" ? H.chains.flat() : H.slots.filter((s) => s && s !== "⌫");
  let total = 0, worst = 0;
  for (const k of keys) {
    let p;
    if (dsa.hashMode === "chain") p = H.chains[dsaHashOf(k) % H.m].indexOf(k) + 1;
    else { let j = dsaHashOf(k) % H.m; p = 1; while (H.slots[j] !== k) { j = (j + 1) % H.m; p += 1; } }
    total += p; worst = Math.max(worst, p);
  }
  return { avg: keys.length ? total / keys.length : 0, worst, tombs: H.slots.filter((s) => s === "⌫").length };
}

function dsaHashSvg(H) {
  const rowH = 26, top = 8, W = 600, chain = dsa.hashMode === "chain";
  let body = "";
  for (let i = 0; i < H.m; i++) {
    const y = top + i * rowH;
    body += `<g class="dsa-bucket"><rect x="8" y="${y}" width="38" height="${rowH - 6}" rx="3"/>${dsaText(27, y + 14, i, "dsa-idx")}</g>`;
    if (chain) {
      H.chains[i].forEach((k, j) => { const x = 66 + j * 132; body += `<line class="dsa-edge" x1="${j ? x - 14 : 46}" y1="${y + 10}" x2="${x - 2}" y2="${y + 10}" marker-end="url(#dsa-ah)"/><g class="dsa-node${k === H.last ? " hot" : ""}"><rect x="${x}" y="${y}" width="118" height="${rowH - 6}" rx="4"/>${dsaText(x + 59, y + 14, k.length > 15 ? k.slice(0, 14) + "…" : k, "dsa-key")}</g>`; });
      if (!H.chains[i].length) body += dsaText(58, y + 14, "∅", "dsa-null", "start");
    } else {
      const s = H.slots[i];
      body += s === null ? dsaText(58, y + 14, "empty", "dsa-null", "start") : `<g class="dsa-node${s === "⌫" ? " tomb" : s === H.last ? " hot" : ""}"><rect x="58" y="${y}" width="150" height="${rowH - 6}" rx="4"/>${dsaText(133, y + 14, s === "⌫" ? "⌫ tombstone" : s, "dsa-key")}</g>${s !== "⌫" && dsaHashOf(s) % H.m !== i ? dsaText(218, y + 14, `home ${dsaHashOf(s) % H.m} → displaced ${(i - (dsaHashOf(s) % H.m) + H.m) % H.m}`, "dsa-note", "start") : ""}`;
    }
  }
  return dsaSvg(W, top + H.m * rowH + 4, `Hash table with ${H.m} buckets`, body, "dsa-hash");
}

function dsaHashing() {
  if (!dsa.hash) dsaHashNew();
  const H = dsa.hash, st = dsaHashStats(H), chain = dsa.hashMode === "chain", alpha = H.size / H.m, nextKey = DSA_KEYS[H.next % DSA_KEYS.length];
  const theory = chain ? [`expected successful search ≈ 1 + α/2 = ${(1 + alpha / 2).toFixed(2)}`] : alpha < 1 ? [`expected successful search ≈ ½(1 + 1/(1−α)) = ${(0.5 * (1 + 1 / (1 - alpha))).toFixed(2)}`] : ["α ≥ 1 — table full"];
  return `<div class="sec-intro"><p>A <strong>hash table</strong> turns a key into an array index with a hash function, giving O(1) average lookup. Two keys can land in the same bucket (a <strong>collision</strong>); <strong>separate chaining</strong> keeps a small linked list per bucket, <strong>open addressing</strong> probes for the next free slot. Everything hinges on the <strong>load factor</strong> α = n / m (${dsaLesson(11)}). The keys are the app's dish ids (<code>domain.DISHES</code>) and Cork place names.</p></div>
    ${secSection("LIVE", "Insert the app's keys and watch the buckets fill", `<div class="sec-row">${dsaSelect("hmode", "Collision strategy", [["chain", "Separate chaining"], ["probe", "Open addressing (linear probing)"]], dsa.hashMode)}${dsaSelect("hm", "Buckets m", [5, 7, 8, 11, 13].map((v) => [v, v]), dsa.hashM)}</div>
      <div class="sec-actions">${dsaButton("hash-put", `put("${nextKey}")`, { primary: true, iconName: "chevron" })}${dsaButton("hash-put4", "put next 4")}${dsaButton("hash-del", "delete oldest")}${dsaButton("hash-resize", dsa.hashResize ? "Auto-resize: on" : "Auto-resize: off")}${dsaButton("hash-reset", "Reset", { iconName: "reset" })}</div>
      <div class="dsa-canvas">${dsaHashSvg(H)}</div>
      ${dsaPills([[`n = ${H.size}`], [`m = ${H.m}`], [`α = ${alpha.toFixed(2)}`, alpha > (chain ? 1 : 0.7) ? "bad" : ""], [`average probes ${st.avg.toFixed(2)}`], [`worst ${st.worst}`], ...theory.map((t) => [t]), ...(chain ? [] : [[`tombstones ${st.tombs}`]]), [`resizes ${H.resizes}`]])}
      ${dsaLog(H.log)}
      <p class="sec-note">${icon("hashgrid", 14)}<span class="dsa-t">Hash h = Σ cᵢ·31^(len−1−i) mod 2³² (Java's <code>String.hashCode</code>), so the buckets are reproducible. Python randomises <code>hash(str)</code> per process (PYTHONHASHSEED) to stop attackers forcing collisions — experiment E18 shows what adversarial keys do to a fixed hash. Turn auto-resize off and keep inserting with probing: clusters grow and probe counts explode as α → 1.</span></p>`)}
    ${secSection("ATLAS GO", "Dictionaries in the app", secTable(["Code", "Key → value", "Operations"], [
      ["<code>domain.DISHES</code>", "dish id → Dish", "built once with a dict comprehension; O(1) lookup by id"],
      ["<code>Cart.items</code>", "dish id → quantity", "<code>add</code>, <code>remove</code>, <code>count</code>, <code>subtotal</code>"],
      ["<code>Catalog.dishes</code>", "dish id → Dish (built-in + seller dishes)", "<code>menu</code> filters per kitchen"],
      ["<code>LocalStore.failures</code>", "email → [failed count, locked until]", "login lockout, see the Security tab"],
      ["<code>TileLoader.failed</code>, <code>pending</code>", "tile key → retry time; set of keys", "dict and set: both hash tables"],
    ]))}
    ${secSection("CPYTHON", "What Python's dict actually does", `<p class="sec-text">CPython's <code>dict</code> uses <strong>open addressing</strong> with a perturbed probe sequence (not linear), keeps a separate dense array of entries so iteration follows insertion order, resizes when two-thirds full, and marks deletions with dummy entries — the tombstones above. The chaining table in <code>dsa_lab/experiments.py</code> (<code>ChainHash</code>) and the probing table (<code>OpenAddressHash</code>) are teaching versions of both designs.</p>`)}`;
}

// ================================================================== trees, heaps, tries
class DsaTNode { constructor(k) { this.k = k; this.l = this.r = null; this.h = 1; } }
const dsaH = (n) => (n ? n.h : 0);
const dsaUpd = (n) => { n.h = 1 + Math.max(dsaH(n.l), dsaH(n.r)); return n; };
function dsaBstInsert(n, k) { if (!n) return new DsaTNode(k); if (k < n.k) n.l = dsaBstInsert(n.l, k); else if (k > n.k) n.r = dsaBstInsert(n.r, k); return dsaUpd(n); }
function dsaRotR(y, log, tag) { const x = y.l; y.l = x.r; x.r = y; dsaUpd(y); dsaUpd(x); if (log) log.push(tag); return x; }
function dsaRotL(x, log, tag) { const y = x.r; x.r = y.l; y.l = x; dsaUpd(x); dsaUpd(y); if (log) log.push(tag); return y; }
function dsaRebalance(n, log) {
  dsaUpd(n); const b = dsaH(n.l) - dsaH(n.r);
  if (b > 1) { if (dsaH(n.l.l) >= dsaH(n.l.r)) return dsaRotR(n, log, `LL at ${n.k}: rotate right`); n.l = dsaRotL(n.l, null); return dsaRotR(n, log, `LR at ${n.k}: rotate left at ${n.l.k}, then right`); }
  if (b < -1) { if (dsaH(n.r.r) >= dsaH(n.r.l)) return dsaRotL(n, log, `RR at ${n.k}: rotate left`); n.r = dsaRotR(n.r, null); return dsaRotL(n, log, `RL at ${n.k}: rotate right at ${n.r.k}, then left`); }
  return n;
}
function dsaAvlInsert(n, k, log) { if (!n) return new DsaTNode(k); if (k < n.k) n.l = dsaAvlInsert(n.l, k, log); else if (k > n.k) n.r = dsaAvlInsert(n.r, k, log); else return n; return dsaRebalance(n, log); }
function dsaMin(n) { while (n.l) n = n.l; return n; }
function dsaDelete(n, k, avl, info, log) {
  if (!n) return null;
  if (k < n.k) n.l = dsaDelete(n.l, k, avl, info, log);
  else if (k > n.k) n.r = dsaDelete(n.r, k, avl, info, log);
  else {
    if (!n.l || !n.r) { if (info && !info.kind) info.kind = !n.l && !n.r ? "leaf: just remove it" : "one child: splice the child into its place"; n = n.l || n.r; }
    else { const s = dsaMin(n.r); if (info && !info.kind) info.kind = `two children: copy the in-order successor ${s.k} up, then delete ${s.k} from the right subtree`; n.k = s.k; n.r = dsaDelete(n.r, s.k, avl, null, log); }
  }
  if (!n) return null;
  return avl ? dsaRebalance(n, log) : dsaUpd(n);
}
const dsaTreeKeys = (n, out = []) => { if (n) { dsaTreeKeys(n.l, out); out.push(n.k); dsaTreeKeys(n.r, out); } return out; };
const dsaPre = (n, out = []) => { if (n) { out.push(n.k); dsaPre(n.l, out); dsaPre(n.r, out); } return out; };
const dsaPost = (n, out = []) => { if (n) { dsaPost(n.l, out); dsaPost(n.r, out); out.push(n.k); } return out; };
const dsaLevel = (n) => { const out = [], q = n ? [n] : []; for (let i = 0; i < q.length; i++) { out.push(q[i].k); if (q[i].l) q.push(q[i].l); if (q[i].r) q.push(q[i].r); } return out; };
const dsaCount = (n) => (n ? 1 + dsaCount(n.l) + dsaCount(n.r) : 0);
const dsaSearchSteps = (n, k) => { let s = 0; while (n) { s += 1; if (k === n.k) return s; n = k < n.k ? n.l : n.r; } return s; };

const DSA_TREE_INPUTS = {
  sorted: { label: "Sorted 1 → 15 (BST worst case)", keys: Array.from({ length: 15 }, (_, i) => i + 1) },
  random: { label: "Random order (seeded)", keys: (() => { const g = mlRng(7), a = Array.from({ length: 15 }, (_, i) => i + 1); for (let i = a.length - 1; i > 0; i--) { const j = g.int(i + 1); [a[i], a[j]] = [a[j], a[i]]; } return a; })() },
  zigzag: { label: "Zig-zag 1, 15, 2, 14, …", keys: [1, 15, 2, 14, 3, 13, 4, 12, 5, 11, 6, 10, 7, 9, 8] },
};
function dsaTreeNew() { dsa.tree = { bst: null, avl: null, i: 0, rot: [], last: null, del: null }; for (let i = 0; i < 7; i++) dsaTreeInsert(); }
function dsaTreeInsert() { const T = dsa.tree, keys = DSA_TREE_INPUTS[dsa.treeInput].keys; if (T.i >= keys.length) return; const k = keys[T.i++]; T.bst = dsaBstInsert(T.bst, k); T.avl = dsaAvlInsert(T.avl, k, T.rot); T.last = k; T.del = null; }

function dsaTreeSvg(root, title, hot) {
  const W = 300, keys = dsaTreeKeys(root), xOf = new Map(keys.map((k, i) => [k, keys.length > 1 ? 16 + (i / (keys.length - 1)) * (W - 32) : W / 2]));
  const h = dsaH(root), dy = h > 8 ? 22 : 30, H = Math.max(70, 26 + Math.max(h, 1) * dy);
  let edges = "", nodes = "";
  const walk = (n, d) => { if (!n) return; const x = xOf.get(n.k), y = 18 + d * dy; for (const c of [n.l, n.r]) if (c) edges += `<line class="dsa-tedge" x1="${x}" y1="${y}" x2="${xOf.get(c.k)}" y2="${18 + (d + 1) * dy}"/>`; nodes += `<g class="dsa-tnode${n.k === hot ? " hot" : ""}"><circle cx="${x}" cy="${y}" r="10"/>${dsaText(x, y + 3.5, n.k)}</g>`; walk(n.l, d + 1); walk(n.r, d + 1); };
  walk(root, 0);
  return dsaSvg(W, H, title, root ? edges + nodes : dsaText(W / 2, 40, "empty tree", "dsa-null"), "dsa-tree");
}

const DSA_DRIVERS = [["Ava", 2], ["Morgan", 3], ["Niamh", 6], ["Ciarán", 8], ["Dara", 1], ["Sam", 3], ["Rory", 4], ["Leah", 5], ["Eoin", 2], ["Aoife", 4], ["Tadhg", 6], ["Sinéad", 7], ["Conor", 1], ["Fiona", 5], ["Paddy", 7], ["Orla", 9]]; // intelligence.DRIVER_POOLS (name, eta)
function dsaHeapNew() { dsa.heap = { a: [], next: 0, log: [], swaps: [] }; for (let i = 0; i < 7; i++) dsaHeapPush(true); dsa.heap.log = []; dsa.heap.swaps = []; dsa.heap.hot = null; }
const dsaLess = (x, y) => x[1] < y[1] || (x[1] === y[1] && x[0] < y[0]);
function dsaHeapPush(quiet) {
  const Hp = dsa.heap; if (Hp.next >= DSA_DRIVERS.length) return; const item = DSA_DRIVERS[Hp.next++]; const a = Hp.a; a.push(item);
  let i = a.length - 1, swaps = []; while (i > 0) { const p = (i - 1) >> 1; if (!dsaLess(a[i], a[p])) break; [a[i], a[p]] = [a[p], a[i]]; swaps.push(`${a[p][0]}↑${p}`); i = p; }
  Hp.swaps = swaps; Hp.hot = item[0];
  if (!quiet) Hp.log.push({ op: `push(${item[0]}, ${item[1]} min)`, text: swaps.length ? `sift up: ${swaps.length} swap(s)` : "already in order — no swaps", cost: "O(log n)" });
}
function dsaHeapPop() {
  const Hp = dsa.heap, a = Hp.a; if (!a.length) return; const top = a[0], last = a.pop();
  let swaps = 0; if (a.length) { a[0] = last; let i = 0; for (;;) { const l = 2 * i + 1, r = l + 1; let m = i; if (l < a.length && dsaLess(a[l], a[m])) m = l; if (r < a.length && dsaLess(a[r], a[m])) m = r; if (m === i) break; [a[i], a[m]] = [a[m], a[i]]; swaps += 1; i = m; } }
  Hp.hot = null; Hp.log.push({ op: "pop()", text: `dispatch ${top[0]} (${top[1]} min); last element moved to the root and sifted down with ${swaps} swap(s)`, cost: "O(log n)" });
}
function dsaHeapSvg() {
  const a = dsa.heap.a, W = 600, levels = Math.max(1, Math.ceil(Math.log2(a.length + 1))), H = 22 + levels * 46 + 50;
  let body = "";
  const pos = (i) => { const d = Math.floor(Math.log2(i + 1)), k = i - (2 ** d - 1), slots = 2 ** d; return [((k + 0.5) / slots) * W, 22 + d * 46]; };
  a.forEach((_, i) => { if (i) { const [x1, y1] = pos((i - 1) >> 1), [x2, y2] = pos(i); body += `<line class="dsa-tedge" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}"/>`; } });
  a.forEach(([name, eta], i) => { const [x, y] = pos(i); body += `<g class="dsa-tnode wide${name === dsa.heap.hot ? " hot" : ""}"><rect x="${x - 34}" y="${y - 13}" width="68" height="26" rx="13"/>${dsaText(x, y - 1, name, "dsa-key")}${dsaText(x, y + 9, eta + " min", "dsa-idx")}</g>`; });
  const yA = 22 + levels * 46 + 10, cw = Math.min(46, (W - 20) / Math.max(a.length, 1));
  a.forEach(([name, eta], i) => { const x = 10 + i * cw; body += `<g class="dsa-bucket"><rect x="${x}" y="${yA}" width="${cw - 3}" height="22" rx="3"/>${dsaText(x + (cw - 3) / 2, yA + 14, eta, "dsa-val")}${dsaText(x + (cw - 3) / 2, yA + 34, i, "dsa-idx")}</g>`; });
  return dsaSvg(W, H + 8, "Min-heap of drivers by pickup minutes", body, "dsa-heap");
}

const DSA_TRIE_WORDS = ["Mardyke", "Western Road", "City Centre", "Douglas", "Oliver Plunkett St", "Grand Parade", "MacCurtain St", "South Mall", "Kent Station", "Lower Glanmire Rd", "Montenotte", "Blackpool", "Airport rank", "Ballygarvan", "Frankfield", "UCC Campus", "Cork Airport", "Cork City Centre"];
function dsaTrie(prefix) {
  const root = {}; let nodes = 1;
  for (const w of DSA_TRIE_WORDS) { let n = root; for (const c of w.toLowerCase()) { if (!n[c]) { n[c] = {}; nodes += 1; } n = n[c]; } n.$ = w; }
  let n = root, steps = 0; for (const c of prefix.toLowerCase()) { steps += 1; n = n[c]; if (!n) break; }
  const out = []; const collect = (m) => { if (!m) return; if (m.$) out.push(m.$); for (const k of Object.keys(m).sort()) if (k !== "$") collect(m[k]); }; collect(n);
  return { nodes, steps, matches: out, chars: DSA_TRIE_WORDS.reduce((s, w) => s + w.length, 0) };
}

function dsaTrees() {
  if (!dsa.tree) dsaTreeNew();
  if (!dsa.heap) dsaHeapNew();
  const T = dsa.tree, keys = DSA_TREE_INPUTS[dsa.treeInput].keys, present = dsaTreeKeys(T.bst), n = present.length;
  const worstB = Math.max(0, ...present.map((k) => dsaSearchSteps(T.bst, k))), worstA = Math.max(0, ...present.map((k) => dsaSearchSteps(T.avl, k)));
  const prefix = dsa.triePrefix ?? "Cork", trie = dsaTrie(prefix);
  return `<div class="sec-intro"><p>A <strong>binary search tree</strong> keeps smaller keys left and larger keys right, so a search follows one path from the root: its cost is the tree's <strong>height</strong>. Insert keys in sorted order and a plain BST degenerates into a linked list; an <strong>AVL tree</strong> repairs itself with rotations to keep the height ≤ 1.44 log₂ n (${dsaLessons(12, 13, 14)}). A <strong>heap</strong> answers a different question — "what is the minimum?" — in O(1), with O(log n) updates (${dsaLesson(15)}).</p></div>
    ${secSection("LIVE", "Insert the same keys into a BST and an AVL tree", `<div class="sec-row">${dsaSelect("tinput", "Insertion order", Object.entries(DSA_TREE_INPUTS).map(([id, x]) => [id, x.label]), dsa.treeInput)}${present.length ? dsaSelect("tdel", "Delete key", present.map((k) => [k, k]), T.delKey ?? present[0]) : ""}</div>
      <div class="sec-actions">${dsaButton("tree-insert", T.i < keys.length ? `insert(${keys[T.i]})` : "all inserted", { primary: true, iconName: "chevron", disabled: T.i >= keys.length })}${dsaButton("tree-all", "Insert all", { disabled: T.i >= keys.length })}${present.length ? dsaButton("tree-delete", "Delete") : ""}${dsaButton("tree-reset", "Reset", { iconName: "reset" })}</div>
      <div class="dsa-two even"><div><p class="sec-label">Plain BST — height ${dsaH(T.bst)}</p><div class="dsa-canvas">${dsaTreeSvg(T.bst, "Binary search tree", T.last)}</div></div><div><p class="sec-label">AVL tree — height ${dsaH(T.avl)}</p><div class="dsa-canvas">${dsaTreeSvg(T.avl, "AVL tree", T.last)}</div></div></div>
      ${dsaPills([[`n = ${n}`], [`⌈log₂(n+1)⌉ = ${n ? Math.ceil(Math.log2(n + 1)) : 0}`], [`worst search: BST ${worstB} vs AVL ${worstA} comparisons`, worstB > worstA ? "bad" : "good"], [`AVL rotations ${T.rot.length}`]])}
      ${T.del ? `<p class="sec-note">${icon("tree", 14)}<span class="dsa-t">Deleted ${T.del.key} — ${T.del.kind}.</span></p>` : ""}
      ${T.rot.length ? dsaLog(T.rot.map((r) => ({ op: "rotate", text: r }))) : ""}
      ${n ? secTable(["Traversal (BST)", "Order", "Uses"], [
        ["In-order (left, node, right)", `<code>${dsaTreeKeys(T.bst).join(" ")}</code>`, "always sorted — the BST property"],
        ["Pre-order (node, left, right)", `<code>${dsaPre(T.bst).join(" ")}</code>`, "copy or serialise the tree"],
        ["Post-order (left, right, node)", `<code>${dsaPost(T.bst).join(" ")}</code>`, "free children before parents; evaluate expressions"],
        ["Level order (queue)", `<code>${dsaLevel(T.bst).join(" ")}</code>`, "breadth-first; shortest number of edges"],
      ]) : ""}`)}
    ${secSection("HEAP", "A priority queue of the app's drivers, keyed by pickup minutes", `<div class="sec-actions">${dsaButton("heap-push", dsa.heap.next < DSA_DRIVERS.length ? `push(${DSA_DRIVERS[dsa.heap.next][0]}, ${DSA_DRIVERS[dsa.heap.next][1]})` : "no more drivers", { primary: true, iconName: "chevron", disabled: dsa.heap.next >= DSA_DRIVERS.length })}${dsaButton("heap-pop", "pop() — dispatch the nearest", { disabled: !dsa.heap.a.length })}${dsaButton("heap-reset", "Reset", { iconName: "reset" })}</div>
      <div class="dsa-canvas">${dsaHeapSvg()}</div>
      ${dsaPills([[`size ${dsa.heap.a.length}`], [`root = minimum: ${dsa.heap.a[0] ? `${dsa.heap.a[0][0]}, ${dsa.heap.a[0][1]} min` : "—"}`, "good"], ["parent(i) = (i − 1) // 2 · children 2i + 1, 2i + 2"]])}
      ${dsaLog(dsa.heap.log)}
      <p class="sec-note">${icon("car", 14)}<span class="dsa-t">The app does not use a heap: <code>intelligence.choose</code> ranks four to six candidates with <code>sorted</code> and takes the first, and the nearest-driver comparison uses <code>min</code>. With k candidates that is Θ(k log k) and Θ(k); a heap pays off when drivers arrive and leave continuously and you need the best one many times — a city-wide dispatcher.</span></p>`)}
    ${secSection("TRIE", "Prefix search over the app's place and zone names", `<div class="sec-row">${dsaSelect("trie", "Prefix", ["C", "Co", "Cork", "M", "Ma", "B", "K", "S", "Do", "Z"].map((v) => [v, `"${v}"`]), prefix)}</div>
      ${dsaPills([[`${trie.matches.length} match(es)`, trie.matches.length ? "good" : "bad"], [`${prefix.length} node step(s) to reach the prefix`], [`trie nodes ${trie.nodes} for ${DSA_TRIE_WORDS.length} names (${trie.chars} characters)`]])}
      <p class="sec-text">${trie.matches.length ? trie.matches.map((m) => `<code>${secEsc(m)}</code>`).join(" ") : "No name starts with this prefix."}</p>
      <p class="sec-note">${icon("search", 14)}<span class="dsa-t">Finding the prefix costs one step per character, independent of how many names are stored; scanning a list (what a <code>[p for p in PLACES if p.startswith(q)]</code> comprehension does) checks every name. Shared prefixes ("Cork …", "C…") are stored once.</span></p>`)}`;
}

// ================================================================== graphs (the app's Cork zones)
const DSA_ZONES = [["Mardyke", 51.8978, -8.4880], ["Western Road", 51.8946, -8.4895], ["City Centre", 51.8986, -8.4730], ["Douglas", 51.8770, -8.4360], ["Oliver Plunkett St", 51.8976, -8.4702], ["Grand Parade", 51.8970, -8.4760], ["MacCurtain St", 51.9020, -8.4700], ["South Mall", 51.8968, -8.4690], ["Kent Station", 51.9017, -8.4582], ["Lower Glanmire Rd", 51.9030, -8.4520], ["Montenotte", 51.9065, -8.4520], ["Blackpool", 51.9150, -8.4730], ["Airport rank", 51.8470, -8.4910], ["Ballygarvan", 51.8300, -8.4630], ["Frankfield", 51.8640, -8.4560], ["UCC Campus", 51.8935, -8.4921]]; // geo.ZONE_COORDS + PLACE_COORDS[0]
function dsaHaversine(a, b) { const R = 6371.0088, t = Math.PI / 180, dl = (b[1] - a[1]) * t, dp = (b[2] - a[2]) * t, h = Math.sin(dl / 2) ** 2 + Math.cos(a[1] * t) * Math.cos(b[1] * t) * Math.sin(dp / 2) ** 2; return 2 * R * Math.asin(Math.min(1, Math.sqrt(h))); }
const DSA_GRAPH = (() => { // undirected: every zone to its 3 nearest zones, weight = Haversine km
  const n = DSA_ZONES.length, adj = Array.from({ length: n }, () => new Map());
  for (let i = 0; i < n; i++) DSA_ZONES.map((z, j) => [j, dsaHaversine(DSA_ZONES[i], z)]).filter(([j]) => j !== i).sort((a, b) => a[1] - b[1]).slice(0, 3).forEach(([j, d]) => { const w = Math.round(d * 100) / 100; adj[i].set(j, w); adj[j].set(i, w); });
  const edges = []; adj.forEach((m, i) => m.forEach((w, j) => { if (i < j) edges.push([i, j, w]); }));
  return { n, adj: adj.map((m) => [...m.entries()].sort((a, b) => a[0] - b[0])), edges };
})();

function dsaGraphFrames(algo, src, dst) {
  const G = DSA_GRAPH, frames = [], name = (i) => DSA_ZONES[i][0];
  if (algo === "bfs" || algo === "dfs") { // BFS marks on enqueue; iterative DFS marks on pop (parent = last pusher)
    const seen = new Set([src]), order = [], tree = [], parent = new Map(), box = [src];
    frames.push({ order: [], tree: [], frontier: [...box], cur: null, msg: `${algo === "bfs" ? "queue" : "stack"} = [${name(src)}]` });
    while (box.length) {
      const u = algo === "bfs" ? box.shift() : box.pop();
      if (order.includes(u)) { frames.push({ order: [...order], tree: [...tree], frontier: [...box], cur: u, msg: `pop ${name(u)} — already visited, skip` }); continue; }
      order.push(u);
      if (parent.has(u)) tree.push([parent.get(u), u]);
      const added = [];
      const nbrs = algo === "dfs" ? [...G.adj[u]].reverse() : G.adj[u];
      for (const [v] of nbrs) {
        if (algo === "bfs" ? seen.has(v) : order.includes(v)) continue;
        seen.add(v); parent.set(v, u); box.push(v); added.push(name(v));
      }
      frames.push({ order: [...order], tree: [...tree], frontier: [...box], cur: u, msg: `visit ${name(u)}; ${added.length ? `${algo === "bfs" ? "enqueue" : "push"} ${added.join(", ")}` : "nothing new"}` });
    }
  } else if (algo === "dijkstra") {
    const dist = Array(G.n).fill(Infinity), prev = Array(G.n).fill(-1), done = new Set(); dist[src] = 0;
    let pq = [[0, src]], relax = 0;
    frames.push({ dist: [...dist], done: new Set(), prev: [...prev], cur: null, frontier: [src], msg: `dist[${name(src)}] = 0; priority queue = [(0, ${name(src)})]`, relax });
    while (pq.length) {
      pq.sort((a, b) => a[0] - b[0]); const [d, u] = pq.shift(); if (done.has(u)) continue; done.add(u);
      const upd = [];
      for (const [v, w] of G.adj[u]) { relax += 1; if (d + w < dist[v] - 1e-9) { dist[v] = d + w; prev[v] = u; pq.push([dist[v], v]); upd.push(`${name(v)} → ${dist[v].toFixed(2)}`); } }
      frames.push({ dist: [...dist], done: new Set(done), prev: [...prev], cur: u, frontier: pq.filter(([, v]) => !done.has(v)).map(([, v]) => v), msg: `settle ${name(u)} at ${d.toFixed(2)} km; ${upd.length ? "relax " + upd.join(", ") : "no improvement"}`, relax });
      if (u === dst) { frames[frames.length - 1].msg += ` — target reached, stop.`; break; }
    }
  } else { // Prim's minimum spanning tree from src
    const inT = new Set([src]), tree = []; let total = 0;
    frames.push({ inT: new Set(inT), tree: [], cur: src, msg: `start the tree at ${name(src)}`, total });
    while (inT.size < G.n) {
      let best = null; for (const u of inT) for (const [v, w] of G.adj[u]) if (!inT.has(v) && (!best || w < best[2])) best = [u, v, w];
      if (!best) break; inT.add(best[1]); tree.push(best); total += best[2];
      frames.push({ inT: new Set(inT), tree: [...tree], cur: best[1], msg: `cheapest edge leaving the tree: ${name(best[0])} – ${name(best[1])} (${best[2].toFixed(2)} km)`, total });
    }
  }
  return frames;
}

function dsaGraphNew() { dsa.graph = { frames: dsaGraphFrames(dsa.graphAlgo, dsa.graphSrc, dsa.graphDst), i: 0 }; }

// Schematic positions (north up, roughly geographic) so the dense city-centre zones stay readable.
const DSA_LAYOUT = { "Blackpool": [320, 30, "r"], "MacCurtain St": [300, 105, "l"], "Montenotte": [440, 62, "r"], "Kent Station": [420, 140, "b"], "Lower Glanmire Rd": [545, 118, "t"], "City Centre": [215, 150, "t"], "Oliver Plunkett St": [300, 185, "r"], "Grand Parade": [200, 218, "l"], "South Mall": [320, 252, "r"], "Mardyke": [130, 128, "t"], "Western Road": [58, 190, "b"], "UCC Campus": [125, 252, "b"], "Douglas": [525, 292, "r"], "Frankfield": [405, 318, "r"], "Airport rank": [235, 352, "l"], "Ballygarvan": [365, 388, "r"] };
function dsaGraphSvg(F) {
  const W = 630, H = 412, P = (i) => DSA_LAYOUT[DSA_ZONES[i][0]];
  const treeSet = new Set((F.tree || []).map(([u, v]) => `${Math.min(u, v)}-${Math.max(u, v)}`));
  let path = new Set();
  if (dsa.graphAlgo === "dijkstra" && F.prev) { let v = dsa.graphDst; while (v !== -1 && F.prev[v] !== -1) { path.add(`${Math.min(v, F.prev[v])}-${Math.max(v, F.prev[v])}`); v = F.prev[v]; } if (!F.done.has(dsa.graphDst)) path = new Set(); }
  const sptSet = new Set(); if (F.prev) F.prev.forEach((p, v) => { if (p >= 0) sptSet.add(`${Math.min(p, v)}-${Math.max(p, v)}`); });
  let body = "";
  for (const [u, v, w] of DSA_GRAPH.edges) {
    const key = `${u}-${v}`, [xa, ya] = P(u), [xb, yb] = P(v), cls = path.has(key) ? "path" : treeSet.has(key) || sptSet.has(key) ? "tree" : "";
    body += `<line class="dsa-gedge ${cls}" x1="${xa}" y1="${ya}" x2="${xb}" y2="${yb}"/>`;
    if (dsa.graphShowW) body += dsaText((xa + xb) / 2, (ya + yb) / 2 - 3, w.toFixed(2), "dsa-w");
  }
  DSA_ZONES.forEach((z, i) => {
    const [x, y, side] = P(i), visited = F.order ? F.order.includes(i) : F.done ? F.done.has(i) : F.inT.has(i), front = (F.frontier || []).includes(i);
    const cls = [visited ? "done" : "", front && !visited ? "front" : "", i === F.cur ? "cur" : "", i === dsa.graphSrc ? "src" : "", dsa.graphAlgo === "dijkstra" && i === dsa.graphDst ? "dst" : ""].join(" ");
    const lbl = F.dist ? (isFinite(F.dist[i]) ? F.dist[i].toFixed(2) : "") : F.order && F.order.includes(i) ? "#" + (F.order.indexOf(i) + 1) : "";
    const nameAt = { r: [x + 11, y + 3.5, "start"], l: [x - 11, y + 3.5, "end"], t: [x, y - 12, "middle"], b: [x, y + 19, "middle"] }[side];
    const lblAt = side === "t" ? [x, y + 19] : side === "b" ? [x, y - 11] : [x, y - 11];
    body += `<g class="dsa-gnode ${cls}"><circle cx="${x}" cy="${y}" r="7"/>${dsaText(nameAt[0], nameAt[1], z[0], "dsa-gname", nameAt[2])}${lbl ? dsaText(lblAt[0], lblAt[1], lbl, "dsa-glabel") : ""}</g>`;
  });
  return dsaSvg(W, H, "Graph of the app's Cork zones", body, "dsa-graph");
}

function dsaGraphs() {
  if (!dsa.graph) dsaGraphNew();
  const Gs = dsa.graph, F = Gs.frames[Gs.i], last = Gs.i === Gs.frames.length - 1, name = (i) => DSA_ZONES[i][0], algo = dsa.graphAlgo;
  const zoneOpts = DSA_ZONES.map((z, i) => [i, z[0]]);
  let table = "";
  if (algo === "dijkstra") {
    const path = []; if (F.done.has(dsa.graphDst)) { let v = dsa.graphDst; while (v !== -1) { path.unshift(name(v)); v = F.prev[v]; } }
    table = dsaPills([[`relaxations ${F.relax}`], [`settled ${F.done.size} / ${DSA_GRAPH.n}`], path.length ? [`shortest: ${path.join(" → ")} = ${F.dist[dsa.graphDst].toFixed(2)} km`, "good"] : ["target not settled yet"], [`straight line ${dsaHaversine(DSA_ZONES[dsa.graphSrc], DSA_ZONES[dsa.graphDst]).toFixed(2)} km`]]);
  } else if (algo === "prim") table = dsaPills([[`edges in tree ${F.tree.length} / ${DSA_GRAPH.n - 1}`], [`total ${F.total.toFixed(2)} km`, last ? "good" : ""]]);
  else table = dsaPills([[`visit order ${F.order.map(name).join(" → ") || "—"}`], [`${algo === "bfs" ? "queue" : "stack"} [${F.frontier.map(name).join(", ")}]`]]);
  return `<div class="sec-intro"><p>A <strong>graph</strong> is vertices joined by edges; most "find the best way" problems are graph searches (${dsaLessons(17, 18)}). The vertices here are the sixteen Cork zones the app knows (<code>geo.ZONE_COORDS</code> and UCC from <code>PLACE_COORDS</code>); each zone is joined to its three nearest zones and the weight is the app's own great-circle distance (<code>geo.haversine_km</code>). The drawing is schematic: north is up, but the crowded city centre is spread out. ATLAS itself has no road graph — it estimates trips along straight lines — so this graph is a teaching extension built from its data.</p></div>
    ${secSection("LIVE", "Step through a graph algorithm", `<div class="sec-row">${dsaSelect("galgo", "Algorithm", [["bfs", "Breadth-first search (queue)"], ["dfs", "Depth-first search (stack)"], ["dijkstra", "Dijkstra shortest path"], ["prim", "Prim minimum spanning tree"]], algo)}${dsaSelect("gsrc", "From", zoneOpts, dsa.graphSrc)}${algo === "dijkstra" ? dsaSelect("gdst", "To", zoneOpts, dsa.graphDst) : ""}</div>
      <div class="sec-actions">${dsaButton("graph-prev", "Back", { iconName: "previous", disabled: Gs.i === 0 })}${dsaButton("graph-next", "Step", { primary: true, iconName: "chevron", disabled: last })}${dsaButton("graph-end", "Run to the end", { disabled: last })}${dsaButton("graph-restart", "Restart", { iconName: "reset" })}${dsaButton("graph-w", dsa.graphShowW ? "Hide weights" : "Show weights")}</div>
      <div class="dsa-canvas">${dsaGraphSvg(F)}</div>
      <p class="sec-label">Step ${Gs.i} of ${Gs.frames.length - 1}: ${secEsc(F.msg)}</p>
      ${table}
      <p class="sec-note">${icon("graph", 14)}<span class="dsa-t">${algo === "bfs" ? "BFS visits vertices in order of their number of edges from the start, so its tree gives the fewest-hops route — not the shortest in km." : algo === "dfs" ? "DFS dives as deep as it can before backtracking; its tree is long and thin. It is the basis of cycle detection and topological sorting." : algo === "dijkstra" ? "Dijkstra settles vertices in increasing distance; once settled, a distance is final because no weight is negative. Labels show the current best distance in km; unlabelled zones are still at ∞." : "Prim grows one tree by always adding the cheapest edge that leaves it: the result connects all sixteen zones with the least total length."}</span></p>`)}
    ${secSection("REPRESENTATION", "Adjacency list of this graph", secTable(["Zone", "Neighbours (km)"], DSA_GRAPH.adj.map((nb, i) => [name(i), nb.map(([v, w]) => `${name(v)} ${w.toFixed(2)}`).join(" · ")])))}
    ${secSection("COSTS", "Which algorithm, and what it costs", secTable(["Algorithm", "Data structure", "Time", "Answers"], [
      ["BFS", "queue", "O(V + E)", "reachability, fewest edges"], ["DFS", "stack / recursion", "O(V + E)", "reachability, cycles, topological order"],
      ["Dijkstra", "binary heap", "O((V + E) log V)", "shortest weighted paths, weights ≥ 0"], ["Prim", "binary heap", "O(E log V)", "minimum spanning tree"],
      ["Kruskal", "sort + union-find", "O(E log E)", "minimum spanning tree (experiment E27 compares union-find variants)"],
    ]))}`;
}

// ================================================================== sorting & searching
// Counting sorts: every comparison goes through cmp(), every array write through put(). trace() records frames.
function dsaSortRun(algo, input, trace = null) {
  const a = [...input], key = (v) => (Array.isArray(v) ? v[1] : v);
  let cmp = 0, writes = 0;
  const lt = (x, y, i, j) => { cmp += 1; if (trace) trace.push({ a: [...a], hi: [i, j], msg: `compare ${key(x)} < ${key(y)}` }); return key(x) < key(y); };
  const swap = (i, j) => { [a[i], a[j]] = [a[j], a[i]]; writes += 2; if (trace) trace.push({ a: [...a], hi: [i, j], swap: true, msg: `swap positions ${i} and ${j}` }); };
  const put = (i, v) => { a[i] = v; writes += 1; if (trace) trace.push({ a: [...a], hi: [i], swap: true, msg: `write ${key(v)} at ${i}` }); };
  const n = a.length;
  if (algo === "insertion") for (let i = 1; i < n; i++) { const x = a[i]; let j = i - 1; while (j >= 0 && lt(x, a[j], i, j)) { put(j + 1, a[j]); j -= 1; } put(j + 1, x); }
  else if (algo === "selection") for (let i = 0; i < n - 1; i++) { let m = i; for (let j = i + 1; j < n; j++) if (lt(a[j], a[m], j, m)) m = j; if (m !== i) swap(i, m); }
  else if (algo === "bubble") for (let end = n - 1; end > 0; end--) { let swapped = false; for (let j = 0; j < end; j++) if (lt(a[j + 1], a[j], j + 1, j)) { swap(j, j + 1); swapped = true; } if (!swapped) break; }
  else if (algo === "merge") { const go = (lo, hi) => { if (hi - lo < 2) return; const mid = (lo + hi) >> 1; go(lo, mid); go(mid, hi); const L = a.slice(lo, mid), R = a.slice(mid, hi); let i = 0, j = 0, k = lo; while (i < L.length && j < R.length) put(k++, lt(R[j], L[i], mid + j, lo + i) ? R[j++] : L[i++]); while (i < L.length) put(k++, L[i++]); while (j < R.length) put(k++, R[j++]); }; go(0, n); }
  else if (algo === "quick") { const g = mlRng(2026), stack = [[0, n - 1]]; while (stack.length) { const [lo, hi] = stack.pop(); if (lo >= hi) continue; const p = lo + g.int(hi - lo + 1); if (p !== hi) swap(p, hi); let store = lo; for (let i = lo; i < hi; i++) if (lt(a[i], a[hi], i, hi)) { if (i !== store) swap(i, store); store += 1; } if (store !== hi) swap(store, hi); stack.push([lo, store - 1], [store + 1, hi]); } }
  else if (algo === "heap") { const sift = (s, end) => { let r = s; for (;;) { let c = 2 * r + 1; if (c > end) break; if (c + 1 <= end && lt(a[c], a[c + 1], c, c + 1)) c += 1; if (lt(a[r], a[c], r, c)) { swap(r, c); r = c; } else break; } }; for (let s = (n >> 1) - 1; s >= 0; s--) sift(s, n - 1); for (let end = n - 1; end > 0; end--) { swap(0, end); sift(0, end - 1); } }
  else if (algo === "builtin") { const out = a.slice().sort((x, y) => { cmp += 1; return key(x) - key(y); }); out.forEach((v, i) => { a[i] = v; }); writes = NaN; }
  return { a, cmp, writes };
}
const dsaSortCount = (algo, data) => dsaSortRun(algo, data);

const DSA_SORTS = [["insertion", "Insertion sort", "O(n²) · O(n) if sorted", "yes"], ["selection", "Selection sort", "O(n²) always", "no"], ["bubble", "Bubble sort (early exit)", "O(n²) · O(n) if sorted", "yes"], ["merge", "Merge sort", "O(n log n)", "yes"], ["quick", "Quick sort (random pivot)", "O(n log n) expected", "no"], ["heap", "Heap sort", "O(n log n)", "no"], ["builtin", "Built-in sort (Timsort)", "O(n log n) · O(n) on runs", "yes"]];
function dsaSortInput(n, order) {
  const g = mlRng(n * 7 + order.length);
  const base = order === "few" ? Array.from({ length: n }, () => g.int(4)) : Array.from({ length: n }, () => g.int(n * 4));
  if (order === "sorted") return base.sort((x, y) => x - y);
  if (order === "reversed") return base.sort((x, y) => y - x);
  if (order === "nearly") { base.sort((x, y) => x - y); for (let i = 0; i < Math.max(1, n / 20); i++) { const p = g.int(n), q = g.int(n); [base[p], base[q]] = [base[q], base[p]]; } }
  return base;
}

function dsaTraceNew() {
  const g = mlRng(dsa.traceSeed || 11), data = Array.from({ length: 10 }, () => 1 + g.int(20));
  const frames = [{ a: [...data], hi: [], msg: "start" }];
  const r = dsaSortRun(dsa.traceAlgo, data, frames);
  frames.push({ a: r.a, hi: [], msg: `done: ${r.cmp} comparisons, ${r.writes} writes`, done: true });
  dsa.trace = { frames, i: 0 };
}
function dsaBars(F) {
  const W = 600, H = 150, n = F.a.length, w = W / n, mx = 21;
  return dsaSvg(W, H, "Array being sorted", F.a.map((v, i) => { const h = (v / mx) * (H - 28), hot = F.hi.includes(i); return `<g class="dsa-bar${hot ? (F.swap ? " swap" : " cmp") : ""}${F.done ? " done" : ""}"><rect x="${i * w + 4}" y="${H - 18 - h}" width="${w - 8}" height="${h}" rx="3"/>${dsaText(i * w + w / 2, H - 5, v, "dsa-idx")}</g>`; }).join(""), "dsa-bars");
}

function dsaStability(algo) {
  const r = dsaSortRun(algo, DSA_DRIVERS), pos = new Map(DSA_DRIVERS.map((d, i) => [d[0], i]));
  let bad = 0; for (let i = 0; i < r.a.length; i++) for (let j = i + 1; j < r.a.length; j++) if (r.a[i][1] === r.a[j][1] && pos.get(r.a[i][0]) > pos.get(r.a[j][0])) bad += 1;
  return { order: r.a, bad };
}

function dsaBinarySearch(a, x) { // first_occurrence: leftmost index with a[i] >= x
  let lo = 0, hi = a.length; const steps = [];
  while (lo < hi) { const mid = (lo + hi) >> 1; steps.push([lo, hi, mid, a[mid]]); if (a[mid] < x) lo = mid + 1; else hi = mid; }
  return { at: lo < a.length && a[lo] === x ? lo : -1, steps, lo };
}

function dsaSorting() {
  if (!dsa.trace) dsaTraceNew();
  const data = dsaSortInput(dsa.sortN, dsa.sortOrder), results = DSA_SORTS.map(([id, label, big, stable]) => ({ id, label, big, stable, ...dsaSortRun(id, data) }));
  const T = dsa.trace, F = T.frames[T.i], etas = DSA_DRIVERS.map((d) => d[1]).sort((x, y) => x - y), bs = dsaBinarySearch(etas, dsa.searchTarget);
  const maxC = Math.max(...results.map((r) => r.cmp));
  return `<div class="sec-intro"><p>Sorting is the most studied problem in computing because so much else depends on it: binary search, duplicate detection, ranking. Comparison sorts cannot beat <strong>Θ(n log n)</strong> comparisons in the worst case, but the input's order, the cost of writes and <strong>stability</strong> decide which one to use (${dsaLessons(19, 20)}). ATLAS Go ranks dispatch candidates with Python's built-in <code>sorted</code> (<code>intelligence.rank</code>).</p></div>
    ${secSection("RACE", "Seven sorts on the same input", `<div class="sec-row">${dsaSelect("sn", "n", [16, 64, 128, 512, 2048].map((v) => [v, v]), dsa.sortN)}${dsaSelect("sorder", "Input order", [["random", "Random"], ["sorted", "Already sorted"], ["nearly", "Nearly sorted (5 % swapped)"], ["reversed", "Reversed"], ["few", "Only 4 distinct values"]], dsa.sortOrder)}</div>
      <div class="dsa-hbars">${results.map((r) => `<div class="dsa-hbar"><span>${r.label}</span><i style="width:${Math.max(0.6, (100 * r.cmp) / maxC).toFixed(1)}%"></i><b>${r.cmp.toLocaleString()}</b></div>`).join("")}</div>
      <p class="sec-text"><small>Bar length is proportional to the exact comparison count.</small></p>
      ${secTable(["Algorithm", "Comparisons", "Writes", "Bound", "Stable", "n log₂ n"], results.map((r) => [r.label, r.cmp.toLocaleString(), isNaN(r.writes) ? "—" : r.writes.toLocaleString(), r.big, r.stable, Math.round(dsa.sortN * Math.log2(dsa.sortN)).toLocaleString()]), "ml-table")}
      <p class="sec-note">${icon("sortbars", 14)}<span class="dsa-t">Try <b>Already sorted</b>: insertion sort and Timsort drop to n − 1 comparisons while selection sort still does n(n−1)/2. Try <b>Only 4 distinct values</b> and <b>Reversed</b> for quick sort and bubble sort. Selection sort makes the fewest writes — it matters when writing is expensive (flash memory).</span></p>`)}
    ${secSection("TRACE", "Watch one algorithm, one operation at a time", `<div class="sec-row">${dsaSelect("talgo", "Algorithm", DSA_SORTS.filter((s) => s[0] !== "builtin").map(([id, l]) => [id, l]), dsa.traceAlgo)}</div>
      <div class="sec-actions">${dsaButton("trace-prev", "Back", { iconName: "previous", disabled: T.i === 0 })}${dsaButton("trace-next", "Step", { primary: true, iconName: "chevron", disabled: T.i === T.frames.length - 1 })}${dsaButton("trace-10", "+10", { disabled: T.i === T.frames.length - 1 })}${dsaButton("trace-end", "Finish", { disabled: T.i === T.frames.length - 1 })}${dsaButton("trace-new", "New data", { iconName: "reset" })}</div>
      <div class="dsa-canvas">${dsaBars(F)}</div>
      <p class="sec-label">Operation ${T.i} of ${T.frames.length - 1}: ${secEsc(F.msg)}</p>
      ${mlLegend([["cmp", "compared"], ["swap", "written / swapped"]])}`)}
    ${secSection("STABILITY", "Sort the app's sixteen drivers by pickup minutes", `<p class="sec-text">Seven pairs of drivers share a pickup time. A <strong>stable</strong> sort keeps each pair in its original pool order (<code>intelligence.DRIVER_POOLS</code>); an unstable one may swap them — which matters when you sort by a second key first, or when ties must be broken fairly.</p>
      ${secTable(["Algorithm", "Order after sorting by minutes", "Equal-key pairs reversed"], ["merge", "insertion", "selection", "heap", "builtin"].map((id) => { const s = dsaStability(id); return [DSA_SORTS.find((x) => x[0] === id)[1], `<code>${s.order.map(([nm, e]) => `${nm} ${e}`).join(", ")}</code>`, s.bad ? `<span class="dsa-bad">${s.bad}</span>` : `<span class="sec-yes">0</span>`]; }))}
      <p class="sec-note">${icon("car", 14)}<span class="dsa-t">Python's <code>sorted</code> is guaranteed stable. <code>intelligence.rank</code> sorts by probability with <code>key=lambda x: -x[1]</code>, so two drivers with the same probability stay in pool order and dispatch is deterministic.</span></p>`)}
    ${secSection("SEARCH", "Binary search for the first driver with a given pickup time", `<div class="sec-row">${dsaSelect("starget", "Find minutes", Array.from({ length: 11 }, (_, i) => [i, i]), dsa.searchTarget)}</div>
      <div class="dsa-cells">${etas.map((v, i) => `<span class="${i === bs.lo && bs.at >= 0 ? "hit" : bs.steps.some((s) => s[2] === i) ? "probe" : ""}"><b>${v}</b><small>${i}</small></span>`).join("")}</div>
      ${secTable(["Step", "lo", "hi", "mid", "a[mid]", "Decision"], bs.steps.map(([lo, hi, mid, v], i) => [i + 1, lo, hi, mid, v, v < dsa.searchTarget ? `${v} < ${dsa.searchTarget} → lo = mid + 1` : `${v} ≥ ${dsa.searchTarget} → hi = mid`]))}
      ${dsaPills([[bs.at >= 0 ? `found at index ${bs.at} after ${bs.steps.length} comparisons` : `not present (would insert at ${bs.lo}) after ${bs.steps.length} comparisons`, bs.at >= 0 ? "good" : "bad"], [`linear scan: ${bs.at >= 0 ? bs.at + 1 : etas.length} comparisons`], [`⌈log₂(${etas.length + 1})⌉ = ${Math.ceil(Math.log2(etas.length + 1))}`]])}
      <p class="sec-note">${icon("search", 14)}<span class="dsa-t">This is <code>first_occurrence</code> from the lab (Python's <code>bisect_left</code>): it keeps going left after a match, so with duplicates it returns the first one.</span></p>`)}`;
}

// ================================================================== algorithm design
const DSA_ITEMS = [["Harvest bowl", 4, 1090], ["Falafel wrap", 2, 850], ["Fresh orange juice", 1, 390], ["Margherita pizza", 5, 1290], ["Garlic flatbread", 2, 490], ["Still water", 1, 200], ["Vegetable curry", 4, 1190], ["Masala dosa", 3, 990], ["Mango lassi", 1, 450]]; // domain.MENU prices; volumes invented
function dsaKnapsack(cap) {
  const n = DSA_ITEMS.length, T = Array.from({ length: n + 1 }, () => Array(cap + 1).fill(0));
  for (let i = 1; i <= n; i++) { const [, w, v] = DSA_ITEMS[i - 1]; for (let c = 0; c <= cap; c++) T[i][c] = Math.max(T[i - 1][c], w <= c ? T[i - 1][c - w] + v : 0); }
  const take = []; let c = cap; for (let i = n; i > 0; i--) if (T[i][c] !== T[i - 1][c]) { take.unshift(i - 1); c -= DSA_ITEMS[i - 1][1]; }
  const greedy = (keyFn) => { let left = cap, val = 0; const got = []; DSA_ITEMS.map((it, i) => [i, keyFn(it)]).sort((a, b) => b[1] - a[1]).forEach(([i]) => { if (DSA_ITEMS[i][1] <= left) { left -= DSA_ITEMS[i][1]; val += DSA_ITEMS[i][2]; got.push(i); } }); return { val, got }; };
  return { T, take, best: T[n][cap], byRatio: greedy((it) => it[2] / it[1]), byValue: greedy((it) => it[2]) };
}
function dsaFib(n) { let naive = 0; const f = (m) => { naive += 1; return m < 2 ? m : f(m - 1) + f(m - 2); }; let value; if (n <= 27) value = f(n); else { const F = [0, 1]; for (let i = 2; i <= n + 1; i++) F[i] = F[i - 1] + F[i - 2]; naive = 2 * F[n + 1] - 1; value = F[n]; } let memoCalls = 0; const memo = new Map(); const g = (m) => { memoCalls += 1; if (m < 2) return m; if (memo.has(m)) return memo.get(m); const v = g(m - 1) + g(m - 2); memo.set(m, v); return v; }; g(n); return { value, naive, memoCalls }; }
function dsaQueens(n) { let solutions = 0, nodes = 0, first = null; const col = new Set(), d1 = new Set(), d2 = new Set(), rows = []; const place = (r) => { if (r === n) { solutions += 1; if (!first) first = [...rows]; return; } for (let c = 0; c < n; c++) { nodes += 1; if (col.has(c) || d1.has(r - c) || d2.has(r + c)) continue; col.add(c); d1.add(r - c); d2.add(r + c); rows.push(c); place(r + 1); rows.pop(); col.delete(c); d1.delete(r - c); d2.delete(r + c); } }; place(0); return { solutions, nodes, first }; }

function dsaDesign() {
  const D = dsa.design, fib = dsaFib(D.fib), ks = dsaKnapsack(D.cap), q = dsaQueens(D.queens), money = (c) => `€${(c / 100).toFixed(2)}`;
  const fibRows = [5, 10, 15, 20, 25, 30, 40].map((n) => { const r = dsaFib(n); return [n, r.naive.toLocaleString(), r.memoCalls, r.value.toLocaleString()]; });
  return `<div class="sec-intro"><p>Four ways to design an algorithm (${dsaLessons(21, 22, 23)}): <strong>divide and conquer</strong> splits a problem into independent halves; <strong>dynamic programming</strong> stores answers to overlapping subproblems; a <strong>greedy</strong> algorithm commits to the locally best choice — fast, but only correct for some problems; <strong>backtracking</strong> builds a solution step by step and abandons a branch as soon as it cannot succeed.</p></div>
    ${secSection("MEMOISATION", "Fibonacci: the same recursion with and without a memo", `<div class="sec-row">${dsaRange("fib", "n", 2, 40, 1, D.fib)}</div>
      ${dsaPills([[`F(${D.fib}) = ${fib.value.toLocaleString()}`], [`naive calls ${fib.naive.toLocaleString()} = 2F(n+1) − 1`, "bad"], [`memoised calls ${fib.memoCalls} = 2n − 1`, "good"]])}
      ${secTable(["n", "Naive calls", "Memoised calls", "F(n)"], fibRows, "ml-table")}
      <p class="sec-note">${icon("puzzle", 14)}<span class="dsa-t">The naive recursion recomputes F(n − 2) inside both F(n − 1) and F(n): its call tree grows like φⁿ ≈ 1.618ⁿ. The memo turns it into a linear chain. Experiment E13 measures both.</span></p>`)}
    ${secSection("DYNAMIC PROGRAMMING", "0/1 knapsack: the most valuable order that fits a courier's bag", `<p class="sec-text">Items are the app's menu (<code>domain.MENU</code>, real prices); the bag volumes are invented for the exercise. T[i][c] = best value using the first i items with capacity c = max(T[i−1][c], T[i−1][c − wᵢ] + vᵢ).</p>
      <div class="sec-row">${dsaSelect("cap", "Bag capacity (volume units)", [4, 5, 6, 7, 8, 9, 10, 12].map((v) => [v, v]), D.cap)}</div>
      <div class="sec-table-wrap"><table class="sec-table dsa-dp"><thead><tr><th scope="col">Item (volume, price)</th>${Array.from({ length: D.cap + 1 }, (_, c) => `<th scope="col">${c}</th>`).join("")}</tr></thead><tbody>${ks.T.map((row, i) => `<tr${i && ks.take.includes(i - 1) ? ' class="take"' : ""}><th scope="row">${i ? `${DSA_ITEMS[i - 1][0]} (${DSA_ITEMS[i - 1][1]}, ${money(DSA_ITEMS[i - 1][2])})` : "—"}</th>${row.map((v) => `<td>${(v / 100).toFixed(2)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
      ${secTable(["Method", "Items", "Value"], [
        ["Dynamic programming (optimal)", ks.take.map((i) => DSA_ITEMS[i][0]).join(", "), `<span class="sec-yes">${money(ks.best)}</span>`],
        ["Greedy by price per volume", ks.byRatio.got.map((i) => DSA_ITEMS[i][0]).join(", "), ks.byRatio.val < ks.best ? `<span class="dsa-bad">${money(ks.byRatio.val)}</span>` : money(ks.byRatio.val)],
        ["Greedy by highest price", ks.byValue.got.map((i) => DSA_ITEMS[i][0]).join(", "), ks.byValue.val < ks.best ? `<span class="dsa-bad">${money(ks.byValue.val)}</span>` : money(ks.byValue.val)],
      ])}
      <p class="sec-note">${icon("bag", 14)}<span class="dsa-t">The table has (items + 1) × (capacity + 1) cells, each O(1): Θ(n·C) time. That is <em>pseudo-polynomial</em> — fine for small C. Change the capacity and look for one where a greedy rule loses.</span></p>`)}
    ${secSection("BACKTRACKING", "N queens: abandon a partial board as soon as two queens attack", `<div class="sec-row">${dsaSelect("queens", "Board size n", [4, 5, 6, 7, 8, 9, 10].map((v) => [v, v]), D.queens)}</div>
      <div class="dsa-two"><div class="dsa-board" style="--n:${D.queens}">${Array.from({ length: D.queens * D.queens }, (_, i) => { const r = Math.floor(i / D.queens), c = i % D.queens; return `<span class="${(r + c) % 2 ? "dark" : ""}">${q.first && q.first[r] === c ? "♛" : ""}</span>`; }).join("")}</div>
      <div>${secTable(["Quantity", "Value"], [["Solutions", q.solutions.toLocaleString()], ["Squares tried by backtracking", q.nodes.toLocaleString()], ["Boards a brute force would test (nⁿ)", (D.queens ** D.queens).toLocaleString()]])}</div></div>`)}
    ${secSection("CORRECTNESS", "Invariants the labs check after every operation", secTable(["Structure", "Invariant", "Checked by"], [
      ["Singly / doubly list", "walking next from head reaches tail in exactly size steps; p.next.prev is p", "<code>validate()</code> — shown live on the Linked lists tab"],
      ["Circular lists", "walking size steps from the head returns to it; the sentinel is never removed", "<code>validate()</code>"],
      ["BST / AVL", "in-order is sorted; |height(left) − height(right)| ≤ 1 (AVL)", "<code>is_bst</code>, <code>validate_avl</code>"],
      ["Heap", "parent ≤ children for every index", "<code>MinHeap.is_heap</code>"],
      ["Hash tables", "every key is reachable from its home bucket; size matches", "<code>ChainHash.validate</code>"],
      ["ATLAS Go state", "structurally valid saved state before any screen reads it", "<code>LocalStore.validate</code>, <code>intelligence.self_test</code>"],
    ]))}`;
}

// ================================================================== experiments & exercises
const DSA_EXPERIMENTS = [["E01", "growth", "n, n log n, n²", "complexity"], ["E02", "search", "linear vs binary comparisons", "sorting"], ["E03", "search_cases", "best / average / worst", "complexity"], ["E04", "sort", "bubble vs merge vs quick", "sorting"], ["E05", "sort_cases", "insertion sort and input order", "sorting"], ["E06", "runtime", "measured search and sort time", "complexity"], ["E07", "array_linked", "front insertion: list vs linked list", "lists"], ["E08", "stack_queue", "draining n items three ways", "queues"], ["E09", "hash", "dict vs scan vs bisect", "hashing"], ["E10", "bst", "balanced vs skewed BST", "trees"], ["E11", "graph", "BFS/DFS edge examinations", "graphs"], ["E12", "shortest_path", "Dijkstra relaxations and pushes", "graphs"], ["E13", "recursion_dp", "Fibonacci calls", "design"], ["E14", "memory", "traced KiB of list/dict/deque", "complexity"], ["E15", "sorting_stability", "equal-key order violations", "sorting"], ["E16", "hash_singly", "singly chained table", "hashing"], ["E17", "hash_doubly", "doubly chained table with deletes", "hashing"], ["E18", "hash_load", "uniform vs adversarial keys", "hashing"], ["E19", "tree_stack_queue", "iterative traversals", "trees"], ["E20", "avl", "AVL vs plain BST", "trees"], ["E21", "circular_singly", "Josephus problem on a circular list", "lists"], ["E22", "circular_doubly", "LRU cache on a circular doubly list", "queues"], ["E23", "ring_buffer", "ring buffer vs deque vs pop(0)", "queues"], ["E24", "heap", "heapify vs n pushes", "trees"], ["E25", "trie", "prefix query: trie vs scan", "trees"], ["E26", "bst_delete", "height after deletions, BST vs AVL", "trees"], ["E27", "union_find", "naive vs rank vs compression", "graphs"], ["E28", "topo_sort", "Kahn vs DFS", "graphs"], ["E29", "open_addressing", "probes vs load factor", "hashing"], ["E30", "dynamic_array", "copies for three growth policies", "complexity"]];
const DSA_PLAN = [["1", "1–2: ADTs, counting", "E01, E02"], ["2", "3: O/Ω/Θ, cases, recurrences", "E03, E05"], ["3", "4: arrays, dynamic arrays", "E07, E30"], ["4", "5–6: singly and doubly lists", "E07, list self-tests"], ["5", "7: circular singly lists", "E21"], ["6", "8: circular doubly, sentinel, LRU, Floyd", "E22"], ["7", "9–10: stacks, queues, ring buffers", "E08, E23"], ["8", "11: hashing", "E09, E16–E18, E29"], ["9", "12–13: trees, BST, deletion", "E10, E19, E26"], ["10", "14: AVL", "E20, E26"], ["11", "15–16: heaps, tries", "E24, E25"], ["12", "17: graphs, BFS, DFS", "E11"], ["13", "18: Dijkstra, topo sort, union-find", "E12, E27, E28"], ["14", "19–22: search, sort, D&C, greedy, DP", "E04, E13, E15"], ["15", "23: correctness; review", "mini-project"]];
const DSA_EXERCISES = [["Circular list: split into two circular halves; insert into a sorted ring", "lists"], ["Circular doubly list: a playlist with next, prev, remove_current", "lists"], ["LRU cache with a time-to-live per entry — compare with TileLoader", "queues"], ["Ring buffer that overwrites the oldest entry; keep the last 100 GPS fixes", "queues"], ["Double hashing vs linear probing at α = 0.8", "hashing"], ["Full AVL deletion by hand for a 12-node tree", "trees"], ["Heap-based dispatch: 1 000 requests with priorities; report waiting times", "trees"], ["Trie autocomplete for Cork place names, ranked by frequency", "trees"], ["Dijkstra vs BFS on unit weights: prove the results coincide", "graphs"], ["Topological order for the ATLAS food-order lifecycle; add a cycle and detect it", "graphs"], ["Mini-project: ride booking with a request queue, a driver hash map, a heap by distance and a zone graph", "graphs"]];
const dsaTopicLink = (id, k) => `<button type="button" class="dsa-link" data-dsa-topic="${id}" data-keep="dsa-x-${k}">${icon(dsaTopicById[id].icon, 13)}${dsaTopicById[id].title}</button>`;

function dsaGaps() {
  return `<div class="sec-intro"><p>The course pairs every lesson with a measured experiment in <a class="sec-inline-link" href="${DSA_LAB}">dsa_lab/experiments.py</a> (run <code>python dsa_lab/experiments.py --all</code>, or open the <a class="sec-inline-link" href="${DSA_COLAB}">Colab notebook</a>). Each experiment counts operations, writes a CSV, JSON and PNG, and checks its own correctness before it charts anything.</p></div>
    ${secSection("EXPERIMENTS", "The 30 experiments and the lab on this tab that previews each", secTable(["ID", "--experiment", "Question", "Try it here"], DSA_EXPERIMENTS.map(([id, flag, q, topic]) => [id, `<code>${flag}</code>`, q, dsaTopicLink(topic, id)])))}
    ${secSection("EXERCISES", "Assignments built on ATLAS", secTable(["#", "Exercise", "Start from"], DSA_EXERCISES.map(([text, topic], i) => [i + 1, text, dsaTopicLink(topic, "e" + i)])))}
    ${secSection("OBSERVATIONS", "Where ATLAS Go could use a better structure", secTable(["#", "Observation", "Where", "Exercise"], [
      ["1", "History grows forever and is filtered on every view", "<code>LocalStore.my_history</code>", "Index history by user id (dict of lists); measure filtering vs lookup"],
      ["2", "Dispatch sorts all candidates to take one", "<code>intelligence.rank</code>, <code>choose</code>", "Use max / heapq.nsmallest; count comparisons for k = 4 and k = 4 000"],
      ["3", "Nearest place is a linear scan", "<code>geo.nearest_place</code>", "Grid-bucket or k-d tree the 16 zones; when does it pay off?"],
      ["4", "Trips follow straight lines", "<code>geo.ride_legs</code>", "Build a road graph and route with Dijkstra or A*"],
      ["5", "The tile request stack is unbounded", "<code>TileLoader.requests</code>", "Replace it with a bounded ring buffer that drops the oldest request"],
    ]))}
    ${secSection("TEACHING PLAN", "15 weeks", secTable(["Week", "Lessons", "Experiments"], DSA_PLAN))}
    <p class="sec-note">Assessment (100 marks): theory 20 · correct code including edge cases 25 · experimental protocol 20 · interpretation 20 · reproducibility and discussion 15. Full guide: <a class="sec-inline-link" href="${DSA_GUIDE}">docs/DATA_STRUCTURES_ALGORITHMS.md</a>.</p>`;
}

// ================================================================== inspector
const dsaInspect = {
  overview: { summary: "Twenty-four lessons, thirty measured experiments and nine live labs; each lab names the ATLAS Go code that uses its idea, or says that it does not.", files: [["docs/DATA_STRUCTURES_ALGORITHMS.md", DSA_GUIDE], ["dsa_lab/experiments.py", DSA_LAB], ["dsa_lab/README.md", DSA_README], ["dsa_lab/DSA_Colab_Labs.ipynb", DSA_COLAB]], facts: [["Lessons", "24"], ["Experiments", "E01–E30"], ["Structures", "lists ×4, ring, hash ×2, BST, AVL, heap, trie, graph"], ["Data", "the app's places, zones, drivers and menu"]], questions: ["Which structures does ATLAS Go actually use, and which only appear in the course?", "Why count operations instead of timing them?"] },
  complexity: { summary: "Count the basic operation, describe its growth with Θ, and check the prediction against a measurement.", files: [["android-app/atlas_go/store.py", DSA_APP + "store.py"], ["android-app/atlas_go/geo.py", DSA_APP + "geo.py"], ["dsa_lab/experiments.py → linear_search, binary_search", DSA_LAB]], facts: [["Binary search, n = 4096", "13 comparisons"], ["Linear search", "4096"], ["Insertion sort", "~ n²/4"], ["App lookups", "Θ(1) table, Θ(k) scans"]], questions: ["Why is a straight line on log–log axes evidence of a power law?", "When is an O(n²) algorithm the right choice?", "Which ATLAS scan would become a problem first as data grows?"] },
  lists: { summary: "Four linked lists that differ in which pointers they keep; that choice decides which operations are O(1).", files: [["dsa_lab/experiments.py → CircularSinglyLinkedList", DSA_LAB], ["dsa_lab/experiments.py → CircularDoublyLinkedList", DSA_LAB], ["dsa_lab/experiments.py → josephus_circular, floyd_cycle", DSA_LAB]], facts: [["Circular singly", "tail only; head = tail.next"], ["Circular doubly", "sentinel; no special cases"], ["rotate(k)", "pointer moves only"], ["Josephus", "n(k − 1) moves"]], questions: ["Why does a circular singly list keep the tail rather than the head?", "What does the sentinel remove from the code?", "Why is pop_back O(n) on a singly list even with a tail pointer?", "Why do the tortoise and hare always meet inside a cycle?"] },
  queues: { summary: "Stacks and queues are defined by their operations; a ring buffer and an LRU cache are the classic efficient implementations.", files: [["android-app/atlas_go/livemap.py (TileLoader)", DSA_APP + "livemap.py"], ["android-app/atlas_go/domain.py (fare)", DSA_APP + "domain.py"], ["dsa_lab/experiments.py → RingBuffer, LRUCache", DSA_LAB]], facts: [["Ring buffer", "O(1) both ends, no moves"], ["LRU", "dict + circular doubly list"], ["App cache", "OrderedDict, 160 tiles"], ["App work queue", "LifoQueue"]], questions: ["How does the ring buffer tell full from empty?", "Why does an LRU cache need both a hash map and a list?", "Why does the tile loader fetch the newest request first?"] },
  hashing: { summary: "A hash function maps keys to buckets; chaining and probing resolve collisions; the load factor decides the cost.", files: [["android-app/atlas_go/domain.py (DISHES, Cart)", DSA_APP + "domain.py"], ["dsa_lab/experiments.py → ChainHash, OpenAddressHash", DSA_LAB]], facts: [["Chaining", "≈ 1 + α/2 probes"], ["Linear probing", "≈ ½(1 + 1/(1 − α))"], ["Resize at", "α > 1 (chain), α > 0.7 (probe)"], ["Python dict", "open addressing, resize at ⅔"]], questions: ["Why does deletion in open addressing need tombstones?", "Why does Python randomise string hashes?", "What does doubling the table cost, and why is insertion still amortised O(1)?"] },
  trees: { summary: "Search cost is tree height; AVL rotations keep it logarithmic; a heap keeps only the minimum handy.", files: [["android-app/atlas_go/intelligence.py (DRIVER_POOLS, rank)", DSA_APP + "intelligence.py"], ["dsa_lab/experiments.py → avl_insert, bst_delete", DSA_LAB], ["dsa_lab/experiments.py → MinHeap, Trie", DSA_LAB]], facts: [["Sorted input, BST", "height n"], ["AVL height", "≤ 1.44 log₂ n"], ["Heap", "O(1) min, O(log n) push/pop"], ["Trie", "O(prefix length)"]], questions: ["Which insertion orders make a plain BST degenerate?", "Why are two rotations needed in the LR and RL cases?", "When would dispatch need a heap instead of sorted()?"] },
  graphs: { summary: "BFS, DFS, Dijkstra and Prim on a graph built from the app's sixteen Cork zones and its Haversine distance.", files: [["android-app/atlas_go/geo.py (ZONE_COORDS, haversine_km)", DSA_APP + "geo.py"], ["dsa_lab/experiments.py → bfs, dfs, dijkstra", DSA_LAB], ["dsa_lab/experiments.py → UnionFind, kruskal, topo_sort_kahn", DSA_LAB]], facts: [["Vertices", "16 zones"], ["Edges", `${DSA_GRAPH.edges.length} (3 nearest each)`], ["Weights", "Haversine km"], ["App routing", "straight lines — no graph"]], questions: ["Why can BFS's route be longer in km than Dijkstra's?", "Why does Dijkstra fail with negative weights?", "What would ATLAS need to route along roads?"] },
  sorting: { summary: "Seven sorts counted on the same input; stability on the app's drivers; binary search for the first match.", files: [["android-app/atlas_go/intelligence.py (rank)", DSA_APP + "intelligence.py"], ["dsa_lab/experiments.py → insertion_sort … heap_sort", DSA_LAB], ["dsa_lab/experiments.py → stability_violations, first_occurrence", DSA_LAB]], facts: [["Lower bound", "Ω(n log n) comparisons"], ["Stable", "insertion, merge, Timsort"], ["Unstable", "selection, quick, heap"], ["App", "sorted() — Timsort, stable"]], questions: ["Why does insertion sort beat merge sort on nearly sorted data?", "When does stability matter?", "Why does first_occurrence keep searching left after a match?"] },
  design: { summary: "Divide and conquer, dynamic programming, greedy and backtracking, each shown on a small ATLAS-flavoured problem.", files: [["android-app/atlas_go/domain.py (MENU)", DSA_APP + "domain.py"], ["dsa_lab/experiments.py → fib_memo_calls, knapsack_01", DSA_LAB], ["dsa_lab/experiments.py → n_queens, interval_schedule", DSA_LAB]], facts: [["Fib(30) naive", "2.7 M calls"], ["Fib(30) memo", "59 calls"], ["Knapsack", "Θ(n·C)"], ["8 queens", "92 solutions"]], questions: ["How do you recognise overlapping subproblems?", "Give a problem where greedy is provably optimal.", "Why is the knapsack DP called pseudo-polynomial?"] },
  gaps: { summary: "Thirty experiments, fifteen exercises, five observations about the app and a fifteen-week plan.", files: [["dsa_lab/README.md", DSA_README], ["docs/DATA_STRUCTURES_ALGORITHMS.md → Exercise bank", DSA_GUIDE + "#exercise-bank"]], facts: [["Experiments", "30"], ["Exercises", "15"], ["Weeks", "15"], ["Marks", "100"]], questions: ["Which observation about ATLAS Go would matter first at city scale?"] },
};

function dsaInspector() {
  const t = dsaTopicById[dsa.topic], info = dsaInspect[dsa.topic];
  return `<div class="inspector-head"><span>${icon("book", 16)} DSA INSPECTOR</span><span class="status-dot" aria-hidden="true"></span></div>
    <div class="inspector-body" style="--accent:${t.status === "impl" ? "#c2f77a" : t.status === "teach" ? "#c4aeff" : "#90bfe8"}"><div class="inspector-identity"><span class="component-icon">${icon(t.icon, 23)}</span><div><p>${t.status ? dsaStatus[t.status].label : "Overview"}</p><h2 id="component-title" tabindex="-1">${t.title}</h2></div></div>
    <p class="inspector-summary">${info.summary}</p>
    <dl class="sec-facts">${info.facts.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join("")}</dl>
    <div class="connection-group"><h3>Lessons</h3>${t.lessons.map((n) => `<a class="uml-row" href="${DSA_GUIDE}#${dsaSlug(n)}"><span>${n}. ${DSA_LESSONS[n - 1]}</span>${icon("diagonal", 12)}</a>`).join("")}</div>
    <div class="connection-group"><h3>Where in the code</h3>${info.files.map(([l, u]) => secLink(l, u)).join("")}</div>
    ${umlInspector(`dsa/${dsa.topic}`, "dsa", dsaTopics)}
    <div class="connection-group"><h3>Questions for students</h3><ol class="sec-questions">${info.questions.map((x) => `<li>${x}</li>`).join("")}</ol></div></div>`;
}

// ================================================================== view + events
const dsaRenderers = { overview: dsaOverview, complexity: dsaComplexity, lists: () => dsaLists() + dsaFloyd(), queues: dsaQueues, hashing: dsaHashing, trees: dsaTrees, graphs: dsaGraphs, sorting: dsaSorting, design: dsaDesign, gaps: dsaGaps };

function dsaView() {
  const t = dsaTopicById[dsa.topic];
  return viewHeading("DATA STRUCTURES & ALGORITHMS", "How the data is organised and searched", "All four kinds of linked list including the circular ones, stacks, queues, ring buffers, LRU caches, hash tables, trees, heaps, tries, graphs and sorting — run live in your browser on the app's own places, drivers and menu.", `<a class="panel-badge sec-guide" href="${DSA_GUIDE}">Teaching guide ↗</a>`)
    + `<nav class="sec-topics" aria-label="Data structures and algorithms topics">${dsaTopics.map((x) => `<button type="button" data-dsa-topic="${x.id}" data-keep="dsa-topic-${x.id}" aria-pressed="${x.id === dsa.topic}">${icon(x.icon, 15)}${x.title}${x.status ? `<i class="sec-dot ${dsaStatus[x.status].tone}" aria-label="${dsaStatus[x.status].label}"></i>` : ""}</button>`).join("")}</nav>
    <div class="sec-body"><div class="sec-title-row"><h3>${t.title}</h3>${dsaChip(t.status)}${umlChip(dsa.topic === "overview" ? "data-structures-and-algorithms-catalogue" : `uml-dsa-${dsa.topic}`, "UML catalogue")}</div>${dsaRenderers[dsa.topic]()}${dsa.topic === "overview" ? umlTopicsSection("dsa", dsaTopics) : umlSection(`dsa/${dsa.topic}`)}</div>`;
}

function dsaOpen(topic) {
  dsa.topic = dsaTopicById[topic] ? topic : "overview";
  state.view = "dsa";
}

function dsaSetHash() {
  try { history.replaceState(null, "", "#dsa" + (dsa.topic === "overview" ? "" : "-" + dsa.topic)); } catch (error) { /* file:// */ }
}

function dsaClick(button) {
  const { dsaTopic, dsaAction: a } = button.dataset;
  if (dsaTopic) {
    dsa.topic = dsaTopic;
    state.view = "dsa";
    dsaSetHash();
    announce("Data structures topic: " + dsaTopicById[dsaTopic].title);
    render();
    if (button.classList.contains("dsa-link") || button.classList.contains("sec-card")) document.querySelector(".sec-topics")?.scrollIntoView({ block: "nearest" });
    return true;
  }
  if (!a) return false;
  if (["push-front", "push-back", "pop-front", "pop-back", "rotate-1", "rotate-3"].includes(a)) dsaListOp(a);
  else if (a === "list-reset") dsaListNew();
  else if (a === "jos-step") { dsaJosStep(); announce(`Person ${dsa.jos.last} leaves`); }
  else if (a === "jos-run") while (dsa.jos.ring.size) dsaJosStep();
  else if (a === "jos-reset") dsaJosNew();
  else if (a === "floyd-step") dsaFloydStep();
  else if (a === "floyd-run") { let guard = 0; while (dsa.floyd.phase !== 4 && guard++ < 500) dsaFloydStep(); }
  else if (a === "floyd-reset") dsaFloydNew();
  else if (a === "ring-enq") dsaRingOp("enq");
  else if (a === "ring-deq") dsaRingOp("deq");
  else if (a === "ring-enq3") for (let i = 0; i < 3; i++) dsaRingOp("enq");
  else if (a === "ring-grow") dsa.ringGrow = !dsa.ringGrow;
  else if (a === "ring-reset") dsaRingNew();
  else if (a.startsWith("lru-")) { if (a === "lru-reset") dsaLruNew(); else dsaLruGet(a.slice(4)); }
  else if (a === "hash-put") { dsaHashPut(dsa.hash, DSA_KEYS[dsa.hash.next % DSA_KEYS.length]); dsa.hash.next += 1; }
  else if (a === "hash-put4") for (let i = 0; i < 4; i++) { dsaHashPut(dsa.hash, DSA_KEYS[dsa.hash.next % DSA_KEYS.length]); dsa.hash.next += 1; }
  else if (a === "hash-del") dsaHashDelete(dsa.hash);
  else if (a === "hash-resize") dsa.hashResize = !dsa.hashResize;
  else if (a === "hash-reset") dsaHashNew();
  else if (a === "tree-insert") dsaTreeInsert();
  else if (a === "tree-all") while (dsa.tree.i < DSA_TREE_INPUTS[dsa.treeInput].keys.length) dsaTreeInsert();
  else if (a === "tree-delete") { const T = dsa.tree, keys = dsaTreeKeys(T.bst), k = keys.includes(T.delKey) ? T.delKey : keys[0], info = {}; T.bst = dsaDelete(T.bst, k, false, info); T.avl = dsaDelete(T.avl, k, true, null, T.rot); T.del = { key: k, kind: info.kind }; T.last = null; T.delKey = null; }
  else if (a === "tree-reset") dsaTreeNew();
  else if (a === "heap-push") dsaHeapPush();
  else if (a === "heap-pop") dsaHeapPop();
  else if (a === "heap-reset") dsaHeapNew();
  else if (a.startsWith("graph-")) {
    const G = dsa.graph, end = G.frames.length - 1;
    if (a === "graph-next") G.i = Math.min(end, G.i + 1); else if (a === "graph-prev") G.i = Math.max(0, G.i - 1); else if (a === "graph-end") G.i = end; else if (a === "graph-restart") G.i = 0; else if (a === "graph-w") dsa.graphShowW = !dsa.graphShowW;
  } else if (a.startsWith("trace-")) {
    const T = dsa.trace, end = T.frames.length - 1;
    if (a === "trace-next") T.i = Math.min(end, T.i + 1); else if (a === "trace-prev") T.i = Math.max(0, T.i - 1); else if (a === "trace-10") T.i = Math.min(end, T.i + 10); else if (a === "trace-end") T.i = end; else if (a === "trace-new") { dsa.traceSeed = (dsa.traceSeed || 11) + 1; dsaTraceNew(); }
  }
  render();
  return true;
}

document.addEventListener("input", (event) => {
  const name = event.target.dataset?.dsaRange;
  if (!name) return;
  const out = document.getElementById("dsa-out-" + name);
  if (out) out.textContent = event.target.value;
});

document.addEventListener("change", (event) => {
  const range = event.target.dataset?.dsaRange, sel = event.target.dataset?.dsaSelect;
  if (!range && !sel) return;
  const raw = event.target.value, v = Number(raw);
  if (range === "cxn") dsa.cx.n = v;
  if (range === "fib") dsa.design.fib = v;
  if (sel === "kind") dsaListNew(raw);
  if (sel === "josn") { dsa.josN = v; dsaJosNew(); }
  if (sel === "josk") { dsa.josK = v; dsaJosNew(); }
  if (sel === "fmu") dsaFloydNew(v, dsa.floyd.lam);
  if (sel === "flam") dsaFloydNew(dsa.floyd.mu, v);
  if (sel === "hmode") { dsa.hashMode = raw; dsaHashNew(); }
  if (sel === "hm") { dsa.hashM = v; dsaHashNew(); }
  if (sel === "tinput") { dsa.treeInput = raw; dsaTreeNew(); }
  if (sel === "tdel") dsa.tree.delKey = v;
  if (sel === "trie") dsa.triePrefix = raw;
  if (sel === "galgo" || sel === "gsrc" || sel === "gdst") { if (sel === "galgo") dsa.graphAlgo = raw; if (sel === "gsrc") dsa.graphSrc = v; if (sel === "gdst") dsa.graphDst = v; dsaGraphNew(); }
  if (sel === "sn") dsa.sortN = v;
  if (sel === "sorder") dsa.sortOrder = raw;
  if (sel === "talgo") { dsa.traceAlgo = raw; dsaTraceNew(); }
  if (sel === "starget") dsa.searchTarget = v;
  if (sel === "cap") dsa.design.cap = v;
  if (sel === "queens") dsa.design.queens = v;
  render();
});
