import { DurableObject } from "cloudflare:workers";

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  ts: number;
}

export class CommandCentreDO extends DurableObject {
  constructor(ctx: DurableObjectState, env: unknown) {
    super(ctx, env);
    ctx.blockConcurrencyWhile(async () => {
      ctx.storage.sql.exec(`
        CREATE TABLE IF NOT EXISTS messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
          text TEXT NOT NULL,
          ts INTEGER NOT NULL
        )
      `);
    });
  }

  async appendMessage(role: ChatMessage["role"], text: string): Promise<ChatMessage> {
    const ts = Date.now();
    this.ctx.storage.sql.exec(
      "INSERT INTO messages (role, text, ts) VALUES (?, ?, ?)",
      role,
      text,
      ts,
    );
    return { role, text, ts };
  }

  async getHistory(limit = 200): Promise<ChatMessage[]> {
    const rows = this.ctx.storage.sql
      .exec<ChatMessage>(
        "SELECT role, text, ts FROM messages ORDER BY id ASC LIMIT ?",
        limit,
      )
      .toArray();
    return rows;
  }

  async clear(): Promise<void> {
    this.ctx.storage.sql.exec("DELETE FROM messages");
  }
}
