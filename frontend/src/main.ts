import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import { router } from "./router";
import "./style.css";

async function main() {
  // 仅显式 mock 模式启用拦截，生产构建不会加载演示数据。
  if (import.meta.env.VITE_MOCK_API === "true") {
    const { worker } = await import("./api/mock");
    await worker.start({ onUnhandledFrame: "bypass" });
  }
  createApp(App).use(createPinia()).use(router).mount("#app");
}
void main();
