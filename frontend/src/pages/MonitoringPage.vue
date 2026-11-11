<template>
    <div class="flex flex-col xl:flex-row h-auto xl:h-full min-h-0 
        overflow-auto xl:overflow-hidden">

        <Sidebar
            :observations="observations" :loading-observations="loadingObservations"
            v-model:selectedObservationIds="selectedObservationIds" />

        <Workspace 
            :observations="selectedObservations"/>

    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { compareAsc } from "date-fns";

import Sidebar from "../components/monitoring/Sidebar.vue";
import Workspace from "../components/monitoring/Workspace.vue";
import observationService from "../services/observationService";
import { ObservationSummary } from "@/types/observationSummary"
import { useNotificationStore } from "@/stores/notification";
import { Survey } from "@/types/survey";
import surveyService from "@/services/surveyService.js";


const notificationStore = useNotificationStore();

const selectedObservationIds = ref<string[]>([]);
const observations = ref<ObservationSummary[]>([]);
const loadingObservations = ref<boolean>(false)
const selectedObservations = computed(() =>
observations.value
.filter((o: ObservationSummary) => selectedObservationIds.value.includes(o.id))
.sort((a, b) => compareAsc(a.observedAt, b.observedAt))
);

const loadObservationSummaries = async () => {
    loadingObservations.value = true;
    try {
        observations.value = await observationService.getObservationSummaries();
    } catch(e) {
        notificationStore.error("An error occurred while loading observations: " + e);
    }
    loadingObservations.value = false;
};

onMounted(async () => {
    await loadObservationSummaries();
});

</script>