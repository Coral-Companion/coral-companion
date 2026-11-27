<template>
  <div ref="container" class="relative">
    <div class="flex flex-col grid grid-cols-1 sm:grid-cols-[1fr_40px]
          hover:opacity-90"
          :class="{ ' opacity-40' : !open, ' opacity-90' : open }"
          >
      <button type="button" :disabled="loading || !image" 
          class="px-3 py-2 text-xs text-coral-primary-text
          rounded border border-coral-button-border 
          border-r-0 rounded-r-none
          bg-coral-overlay hover:bg-coral-button-hover"
          @click="runSegmentation">
          {{ loading ? "Segmenting..." : "Advanced segmentation" }}
      </button>
      <button type="button" :disabled="loading || !image" @click="toggleDropdown" class="px-3 py-2 text-xs font-medium text-coral-primary-text
          rounded border border-coral-button-border rounded-l-none
          bg-coral-overlay hover:bg-coral-button-hover">
        <span class="text-coral-secondary-text transition-transform" :class="open ? 'rotate-180' : ''">▼</span>
      </button>
    </div>

    <aside v-if="open"
        class="absolute z-40 w-full bottom-full overflow-hidden
        rounded border border-b-0 rounded-b-none border-coral-surface-border
        bg-coral-overlay shadow-xl p-3 opacity-90">
      <label class="block mb-1 text-xs text-coral-primary-text">Layers: {{ layers }}</label>
      <input type="range" v-model.number="layers" min="0" max="5" :disabled="loading" class="w-full mb-3 rounded border border-coral-raised-border bg-coral-input
        p-2 text-coral-primary-text accent-coral-primary" />

      <label class="block mb-1 text-xs text-coral-primary-text">Points per Side: {{ pointsPerSide }}</label>
      <input type="range" v-model.number="pointsPerSide" min="10" max="100" step="10" :disabled="loading" class="w-full mb-3 rounded border border-coral-raised-border bg-coral-input
        p-2 text-coral-primary-text accent-coral-primary" />

      <label class="block mb-1 text-xs text-coral-primary-text">Points per Batch: {{ pointsPerBatch }}</label>
      <input type="range" v-model.number="pointsPerBatch" min="32" max="512" step="32" :disabled="loading" class="w-full rounded border border-coral-raised-border bg-coral-input
        p-2 text-coral-primary-text accent-coral-primary" />
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ref, onBeforeUnmount, onMounted } from "vue";
import segmentation from "@/services/segmentationService";
import { useNotificationStore } from "@/stores/notification";
import type { Segment } from "@/types/segment";
import type { CoralCandidate } from "@/types/api";

const props = defineProps<{
  image: File | null;
}>();

const emit = defineEmits<{
  done: [segments: Segment[], candidates: CoralCandidate[]];
  loading: [isLoading: boolean];
}>();

const container = ref<HTMLElement | null>(null);
const layers = ref(0);
const pointsPerSide = ref(10);
const pointsPerBatch = ref(32);
const open = ref(false);
const loading = ref(false);
const notificationStore = useNotificationStore();

const toggleDropdown = () => {
  open.value = !open.value;
};

const runSegmentation = async () => {
  if (!props.image || loading.value) return;

  loading.value = true;
  emit("loading", true);
  notificationStore.info("Re-running Segmentation...");
  window.umami.track("observation-repeat-segmentation", {
    "layers": layers.value,
    "pointsPerSide": pointsPerSide.value,
    "pointsPerBatch": pointsPerBatch.value
  });

  try {
    const result = await segmentation.segmentImage(
      props.image,
      layers.value,
      pointsPerSide.value,
      pointsPerBatch.value,
    );
    emit("done", result.segments, result.observationCandidates);
    notificationStore.success("Segments Recalculated");
  } catch (e) {
    notificationStore.error(e instanceof Error ? e.message : "Segmentation failed.");
    window.umami.captureException(e);
  } finally {
    loading.value = false;
    emit("loading", false);
    open.value = false;
  }
};

const handleClickOutside = (event: MouseEvent) => {
  if (container.value && !container.value.contains(event.target as Node)) {
    open.value = false;
  }
};

onMounted(() => {
  document.addEventListener("click", handleClickOutside);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleClickOutside);
});
</script>
