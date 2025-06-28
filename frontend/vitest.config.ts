/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    include: [
      'src/test/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
      'tests/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',
      exclude: [
        'node_modules/',
        'src/test/setup.ts',
        'src/test/utils.tsx',
        'tests/integration/api-integration-test-runner.ts',
        'src/vite-env.d.ts',
        'src/main.tsx',
        '**/*.d.ts',
        '**/*.config.{js,ts}',
        '**/dist/**',
        '**/build/**'
      ],
      include: [
        'src/**/*.{js,ts,jsx,tsx}',
        '!src/test/**',
        '!src/**/*.{test,spec}.{js,ts,jsx,tsx}'
      ],
      // Coverage thresholds specifically for ApiResponse-related code
      thresholds: {
        global: {
          branches: 75,
          functions: 75,
          lines: 75,
          statements: 75
        },
        // Higher thresholds for critical API response handling code
        'src/lib/api.ts': {
          branches: 90,
          functions: 90,
          lines: 90,
          statements: 90
        },
        'src/lib/types/api.ts': {
          branches: 85,
          functions: 85,
          lines: 85,
          statements: 85
        },
        // Ensure polling system has good coverage since it handles ApiResponse
        'src/lib/polling.ts': {
          branches: 85,
          functions: 85,
          lines: 85,
          statements: 85
        }
      },
      // Watermarks for coverage reporting colors
      watermarks: {
        statements: [75, 90],
        functions: [75, 90],
        branches: [75, 90],
        lines: [75, 90]
      }
    },
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
}) 