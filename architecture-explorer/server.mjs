import { readFile } from "node:fs/promises";
import { createServer } from "node:http";

const host = "127.0.0.1";
const port = Number(process.env.PORT ?? 8080);
if (!Number.isInteger(port) || port < 1 || port > 65535) {
  throw new Error("PORT must be an integer from 1 to 65535.");
}

const contentTypes = {
  "index.html": "text/html; charset=utf-8",
  "build.html": "text/html; charset=utf-8",
  "build.js": "text/javascript; charset=utf-8",
  "build-spec.json": "application/json; charset=utf-8",
  "ride-event.schema.json": "application/schema+json; charset=utf-8",
  "styles.css": "text/css; charset=utf-8",
  "atlas.js": "text/javascript; charset=utf-8",
  "atlas-go.js": "text/javascript; charset=utf-8",
  "uml-catalog.js": "text/javascript; charset=utf-8",
  "security.js": "text/javascript; charset=utf-8",
  "crypto.js": "text/javascript; charset=utf-8",
  "ml.js": "text/javascript; charset=utf-8",
  "explorer.js": "text/javascript; charset=utf-8",
  "atlas.svg": "image/svg+xml",
};

const assets = new Map(await Promise.all(Object.entries(contentTypes).map(async ([file, type]) => {
  const body = await readFile(new URL(`./dist/${file}`, import.meta.url));
  return ["/" + file, { type, body }];
})));

const textType = "text/plain; charset=utf-8";
const securityHeaders = {
  "Cache-Control": "no-store",
  "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
  "Referrer-Policy": "no-referrer",
  "X-Content-Type-Options": "nosniff",
  "X-Robots-Tag": "noindex, nofollow",
};

function reply(request, response, status, type, body, headers = {}) {
  response.writeHead(status, {
    ...securityHeaders,
    ...headers,
    "Content-Type": type,
    "Content-Length": Buffer.byteLength(body),
  });
  response.end(request.method === "HEAD" ? undefined : body);
}

createServer((request, response) => {
  if (request.method !== "GET" && request.method !== "HEAD") {
    return reply(request, response, 405, textType, "Method not allowed\n", { Allow: "GET, HEAD" });
  }

  const path = request.url.split("?", 1)[0];
  if (path === "/healthz") {
    return reply(request, response, 200, textType, "ok\n");
  }

  const asset = assets.get(path === "/" ? "/index.html" : path);
  if (!asset) {
    return reply(request, response, 404, textType, "Not found\n");
  }

  reply(request, response, 200, asset.type, asset.body);
}).listen(port, host, () => console.log(`ATLAS listening on http://${host}:${port}/`));
