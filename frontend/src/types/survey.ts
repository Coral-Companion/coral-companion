import { DiveSite } from "./diveSite";

export type Survey = {
    id: string;
    name: string | null;
    diveSite: string;
    timestamp: string;
    observationCount: number;
};