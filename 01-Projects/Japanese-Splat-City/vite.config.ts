/// <reference types="vitest/config" />
import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    host: true,
    port: 5173,
    // Editor tools (write/edit) stage file replacements in sibling
    // `.scratch-*.tmpdir` directories, and headless-browser profiles keep
    // locked files (Cookies, LevelDB) open; watching either trips EBUSY and
    // kills the dev server watcher. Ignore them.
    watch: {
      ignored: [
        '**/.scratch-*',
        '**/.*.tmpdir',
        '**/.*.tmpdir/**',
        '**/.chrome-headless',
        '**/.chrome-headless/**',
        '**/.tmp-esbuild',
        '**/.tmp-esbuild/**',
      ],
    },
  },
  preview: {
    host: true,
    port: 4173,
  },
  build: {
    target: 'es2022',
    chunkSizeWarningLimit: 2500,
    sourcemap: false,
  },
  test: {
    environment: 'node',
    include: ['tests/**/*.test.ts'],
  },
});
