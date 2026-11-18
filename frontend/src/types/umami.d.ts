export interface UmamiEventData {
    [key: string]: string | number | boolean;
}

export interface UmamiExceptionOptions {
    /** Overrides data-release for this error (100-character limit) */
    release?: string;
    /** Overrides data-environment for this error (50-character limit) */
    environment?: string;
    /** Key-value pairs of strings shown on the occurrence (up to 20 tags) */
    tags?: Record<string, string>;
    /** Up to 5 strings used to group the error into an issue, replacing automatic grouping */
    fingerprint?: string[];
}

export interface UmamiTracker {
    track: (
        eventName?: string | Record<string, unknown> | ((props: Record<string, unknown>) => Record<string, unknown>),
        eventData?: UmamiEventData | {}
    ) => Promise<string> | void;
    identify: (
        idOrData: string | Record<string, unknown>,
        data?: Record<string, unknown>
    ) => Promise<string> | void;
    captureException: (
        error: unknown,
        options?: UmamiExceptionOptions
    ) => void;
}

declare global {
    interface Window {
        umami: UmamiTracker;
    }
}
