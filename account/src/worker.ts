// Cloudflare entry point SKETCH. Not deployed. Wiring only: real deployment needs a
// D1-backed Store, a real EmailSender and a real PaymentProvider, with secrets set via
// `wrangler secret put` (never committed).

import { handle, type LegalVersions } from "./app.ts";
import { ConsoleEmail } from "./auth.ts";
import { MockProvider } from "./billing/mock.ts";
import { MemoryStore } from "./store.ts";

type Env = { BASE_URL: string; MOCK_WEBHOOK_SECRET: string };

const LEGAL: LegalVersions = { kvkk_aydinlatma: "draft-1", mesafeli_satis: "draft-1", on_bilgilendirme: "draft-1", cayma_istisnasi: "draft-1" };

// In-memory state is per-isolate and lost on restart: development only.
const store = new MemoryStore();
const mail = new ConsoleEmail();

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    if (!new URL(req.url).pathname.startsWith("/api/")) return new Response("Not found", { status: 404 });
    return handle(req, { store, mail, provider: new MockProvider(env.MOCK_WEBHOOK_SECRET), baseUrl: env.BASE_URL, legal: LEGAL });
  },
};
