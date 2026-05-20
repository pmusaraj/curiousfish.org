const ASSET_VERSION = "20260519-simple-static-site";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const allowed = url.pathname === "/" ||
      url.pathname === "/index.html" ||
      url.pathname === "/style.css" ||
      url.pathname.startsWith("/images/");

    if (!allowed) {
      return new Response("Not found", {
        status: 404,
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
    }

    const assetUrl = new URL(request.url);
    assetUrl.searchParams.set("v", ASSET_VERSION);

    const assetResponse = await env.ASSETS.fetch(new Request(assetUrl, request));
    const response = new Response(assetResponse.body, assetResponse);
    response.headers.set("cache-control", "no-store");
    return response;
  },
};
