import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  plugins: [svelte()],
  base: '/aoe2table/',   // ← important: include the trailing slash
})


// import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
// import adapter from '@sveltejs/vite-plugin-svelte';

// /** @type {import('@sveltejs/kit').Config} */
// const config = {
//   kit: {
//     adapter: adapter(),
//     paths: {
//       base: process.env.BASE_PATH || ''   // or hardcode '/repo-name'
//     }
//   },
//   // Consult https://svelte.dev/docs#compile-time-svelte-preprocess
//   // for more information about preprocessors
//   preprocess: vitePreprocess(),
// };

// export default config;

// // import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
// // export default {
// //   // Consult https://svelte.dev/docs#compile-time-svelte-preprocess
// //   // for more information about preprocessors
// //   preprocess: vitePreprocess(),
// // }
