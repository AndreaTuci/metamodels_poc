import { defineConfig } from 'astro/config';
import vue from '@astrojs/vue';

export default defineConfig({
  output: 'hybrid', // Abilita il rendering dinamico per le pagine con getStaticPaths vuoto
  integrations: [vue()],
  server: {
    port: 3000,
    host: true
  }
});
