<template>
    <aside
        class="flex h-full min-h-0 flex-col overflow-hidden rounded border border-coral-surface-border bg-coral-surface">
        <!-- Candidate controls -->
        <div class="border-b border-slate-800 p-4">
            <h2 class="text-sm font-semibold">
                Candidates
            </h2>

            <p class="mt-1 text-xs text-coral-secondary-text">
                Compare uploaded image with past observations
            </p>

            <div class="mt-3 grid grid-cols-2 gap-2 text-xs">

                <input v-model="name"
                    class="w-full rounded border border-coral-raised-border bg-coral-input p-2 text-coral-primary-text"
                    placeholder="Enter New Coral Colony Name" />

                <button :disabled="!selectedCount || loadingConfirm"
                    class="rounded bg-coral-primary text-xs px-3 py-1.5 font-semibold text-coral-primary-button-text disabled:opacity-40"
                    @click="confirm">
                    {{
                        loadingConfirm
                            ? "Saving..."
                            : active
                                ? "Confirm match"
                                : "Save as new"
                    }}
                </button>
            </div>

            <button v-if="active" class="mt-2 text-xs text-teal-300" @click="clickDeselectCandidate">
                Deselect Candidate
            </button>
        </div>

        <!-- Candidate list -->
        <div class="min-h-0 flex-1 overflow-y-auto p-3">
            <Spinner v-if="loadingSegment || loadingIdentify" text="Calculating possible matches..." />

            <p v-else-if="!imageUrl" class="h-full flex justify-center items-center text-xs text-coral-secondary-text">
                Upload an image to begin comparison.
            </p>

            <p v-else-if="!coralObservations.length" class="h-full flex justify-center items-center text-xs text-coral-secondary-text">
                No matching colonies found. You can save this observation as a new
                colony.
            </p>

            <button v-for="coralObservation in coralObservations" v-else :key="coralObservation.coralName"
                class="mb-1 ml-1 w-full overflow-hidden rounded border text-left" :class="activeId === coralObservation.coralName
                    ? 'border-coral-primary bg-coral-primary-bg'
                    : 'border-coral-raised-border bg-coral-raised'
                    " @click="selectCandidate(coralObservation.coralName)">
                <div class="mt-2 flex ">
                    <span class="p-2 text-sm font-semibold">
                        Coral {{ coralObservation.coralName }}
                    </span>

                    <div v-if="hasHighSimilarity(coralObservation.candidates)"
                        class="ml-3 inline-flex items-center rounded bg-coral-primary-bg px-1.5 text-xs font-medium">
                        <svg fill="#ffffff" width="24px" height="24px" viewBox="0 0 24 24"
                            xmlns="http://www.w3.org/2000/svg">
                            <path
                                d="M21 4h-3V3a1 1 0 0 0-1-1H7a1 1 0 0 0-1 1v1H3a1 1 0 0 0-1 1v3a4 4 0 0 0 4 4h1.54A6 6 0 0 0 11 13.91V16h-1a3 3 0 0 0-3 3v2a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-2a3 3 0 0 0-3-3h-1v-2.09A6 6 0 0 0 16.46 12H18a4 4 0 0 0 4-4V5a1 1 0 0 0-1-1M6 10a2 2 0 0 1-2-2V6h2v2a6 6 0 0 0 .35 2Zm8 8a1 1 0 0 1 1 1v1H9v-1a1 1 0 0 1 1-1Zm2-10a4 4 0 0 1-8 0V4h8Zm4 0a2 2 0 0 1-2 2h-.35A6 6 0 0 0 18 8V6h2Z" />
                        </svg>

                        <span class="ml-1">
                            Great Match
                        </span>
                    </div>
                </div>

                <div class="grid grid-cols-3">
                    <div v-for="candidate in coralObservation.candidates" :key="candidate.id" class="mb-2 text-center">
                        <div class="flex h-[150px] items-center justify-center">
                            <img v-if="candidate.imageUrl" :src="candidate.imageUrl"
                                class="h-full w-full object-contain mix-blend-screen" />

                            <span v-else class="text-xs text-coral-primary-text">
                                No preview
                            </span>
                        </div>

                        <div class="text-xs">
                            <p class="text-teal-300">
                                {{ similarityLabel(candidate.visualSimilarity) }}
                            </p>

                            <p class="text-coral-secondary-text">
                                <Date :timestamp="candidate.surveyDate" />
                            </p>
                        </div>
                    </div>
                </div>
            </button>
        </div>
    </aside>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useNotificationStore } from "../../stores/notification";
import type { CoralCandidate, CoralObservations} from "../../types/api";
import { Survey } from "../../types/survey";
import { format } from "date-fns";
import Spinner from "../utils/Spinner.vue";
import Date from "../utils/Date.vue";

type Props = {
    imageUrl: string;
    candidates: CoralCandidate[];
    selectedCount: number;
    loadingSegment: boolean;
    loadingIdentify: boolean;
    loadingConfirm: boolean;
    selectedSurvey: Survey | null;
};

const props = defineProps<Props>();
const emit = defineEmits<{
    confirm: [payload: {
        selectedCandidateId: string | null;
        diveSite: string;
        coralName: string;
    }]}>();

const name = ref("");
const activeId = ref("");
const notificationStore = useNotificationStore();

const coralObservations = computed<CoralObservations[]>(() => {
    const grouped = Object.groupBy(props.candidates, (candidate: CoralCandidate) => candidate.coralName);

    return Object.entries(grouped).map(
        ([coralName, candidates]) => ({ coralName, candidates: candidates ?? [] }));
});

const active = computed(() =>
    coralObservations.value.find(
        (coralObservation) =>
            coralObservation.coralName === activeId.value,
    ),
);

const selectCandidate = (coralName: string) => {
    if (activeId.value === coralName) {
        window.umami.track("candidate-deselect-candidate-click");
        deselectCandidate();
        return;
    }
    
    window.umami.track("candidate-select");
    activeId.value = coralName;
    name.value = coralName;
};

const deselectCandidate = () => {
    activeId.value = "";
    name.value = "";
};

const clickDeselectCandidate = () => {
    window.umami.track("candidate-deselect-link-click");
    deselectCandidate();
};

const confirm = () => {
    if (name.value.length == 0) {
        notificationStore.error("Coral name must not be empty");
        return;
    }
    emit("confirm", {
        selectedCandidateId: activeId.value || null,
        diveSite: props.selectedSurvey.diveSite,
        coralName: name.value,
    });
    activeId.value = '';
};


const hasHighSimilarity = (
    candidates: CoralCandidate[],
) => {
    return candidates.some(
        (candidate) =>
            candidate.visualSimilarity >= 0.95,
    );
};

const similarityLabel = (
    similarity: number,
) => {
    if (similarity === 1) {
        return "Identical";
    } else if (similarity >= 0.95) {
        return "Very strong match";
    } else if (similarity >= 0.90) {
        return "Strong match";
    } else if (similarity >= 0.85) {
        return "Possible match";
    } else if (similarity >= 0.70) {
        return "Weak match";
    } else {
        return "Low similarity";
    }
};
</script>