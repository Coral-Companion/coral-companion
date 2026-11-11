<template>
  <!--
    <main class="h-fit min-h-full bg-coral-bg p-5 text-coral-primary-text xl:overflow-hidden mx-auto flex max-w-[1800px] flex-col">
  -->
  <main class="flex flex-col xl:flex-row xl:h-full min-h-0 bg-coral-bg p-3 text-coral-primary-text">
    <div class="grid flex-1 gap-4 xl:grid-cols-[3fr_2fr]">
      <!-- Image / segmentation panel -->
      <section class="flex flex-col overflow-hidden rounded border border-coral-surface-border bg-coral-surface">
        <div
          class="grid grid-cols-[1fr_1fr_1fr] items-center gap-4 border-b border-coral-surface-border px-4 py-3 text-xs">

          <div class="mr-auto">
            <button class="px-3 py-1.5 rounded border border-coral-button-border hover:bg-coral-button-hover"
              @click="picker?.click()">
              New Image
            </button>
            <input ref="picker" class="hidden" type="file" accept="image/*" @change="picked" />
          </div>

          <div class="flex flex-col items-center gap-3 text-coral-secondary-text">
            <label>
              Opacity:
              <span class="text-coral-primary-text">
                <b>
                  {{ Math.round(opacity * 100) }}%
                </b>
              </span>
            </label>
            <input :disabled="loading.segment || loading.identify || segments?.length == 0"
                  v-model.number="opacity" type="range" min="0" max="1" step=".05"
                  class="w-20 accent-coral-primary disabled:opacity-40" />
          </div>

          <div class="flex flex-col items-center ml-auto gap-3">
            <span class="text-coral-secondary-text">
              <b class="text-coral-primary-text">
                {{ selected.size }}
              </b>
              of
              {{ segments.length }}
              segments selected
            </span>

            <button :disabled="!selected.size || loading.identify"
              class="px-3 py-2 rounded border border-coral-button-border hover:bg-coral-button-hover disabled:opacity-40"
              @click="identify">
              {{
                loading.identify
                  ? "Finding candidates..."
                  : "Find coral colony for selection"
              }}
            </button>
          </div>

        </div>

        <div class="relative flex min-h-0 flex-1 items-center justify-center bg-coral-surface p-3" @dragover.prevent
          @drop.prevent="dropped">
          <CoralImageViewer v-if="imageUrl" :image-src="imageUrl" :segments="segments" :selected="selected"
            :opacity="opacity" @toggle="toggle" />

          <div v-else class="text-center">
            <p class="text-base">
              Drop an image here
            </p>

            <p class="mt-2 text-xs text-coral-secondary-text">
              Segmentation overlays appear after segmentation results are
              calculated.
            </p>

            <button class="mt-4 rounded bg-coral-primary px-4 py-2 text-sm font-semibold text-coral-primary-button-text"
              @click="picker?.click()">
              Browse image
            </button>
          </div>

          <div v-if="loading.segment || loading.identify"
            class="absolute inset-0 flex items-center justify-center bg-[#071116]/45">
            <div class="rounded border border-slate-700 bg-[#0d1b21] px-5 py-4 text-center">
              <i
                class="mx-auto block h-5 w-5 rounded-full border-2 border-coral-primary border-t-transparent animate-spin"></i>

              <p class="mt-2 text-sm">
                Segmenting image
              </p>

              <p class="text-xs text-coral-secondary-text">
                This may take several minutes.
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- 
        <div class="flex min-h-0 flex-col">
      -->
      <div class="shrink-0 h-full flex flex-col min-h-0">
        <SurveySelector v-model="selectedSurvey" class="mb-2" />
        <CandidatesPanel :image-url="imageUrl" :candidates="candidates" :selected-count="selected.size"
          :loading-segment="loading.segment" :loading-identify="loading.identify" :loading-confirm="loading.confirm"
          @confirm="confirm" :selected-survey="selectedSurvey" />
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import {
  reactive,
  ref,
} from "vue";

import { useNotificationStore } from "../stores/notification";
import { useCoralDataStore } from "../stores/coral";

import CoralImageViewer from "../components/observation/CoralImageViewer.vue";
import CandidatesPanel from "../components/observation/CandidatesPanel.vue";
import SurveySelector from "../components/observation/SurveySelector.vue";

import segmentation from "../services/segmentationService";
import observationService from "../services/observationService";

import type { Segment } from "../types/segment";
import type { CoralCandidate } from "../types/api";
import type { Survey } from "../types/survey.js";

const picker = ref<HTMLInputElement>();

const image = ref<File>();
const imageUrl = ref("");

const segments = ref<Segment[]>([]);
const selected = ref(new Set<number>());

const candidates = ref<CoralCandidate[]>([]);

const opacity = ref(0.55);

const error = ref("");
const info = ref("");
const success = ref("");

const loading = reactive({
  segment: false,
  identify: false,
  confirm: false,
});

const selectedSurvey = ref<Survey | null>(null);
const notificationStore = useNotificationStore();
const coralDataStore = useCoralDataStore();

const toggle = (id: number) => {
  const next = new Set(selected.value);

  next.has(id)
    ? next.delete(id)
    : next.add(id);

  selected.value = next;
};

const updateCandidates = (
  nextCandidates: CoralCandidate[],
) => {
  candidates.value = nextCandidates;
};

const upload = async (
  file: File,
) => {
  image.value = file;
  imageUrl.value = URL.createObjectURL(file);

  segments.value = [];
  selected.value = new Set();
  candidates.value = [];

  loading.segment = true;

  notificationStore.info("Calculating Segments...");

  try {
    const uploadResult = await segmentation.segmentImage(file);

    segments.value = uploadResult.segments;

    updateCandidates(uploadResult.observationCandidates);

    notificationStore.success("Segments Calculated");
  } catch (e) {
    notificationStore.error(e instanceof Error ? e.message : "Segmentation failed."
    );
  } finally {
    loading.segment = false;
  }
};

const picked = (
  e: Event,
) => {
  const file =
    (e.target as HTMLInputElement)
      .files?.[0];

  if (file) {
    void upload(file);
  }
};

const dropped = (
  e: DragEvent,
) => {
  const file =
    e.dataTransfer?.files[0];

  if (file) {
    void upload(file);
  }
};

const identify = async () => {
  if (!image.value) {
    return;
  }

  loading.identify = true;

  notificationStore.info(`Finding Candidates for ${selected.value.size} Segments...`);

  try {
    const result =
      await observationService.identifyCoralBySegments(
        segments.value.filter(
          (segment) =>
            selected.value.has(segment.id),
        ),
        image.value,
      );

    updateCandidates(
      result.candidates ?? [],
    );

    notificationStore.success(`Found ${result.candidates?.length ?? 0} Candidates`);
  } catch (e) {
    notificationStore.error(e instanceof Error ? e.message : "Could not find matches.");
  } finally {
    loading.identify = false;
  }
};

type ConfirmPayload = {
  selectedCandidateId: string | null;
  diveSite: string;
  coralName: string;
};

const confirm = async (payload: ConfirmPayload) => {
  if (!image.value) {
    return;
  }

  loading.confirm = true;

  const previousCandidates = candidates.value;
  const previousSelected = selected.value;

  notificationStore.info("Saving Observation...");

  try {
    candidates.value = [];
    selected.value = new Set();

    await observationService.confirmCoral({
      image: image.value,
      selectedSegments: segments.value.filter((segment) => previousSelected.has(segment.id)),
      selectedCandidateId: payload.selectedCandidateId,
      diveSite: payload.diveSite,
      coralName: payload.coralName,
      surveyId: coralDataStore.getSelectedSurveyId(),
    });

    notificationStore.success(`Observation for ${payload.coralName} has been successfully saved`);
  } catch (e) {
    notificationStore.error(e instanceof Error ? e.message : "Could not save Observation");
    candidates.value = previousCandidates;
    selected.value = previousSelected;
  } finally {
    loading.confirm = false;
  }
};
</script>