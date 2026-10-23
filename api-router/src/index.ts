import { Container, getContainer } from "@cloudflare/containers";
import type { Fetcher, DurableObjectState, ExecutionContext } from "@cloudflare/workers-types"

export interface Env {
    CORE_CONTAINER: any;
    ASSETS: Fetcher;

    SUPABASE_KEY: string;
    DATABASE_URL: string;

    SEGMENTATION_WORKER_URL: string;
    MODAL_KEY: string;
    MODAL_SECRET: string;
    
    R2_ACCOUNT_ID: string;
    R2_ACCESS_KEY_ID: string;
    R2_SECRET_ACCESS_KEY: string;
    
    R2_PUBLIC_BASE_URL: string;
    BUCKET_NAME: string;
    SEGMENTATION_PROVIDER: string;
}

export class BackendCore extends Container {
    defaultPort = 8000;
    sleepAfter = "10m";

    constructor(ctx: DurableObjectState, env: Env) {
        super(ctx, env);

        this.envVars = {
            SUPABASE_KEY: env.SUPABASE_KEY,
            DATABASE_URL: env.DATABASE_URL,
            
            SEGMENTATION_WORKER_URL: env.SEGMENTATION_WORKER_URL,
            MODAL_SECRET: env.MODAL_SECRET,
            MODAL_KEY: env.MODAL_KEY,
            
            R2_ACCOUNT_ID: env.R2_ACCOUNT_ID,
            R2_ACCESS_KEY_ID: env.R2_ACCESS_KEY_ID,
            R2_SECRET_ACCESS_KEY: env.R2_SECRET_ACCESS_KEY,
            R2_PUBLIC_BASE_URL: env.R2_PUBLIC_BASE_URL,

            BUCKET_NAME: env.BUCKET_NAME,
            SEGMENTATION_PROVIDER: env.SEGMENTATION_PROVIDER,
        };
    }
}

export default {
    async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
        const url = new URL(request.url);
        console.log(`[Router] Routing request: ${request.method} ${url.pathname}`);

        if (url.pathname.startsWith("/api/")) {
            // Strip prefix if needed before passing to the container
            const containerInstance = getContainer(env.CORE_CONTAINER, "global");
            const modifiedRequest = new Request(url, request);
            return await containerInstance.fetch(modifiedRequest);
        }


        return env.ASSETS.fetch(request);
    },
};