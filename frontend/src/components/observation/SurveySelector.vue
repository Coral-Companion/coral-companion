<template>
    <div ref="container" class="relative">

        <!-- Selector button -->
        <button type="button" class="flex w-full items-center justify-between rounded 
            border border-coral-surface-border bg-coral-input p-2 text-left 
            hover:border-slate-600 disabled:cursor-not-allowed disabled:opacity-50" :disabled="loading"
            @click="toggleDropdown">
            <div class="grid grid-cols-[3fr_1fr] w-full text-xs text-coral-primary-text font-semibold m-1">
                <span v-if="selectedSession">
                    <span class="text-coral-secondary-text font-normal">Survey </span>
                    <Date :timestamp="selectedSession.timestamp" /> · {{ selectedSession.diveSite }}
                    <span v-if="selectedSession.name"> · {{ selectedSession.name }}</span>
                </span>

                <span v-if="selectedSession" class="ml-auto text-coral-secondary-text font-normal">
                    {{ selectedSession.observationCount }}
                    observation{{
                        selectedSession.observationCount === 1
                            ? ""
                            : "s"
                    }}
                </span>


                <p v-else class="text-xs text-coral-secondary-text">
                    {{
                        loading
                            ? "Loading Surveys..."
                            : "Select a Survey"
                    }}
                </p>
            </div>

            <span class="ml-3 text-coral-secondary-text transition-transform" :class="open ? 'rotate-180' : ''">
                ▼
            </span>
        </button>

        <!-- Error -->
        <p v-if="error" class="mt-1 text-xs text-red-400">
            {{ error }}
        </p>

        <!-- Dropdown -->
        <div v-if="open"
            class="absolute z-40 mt-1 w-full overflow-hidden rounded border border-coral-surface-border bg-coral-surface shadow-xl">
            <!-- Loading -->
            <div v-if="loading" class="px-3 py-4 text-center text-xs text-coral-secondary-text bg-coral-raised">
                Loading sessions...
            </div>

            <!-- Existing sessions -->
            <div v-else-if="sessions.length" class="max-h-72 overflow-y-auto">
                <button v-for="session in sessions" :key="session.id" type="button" class="w-full border-b border-coral-raised-border
                    px-3 py-2 text-left transition 
                    hover:bg-coral-primary-bg" :class="session.id === selectedSession?.id
                        ? 'bg-coral-primary-bg'
                        : 'bg-coral-raised'
                        " @click="clickSurvey(session)">
                    <div class="grid grid-cols-[3fr_1fr] w-full text-xs text-coral-primary-text font-semibold m-1">
                        <span v-if="selectedSession">
                            <span class="text-coral-secondary-text font-normal">Survey </span>
                            <Date :timestamp="session.timestamp" /> · {{ session.diveSite }}
                            <span v-if="session.name"> · {{ session.name }}</span>
                        </span>

                        <span v-if="session" class="ml-auto text-coral-secondary-text font-normal">
                            {{ session.observationCount }}
                            observation{{
                                session.observationCount === 1
                                    ? ""
                                    : "s"
                            }}
                        </span>
                    </div>
                </button>
            </div>

            <!-- Empty state -->
            <p v-else class="px-3 py-4 text-center text-xs text-coral-secondary-text">
                No Surveys yet.
            </p>

            <!-- Create new session -->
            <button type="button" class="w-full border-coral-raised-border px-3 py-3 text-left text-xs font-medium text-teal-300 transition
                bg-coral-raised hover:bg-coral-primary-bg" @click="openCreateDialog">
                ＋ Create new Survey
            </button>
        </div>

        <!-- Create dialog -->
        <CreateSurveyDialog v-if="showCreateDialog" :dive-sites="diveSites" :initial-dive-site-id="selectedSession?.diveSite
            " @cancel="showCreateDialog = false" @create="createSession" />
    </div>
</template>

<script setup lang="ts">
import {
    computed,
    onBeforeUnmount,
    onMounted,
    ref,
} from "vue";


import surveyService from "../../services/surveyService";
import { Survey } from "../../types/survey"
import CreateSurveyDialog from "./CreateSurveyDialog.vue";
import diveSiteService from "../../services/diveSiteService"
import { useNotificationStore } from "../../stores/notification";
import { useCoralDataStore } from "../../stores/coral";
import Date from "../utils/Date.vue";
import { format } from "date-fns";

type Props = {
    modelValue: Survey | null;
};

const props = defineProps<Props>();

const emit = defineEmits<{
    "update:modelValue": [
        session: Survey | null,
    ];
}>();

const container =
    ref<HTMLElement | null>(null);

const open = ref(false);
const loading = ref(false);
const error = ref("");
const showCreateDialog = ref(false);
const sessions = ref<Survey[]>([]);
const diveSites = ref<string[]>([]);
const selectedSession = computed(() => props.modelValue);
const notificationStore = useNotificationStore();
const coralDataStore = useCoralDataStore();

const toggleDropdown = () => {
    if (loading.value) {
        return;
    }
    open.value = !open.value;
};

const clickSurvey = (session: Survey) => {
    selectSurvey(session);
    window.umami.track("survey-select", { "survey": session });
};

const selectSurvey = (session: Survey) => {
    emit("update:modelValue", session);
    coralDataStore.selectSurvey(session);
    open.value = false;
};

const openCreateDialog = () => {
    open.value = false;
    showCreateDialog.value = true;
    window.umami.track("survey-creation-dialog-open");
};

const loadSessions = async () => {
    loading.value = true;
    error.value = "";

    try {
        sessions.value = await surveyService.getAll();
        if (sessions.value.length > 0) {
            selectSurvey(sessions.value[0]);
        }
    } catch (e) {
        if (e instanceof Error) {
            notificationStore.error(e.message);
        } else {
            notificationStore.error("Could not load Surveys.");
        }
    } finally {
        loading.value = false;
    }
};

const loadDiveSites = async () => {
    loading.value = true;
    error.value = "";

    try {
        diveSites.value =
            await diveSiteService.getAll();
    } catch (e) {
        error.value =
            e instanceof Error
                ? e.message
                : "Could not load dive sites.";
    } finally {
        loading.value = false;
    }
};

const createSession = async (payload: Survey) => {
    loading.value = true;
    error.value = "";

    try {
        const created = await surveyService.create(payload);
        window.umami.track("survey-create", { "survey": payload });
        showCreateDialog.value = false;

        // Automatically select the newly-created session.
        emit("update:modelValue", created);
        coralDataStore.selectSurvey(created);
    } catch (e) {
        error.value = e instanceof Error ? e.message : "Could not create Survey.";
        window.umami.captureException(e);
    } finally {
        loading.value = false;
    }
};

const handleClickOutside = (event: MouseEvent) => {
    if (container.value &&
        !container.value.contains(event.target as Node)) {
        open.value = false;
    }
};

onMounted(async () => {
    document.addEventListener(
        "click",
        handleClickOutside,
    );

    await loadSessions();
    await loadDiveSites();
});

onBeforeUnmount(() => {
    document.removeEventListener(
        "click",
        handleClickOutside,
    );
});
</script>