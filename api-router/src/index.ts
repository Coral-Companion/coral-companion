import { Container, getContainer } from "@cloudflare/containers";
import type { Fetcher } from "@cloudflare/workers-types"

export interface Env {
    CORE_CONTAINER: any;
    ASSETS: Fetcher;
    SEGMENTATION_CONTAINER: {
        fetch(request: Request | string, init?: RequestInit): Promise<Response>;
    };
}

export class BackendCore extends Container {
    defaultPort = 8080;
    sleepAfter = "10m";
}
/*export class BackendSegmentationWorker extends Container {
    defaultPort = 8080;
    sleepAfter = "2m";
}*/

export default {
    async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
        const url = new URL(request.url);
        console.log(`[Router] Routing request: ${request.method} ${url.pathname}`);
        
        /*if (url.pathname.startsWith("/api/segment")) {
            return env.SEGMENTATION_CONTAINER.fetch(request);
            }*/

        if (url.pathname.startsWith("/api/")) {
            // Strip prefix if needed before passing to the container
            const containerInstance = getContainer(env.CORE_CONTAINER, "global");
            const modifiedRequest = new Request(url, request);
            return await containerInstance.fetch(modifiedRequest);
        }


        return env.ASSETS.fetch(request);
    },
};