import { createApp } from 'vue'
import App from './App.vue'
import './styles/tailwind.css'
import { createPinia } from "pinia";
import router from "./router";
import "./plugins/echarts";


if (import.meta.env.VITE_UMAMI_SCRIPT_SOURCE) {
    const script = document.createElement('script')
    script.defer = true
    script.src = import.meta.env.VITE_UMAMI_SCRIPT_SOURCE
    script.dataset.websiteId = import.meta.env.VITE_UMAMI_ID
    document.head.appendChild(script)
}

createApp(App)
    .use(createPinia())
    .use(router)
    .mount('#app');
