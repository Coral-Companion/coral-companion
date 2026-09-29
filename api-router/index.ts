import { Container, getContainer } from "@cloudflare/containers";

export interface Env {
    CORE_CONTAINER: {
        fetch(request: Request | string, init?: RequestInit): Promise<Response>;
    };
    SEGMENTATION_CONTAINER: {
        fetch(request: Request | string, init?: RequestInit): Promise<Response>;
    };
}

export default {
    async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
        const url = new URL(request.url);

        if (url.pathname.startsWith("/api/segment")) {
            return env.SEGMENTATION_CONTAINER.fetch(request);
        }

        if (url.pathname.startsWith("/api/")) {
            // Strip prefix if needed before passing to the container
            const modifiedRequest = new Request(url, request);
            return env.CORE_CONTAINER.fetch(modifiedRequest);
        }


        return new Response("Not Found", { status: 404 });
    },
};