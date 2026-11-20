<script setup lang="ts">
withDefaults(defineProps<{ size?: number }>(), { size: 44 });
</script>
<template>
  <svg
    class="emblem"
    :width="size"
    :height="size"
    viewBox="0 0 64 64"
    aria-hidden="true"
    focusable="false"
  >
    <defs>
      <linearGradient id="emblem-g" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#e4c27a" />
        <stop offset="1" stop-color="#b08636" />
      </linearGradient>
    </defs>
    <circle cx="32" cy="32" r="30" fill="none" stroke="url(#emblem-g)" stroke-width="2.4" />
    <circle cx="32" cy="32" r="25" fill="none" stroke="url(#emblem-g)" stroke-width="0.9" stroke-dasharray="2 2.6" />
    <path
      d="M32 17 14 26l18 9 18-9z"
      fill="url(#emblem-g)"
    />
    <path
      d="M21 30.5v8.5c5.5 5 16.5 5 22 0v-8.5L32 36z"
      fill="none"
      stroke="url(#emblem-g)"
      stroke-width="2.4"
      stroke-linejoin="round"
    />
    <path d="M48 26v11" stroke="url(#emblem-g)" stroke-width="2" stroke-linecap="round" />
    <circle cx="48" cy="39" r="2" fill="url(#emblem-g)" />
  </svg>
</template>
