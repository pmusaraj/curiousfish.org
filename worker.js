// An explicit Markdown media type opts in. Wildcards alone retain HTML.
export function prefersMarkdown(accept = "") {
  const ranges = accept.toLowerCase().split(",").map((entry) => {
    const [type, ...parameters] = entry.trim().split(";");
    const quality = parameters.find((parameter) => parameter.trim().startsWith("q="));
    const raw = quality?.trim().slice(2);
    const q = raw === undefined ? 1 : /^(?:0(?:\.\d{0,3})?|1(?:\.0{0,3})?)$/.test(raw) ? Number(raw) : 0;
    return { type: type.trim(), q };
  });
  function qualityFor(type) {
    for (const candidate of [type, "text/*", "*/*"]) {
      const matches = ranges.filter((range) => range.type === candidate);
      if (matches.length) return Math.max(...matches.map((range) => range.q));
    }
    return 0;
  }
  return ranges.some((range) => range.type === "text/markdown") &&
    qualityFor("text/markdown") > 0 &&
    qualityFor("text/markdown") >= qualityFor("text/html");
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const homepage = url.pathname === "/" || url.pathname === "/index.html";
    const markdownPath = url.pathname === "/index.md";
    const allowed = homepage || markdownPath || url.pathname === "/style.css" || url.pathname === "/theme.js" || url.pathname === "/activity.js" ||
      url.pathname.startsWith("/images/");
    if (!allowed) {
      return new Response("Not found", { status: 404 });
    }
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method not allowed", { status: 405, headers: { Allow: "GET, HEAD" } });
    }

    const markdown = markdownPath || (homepage && prefersMarkdown(request.headers.get("Accept") || ""));
    const assetUrl = new URL(request.url);
    if (markdown) assetUrl.pathname = "/index.md";
    const assetResponse = await env.ASSETS.fetch(new Request(assetUrl, request));
    const response = new Response(request.method === "HEAD" ? null : assetResponse.body, assetResponse);
    if (markdown && assetResponse.ok) {
      response.headers.set("Content-Type", "text/markdown; charset=utf-8");
      response.headers.set("X-Content-Type-Options", "nosniff");
    }
    if (homepage) {
      const vary = response.headers.get("Vary");
      if (!vary?.split(",").some((value) => ["accept", "*"].includes(value.trim().toLowerCase()))) {
        response.headers.set("Vary", vary ? `${vary}, Accept` : "Accept");
      }
    }
    response.headers.set("Cache-Control", "no-store");
    return response;
  },
};
