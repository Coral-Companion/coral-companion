<template>
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" @click.self="cancel">
        <div class="w-full max-w-md rounded border border-slate-700 bg-[#0b181e] shadow-2xl">
            <!-- Header -->
            <div class="flex items-center justify-between border-b border-slate-800 px-5 py-4">
                <div>
                    <h2 class="text-base font-semibold text-coral-primary-text">
                        New Survey
                    </h2>

                    <p class="mt-1 text-xs text-coral-secondary-text">
                        Create a session for recording coral observations.
                    </p>
                </div>

                <button type="button" class="text-xl text-coral-secondary-text hover:text-coral-primary-text" aria-label="Close"
                    @click="cancel">
                    ✕
                </button>
            </div>

            <!-- Form -->
            <form class="space-y-4 p-5" @submit.prevent="create">
                <!-- Name -->
                <label class="block text-sm">
                    <span class="text-coral-primary-text">
                        Name
                        <span class="text-xs text-coral-secondary-text">
                            (optional)
                        </span>
                    </span>

                    <input v-model="name" type="text" placeholder="Morning Survey Interns"
                        class="mt-1 w-full rounded border border-slate-700 bg-coral-bg p-2 text-sm text-coral-primary-text placeholder:text-coral-secondary-text focus:border-coral-primary focus:outline-none" />
                </label>

                <!-- Dive site -->
                <label class="block text-sm">
                    <span class="text-coral-primary-text">
                        Dive site
                    </span>

                    <select v-model="diveSite"
                        class="mt-1 block w-full rounded border border-slate-700 bg-coral-bg p-2 text-sm text-coral-primary-text focus:border-coral-primary focus:outline-none">
                        <option v-for="site in diveSites" :key="site" :value="site">
                            {{ site }}
                        </option>
                    </select>
                </label>

                <!-- Timestamp -->
                <label class="block text-sm">
                    <span class="text-coral-primary-text">
                        Date and time
                    </span>

                    <input v-model="timestamp" type="datetime-local" class="mt-1 w-full rounded border border-slate-700 bg-[#091419] p-2 text-sm 
                        text-coral-primary-text focus:border-coral-primary focus:outline-none
                        dark:[color-scheme:dark] [&-webkit-calendar-picker-indicator]:dark:invert" />
                </label>

                <!-- Error -->
                <p v-if="error" class="rounded border border-red-400/40 bg-red-500/10 px-3 py-2 text-sm text-red-300">
                    {{ error }}
                    </p>

                    <!-- Actions -->
                    <div class="flex justify-end gap-2 border-t border-slate-800 pt-4">
                        <button type="button"
                            class="rounded border border-slate-700 px-4 py-2 text-sm text-coral-primary-text hover:bg-slate-800"
                            :disabled="loading" @click="cancel">
                            Cancel
                        </button>

                        <button type="submit"
                            class="rounded bg-coral-primary px-4 py-2 text-sm font-semibold text-[#062126] disabled:opacity-40"
                            :disabled="loading || !diveSite">
                            {{ loading ? "Creating..." : "Create survey" }}
                        </button>
                    </div>
            </form>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Survey } from "../../types/survey";

type Props = {
    diveSites: string[];
    initialDiveSiteId?: string | null;
};

const props = withDefaults(
    defineProps<Props>(),
    {
        initialDiveSiteId: null,
    },
);

const emit = defineEmits<{
    cancel: [];

    create: [
        payload: Survey,
    ];
}>();

const name = ref("");

const diveSite = ref(
    props.initialDiveSiteId ??
    props.diveSites[0] ??
    "",
);

const getCurrentDateTimeLocal = () => {
    const now = new Date();

    const offset =
        now.getTimezoneOffset();

    const localDate = new Date(
        now.getTime() -
        offset * 60 * 1000,
    );

    return localDate
        .toISOString()
        .slice(0, 16);
};

const timestamp = ref(
    getCurrentDateTimeLocal(),
);

const loading = ref(false);

const error = ref("");

const cancel = () => {
    if (loading.value) {
        return;
    }

    emit("cancel");
};

const create = () => {
    error.value = "";

    if (!diveSite) {
        error.value =
            "Please select a dive site.";

        return;
    }

    const localDate = new Date(timestamp.value);
    emit("create", {
        id: "",
        name: name.value.trim() || null,
        diveSite: diveSite.value,
        timestamp: localDate.toISOString(),
        observationCount: 0
    });
};

</script>