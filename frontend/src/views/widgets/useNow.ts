import { onBeforeUnmount, onMounted, ref } from "vue";

/** 每隔 interval 毫秒更新一次的当前时间，用于倒计时等展示。 */
export function useNow(interval = 30_000) {
  const now = ref(Date.now());
  let timer: number | undefined;
  onMounted(() => {
    timer = window.setInterval(() => (now.value = Date.now()), interval);
  });
  onBeforeUnmount(() => window.clearInterval(timer));
  return now;
}
