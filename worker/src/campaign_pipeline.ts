import { WorkflowEntrypoint, WorkflowStep, WorkflowEvent } from "cloudflare:workers";

export interface CampaignPipelineParams {
  campaign_id: string;
  communication_ids: string[];
  batch_size?: number;
  rate_limit_seconds?: number;
}

interface PipelineEnv {
  COMM_SERVICE_URL: string;
  INTERNAL_SHARED_TOKEN: string;
}

const DEFAULT_BATCH_SIZE = 25;
const DEFAULT_RATE_LIMIT_SECONDS = 30;

export class CampaignPipeline extends WorkflowEntrypoint<PipelineEnv, CampaignPipelineParams> {
  async run(event: WorkflowEvent<CampaignPipelineParams>, step: WorkflowStep): Promise<unknown> {
    const { campaign_id, communication_ids } = event.payload;
    const rawBatchSize = event.payload.batch_size ?? DEFAULT_BATCH_SIZE;
    const batchSize = Number.isFinite(rawBatchSize) && rawBatchSize > 0 ? Math.floor(rawBatchSize) : DEFAULT_BATCH_SIZE;
    const rawSleep = event.payload.rate_limit_seconds ?? DEFAULT_RATE_LIMIT_SECONDS;
    const sleepSeconds = Number.isFinite(rawSleep) && rawSleep >= 0 ? rawSleep : DEFAULT_RATE_LIMIT_SECONDS;
    const baseUrl = this.env.COMM_SERVICE_URL;
    const token = this.env.INTERNAL_SHARED_TOKEN;

    if (!baseUrl || !token) {
      throw new Error("CampaignPipeline misconfigured: COMM_SERVICE_URL or INTERNAL_SHARED_TOKEN missing");
    }
    if (!Array.isArray(communication_ids) || communication_ids.length === 0) {
      return { campaign_id, processed: 0, batches: 0 };
    }

    let processed = 0;
    let batchNum = 0;

    for (let i = 0; i < communication_ids.length; i += batchSize) {
      const batch = communication_ids.slice(i, i + batchSize);
      batchNum++;

      const batchResult = await step.do(`send-batch-${batchNum}`, async () => {
        const resp = await fetch(`${baseUrl}/api/v1/internal/process-batch`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Internal-Token": token,
          },
          body: JSON.stringify({ campaign_id, communication_ids: batch }),
        });
        if (!resp.ok) {
          throw new Error(`process-batch ${batchNum} failed: ${resp.status} ${await resp.text()}`);
        }
        return (await resp.json()) as { processed?: number };
      });
      processed += batchResult.processed ?? batch.length;

      const remaining = communication_ids.length - (i + batchSize);
      if (remaining > 0) {
        await step.sleep(`rate-limit-${batchNum}`, `${sleepSeconds} seconds`);
      }
    }

    return { campaign_id, processed, batches: batchNum };
  }
}
