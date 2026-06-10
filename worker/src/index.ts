import { CommandCentreDO } from "./command_centre_do";
import { CampaignPipeline, CampaignPipelineParams } from "./campaign_pipeline";

export { CommandCentreDO, CampaignPipeline };

interface WorkflowBinding<P = unknown> {
  create(options: { id?: string; params?: P }): Promise<{ id: string }>;
  get(id: string): Promise<{ id: string; status(): Promise<unknown> }>;
}

interface Env {
  API_CACHE: KVNamespace;
  APP_SERVICE_URL: string;
  COMMAND_CENTRE: DurableObjectNamespace<CommandCentreDO>;
  CAMPAIGN_PIPELINE: WorkflowBinding<CampaignPipelineParams>;
  CLERK_PUBLISHABLE_KEY?: string;
  DEFAULT_TTL: string;
  COMM_SERVICE_URL: string;
  INTERNAL_SHARED_TOKEN?: string;
}

const CACHEABLE_METHODS = new Set(["GET"]);
const INVALIDATE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);
const CACHE_TTL = 300;
const KEY_PREFIX = "api:";

async function hashAuth(auth: string | null): Promise<string> {
  if (!auth) return "anon";
  const bytes = new TextEncoder().encode(auth);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  const hex = Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return hex.slice(0, 16);
}

async function cacheKey(request: Request): Promise<string> {
  const url = new URL(request.url);
  const auth = await hashAuth(request.headers.get("Authorization"));
  return `${KEY_PREFIX}${auth}:${url.pathname}${url.search}`;
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

function getApiUrl(env: Env): string {
  return env.APP_SERVICE_URL;
}

async function getCommandCentreStub(
  env: Env,
  request: Request,
): Promise<DurableObjectStub<CommandCentreDO>> {
  const userKey = await hashAuth(request.headers.get("Authorization"));
  const id = env.COMMAND_CENTRE.idFromName(`cc:${userKey}`);
  return env.COMMAND_CENTRE.get(id);
}

async function handleCommandCentreHistory(
  request: Request,
  env: Env,
  cors: HeadersInit,
): Promise<Response> {
  const stub = await getCommandCentreStub(env, request);
  const history = await stub.getHistory();
  return new Response(JSON.stringify({ history }), {
    status: 200,
    headers: { ...cors, "Content-Type": "application/json" },
  });
}

async function handleCommandCentreClear(
  request: Request,
  env: Env,
  cors: HeadersInit,
): Promise<Response> {
  const stub = await getCommandCentreStub(env, request);
  await stub.clear();
  return new Response(JSON.stringify({ status: "cleared" }), {
    status: 200,
    headers: { ...cors, "Content-Type": "application/json" },
  });
}

async function handleWorkflowDispatch(
  request: Request,
  env: Env,
  cors: HeadersInit,
): Promise<Response> {
  const expected = env.INTERNAL_SHARED_TOKEN;
  const provided = request.headers.get("X-Internal-Token");
  if (!expected || provided !== expected) {
    return new Response(JSON.stringify({ detail: "Invalid internal token" }), {
      status: 401,
      headers: { ...cors, "Content-Type": "application/json" },
    });
  }

  let body: Partial<CampaignPipelineParams>;
  try {
    body = await request.json();
  } catch {
    return new Response(JSON.stringify({ detail: "Invalid JSON" }), {
      status: 400,
      headers: { ...cors, "Content-Type": "application/json" },
    });
  }

  if (!body.campaign_id || !Array.isArray(body.communication_ids) || body.communication_ids.length === 0) {
    return new Response(JSON.stringify({ detail: "campaign_id and non-empty communication_ids required" }), {
      status: 400,
      headers: { ...cors, "Content-Type": "application/json" },
    });
  }

  const params: CampaignPipelineParams = {
    campaign_id: body.campaign_id,
    communication_ids: body.communication_ids,
    batch_size: body.batch_size,
    rate_limit_seconds: body.rate_limit_seconds,
  };

  try {
    const instance = await env.CAMPAIGN_PIPELINE.create({ params });
    return new Response(JSON.stringify({ instance_id: instance.id, status: "started" }), {
      status: 202,
      headers: { ...cors, "Content-Type": "application/json" },
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return new Response(JSON.stringify({ detail: `Failed to start workflow: ${msg}` }), {
      status: 500,
      headers: { ...cors, "Content-Type": "application/json" },
    });
  }
}

async function handleCommandCentreChat(
  request: Request,
  env: Env,
  cors: HeadersInit,
  appServiceUrl: string,
): Promise<Response> {
  let body: { query?: string };
  try {
    body = await request.json();
  } catch {
    return new Response(JSON.stringify({ detail: "Invalid JSON" }), {
      status: 400,
      headers: { ...cors, "Content-Type": "application/json" },
    });
  }
  const query = (body.query || "").trim();
  if (!query) {
    return new Response(JSON.stringify({ detail: "Empty query" }), {
      status: 400,
      headers: { ...cors, "Content-Type": "application/json" },
    });
  }

  const stub = await getCommandCentreStub(env, request);
  await stub.appendMessage("user", query);

  const upstreamHeaders = new Headers({ "Content-Type": "application/json" });
  const auth = request.headers.get("Authorization");
  if (auth) upstreamHeaders.set("Authorization", auth);

  const upstream = await fetch(`${appServiceUrl}/api/v1/agents/command-centre`, {
    method: "POST",
    headers: upstreamHeaders,
    body: JSON.stringify({ query }),
  });

  if (!upstream.ok) {
    const text = await upstream.text();
    return new Response(text, {
      status: upstream.status,
      headers: { ...cors, "Content-Type": "application/json" },
    });
  }

  const result = (await upstream.json()) as { response?: string };
  const assistantText = result.response || "I could not process that query.";
  await stub.appendMessage("assistant", assistantText);

  return new Response(JSON.stringify(result), {
    status: 200,
    headers: { ...cors, "Content-Type": "application/json" },
  });
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "*";
    const cors = corsHeaders(origin);
    const appServiceUrl = getApiUrl(env);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }

    if (url.pathname === "/api/v1/config") {
      return new Response(JSON.stringify({
        clerkPublishableKey: env.CLERK_PUBLISHABLE_KEY || "",
      }), {
        status: 200,
        headers: { ...cors, "Content-Type": "application/json" },
      });
    }

    if (url.pathname === "/internal/workflows/dispatch" && request.method === "POST") {
      return handleWorkflowDispatch(request, env, cors);
    }

    if (url.pathname === "/api/v1/command-centre/history" && request.method === "GET") {
      return handleCommandCentreHistory(request, env, cors);
    }
    if (url.pathname === "/api/v1/command-centre/history" && request.method === "DELETE") {
      return handleCommandCentreClear(request, env, cors);
    }
    if (url.pathname === "/api/v1/command-centre/chat" && request.method === "POST") {
      return handleCommandCentreChat(request, env, cors, appServiceUrl);
    }

    if (INVALIDATE_METHODS.has(request.method)) {
      const apiUrl = `${appServiceUrl}${url.pathname}${url.search}`;
      const resp = await fetch(apiUrl, { method: request.method, headers: request.headers, body: request.body });
      const respHeaders = new Headers(resp.headers);
      for (const [k, v] of Object.entries(cors)) respHeaders.set(k, v);

      const auth = await hashAuth(request.headers.get("Authorization"));
      const exactKey = `${KEY_PREFIX}${auth}:${url.pathname}${url.search}`;
      ctx.waitUntil(env.API_CACHE.delete(exactKey));

      const collectionPath = url.pathname.split("/").slice(0, -1).join("/") + "/";
      const collectionPrefix = `${KEY_PREFIX}${auth}:${collectionPath}`;
      ctx.waitUntil(clearPrefix(env.API_CACHE, collectionPrefix));

      return new Response(resp.body, { status: resp.status, headers: respHeaders });
    }

    if (request.method === "GET" && !shouldBypassCache(url.pathname)) {
      const ck = await cacheKey(request);
      const cached = await env.API_CACHE.get(ck, "json");
      if (cached !== null) {
        return new Response(JSON.stringify(cached), {
          status: 200,
          headers: { ...cors, "Content-Type": "application/json", "X-Cache": "HIT" },
        });
      }

      const apiUrl = `${appServiceUrl}${url.pathname}${url.search}`;
      const resp = await fetch(apiUrl, { method: "GET", headers: request.headers });
      const respHeaders = new Headers(resp.headers);
      for (const [k, v] of Object.entries(cors)) respHeaders.set(k, v);
      respHeaders.set("X-Cache", "MISS");

      const contentType = resp.headers.get("Content-Type") || "";
      if (resp.ok && contentType.includes("application/json")) {
        const body = await resp.json();
        ctx.waitUntil(env.API_CACHE.put(ck, JSON.stringify(body), { expirationTtl: CACHE_TTL }));
        return new Response(JSON.stringify(body), { status: resp.status, headers: respHeaders });
      }

      return new Response(resp.body, { status: resp.status, headers: respHeaders });
    }

    const apiUrl = `${appServiceUrl}${url.pathname}${url.search}`;
    const resp = await fetch(apiUrl, { method: request.method, headers: request.headers, body: request.body });
    const respHeaders = new Headers(resp.headers);
    for (const [k, v] of Object.entries(cors)) respHeaders.set(k, v);
    return new Response(resp.body, { status: resp.status, headers: respHeaders });
  },
} satisfies ExportedHandler<Env>;

async function clearPrefix(kv: KVNamespace, prefix: string): Promise<void> {
  let cursor: string | undefined;
  do {
    const list = await kv.list({ prefix, cursor });
    await Promise.all(list.keys.map((k) => kv.delete(k.name)));
    cursor = list.list_complete ? undefined : list.cursor;
  } while (cursor);
}
