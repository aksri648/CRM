interface Env {
  API_CACHE: KVNamespace;
  APP_SERVICE_URL: string;
  DEFAULT_TTL: string;
}

const CACHEABLE_METHODS = new Set(["GET"]);
const INVALIDATE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);
const CACHE_TTL = 300;

function cacheKey(request: Request): string {
  const url = new URL(request.url);
  return `api:${url.pathname}${url.search}`;
}

function shouldBypassCache(pathname: string): boolean {
  return pathname === "/api/v1/auth/login" || pathname === "/api/v1/auth/register";
}

function corsHeaders(origin: string): HeadersInit {
  return {
    "Access-Control-Allow-Origin": origin || "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Max-Age": "86400",
  };
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "*";
    const cors = corsHeaders(origin);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }

    if (INVALIDATE_METHODS.has(request.method)) {
      const apiUrl = `${env.APP_SERVICE_URL}${url.pathname}${url.search}`;
      const resp = await fetch(apiUrl, { method: request.method, headers: request.headers, body: request.body });
      const respHeaders = new Headers(resp.headers);
      for (const [k, v] of Object.entries(cors)) respHeaders.set(k, v);

      const ck = cacheKey(request);
      ctx.waitUntil(env.API_CACHE.delete(ck));

      const prefix = url.pathname.split("/").slice(0, -1).join("/") + "/";
      ctx.waitUntil(clearPrefix(env.API_CACHE, prefix));

      return new Response(resp.body, { status: resp.status, headers: respHeaders });
    }

    if (request.method === "GET" && !shouldBypassCache(url.pathname)) {
      const ck = cacheKey(request);
      const cached = await env.API_CACHE.get(ck, "json");
      if (cached !== null) {
        return new Response(JSON.stringify(cached), {
          status: 200,
          headers: { ...cors, "Content-Type": "application/json", "X-Cache": "HIT" },
        });
      }

      const apiUrl = `${env.APP_SERVICE_URL}${url.pathname}${url.search}`;
      const resp = await fetch(apiUrl, { method: "GET", headers: request.headers });
      const respHeaders = new Headers(resp.headers);
      for (const [k, v] of Object.entries(cors)) respHeaders.set(k, v);
      respHeaders.set("X-Cache", "MISS");

      if (resp.ok) {
        const body = await resp.json();
        ctx.waitUntil(env.API_CACHE.put(ck, JSON.stringify(body), { expirationTtl: CACHE_TTL }));
        return new Response(JSON.stringify(body), { status: resp.status, headers: respHeaders });
      }

      return new Response(resp.body, { status: resp.status, headers: respHeaders });
    }

    const apiUrl = `${env.APP_SERVICE_URL}${url.pathname}${url.search}`;
    const resp = await fetch(apiUrl, { method: request.method, headers: request.headers, body: request.body });
    const respHeaders = new Headers(resp.headers);
    for (const [k, v] of Object.entries(cors)) respHeaders.set(k, v);
    return new Response(resp.body, { status: resp.status, headers: respHeaders });
  },
} satisfies ExportedHandler<Env>;

async function clearPrefix(kv: KVNamespace, prefix: string): Promise<void> {
  const list = await kv.list({ prefix });
  if (list.keys.length === 0) return;
  await kv.delete(list.keys.map((k) => k.name));
}
