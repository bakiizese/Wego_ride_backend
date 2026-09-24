// Serves the landing page from Cloudflare's static assets (wrangler.jsonc) and
// passes everything else (docs, API, health, websockets) through to Render, so
// the public address stays the Cloudflare one.
const ORIGIN = "https://wego-ride-backend.onrender.com";

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const target = new URL(url.pathname + url.search, ORIGIN);
    const upstreamRequest = new Request(target, request);
    // let the runtime decode Render's response itself, and re-compress for
    // the real client below, instead of passing a possibly-mismatched
    // Content-Encoding through
    upstreamRequest.headers.delete("Accept-Encoding");

    // re-wrapping the response would break the websocket handshake
    if (request.headers.get("Upgrade") === "websocket") {
      return fetch(upstreamRequest);
    }

    const upstream = await fetch(upstreamRequest, { redirect: "manual" });
    const response = new Response(upstream.body, upstream);
    response.headers.delete("Content-Encoding");
    response.headers.delete("Content-Length");

    // Flask builds redirects (e.g. /apidocs -> /apidocs/) from the Host it
    // sees, which is the Render one
    const location = response.headers.get("Location");
    if (location && location.startsWith(ORIGIN)) {
      response.headers.set("Location", url.origin + location.slice(ORIGIN.length));
    }
    return response;
  },
};
