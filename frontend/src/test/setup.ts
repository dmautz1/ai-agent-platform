import '@testing-library/jest-dom'
import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// Extend Vitest expect with Jest DOM matchers
expect.extend(matchers)

// Cleanup after each test case
afterEach(() => {
  cleanup()
})

// Mock window.matchMedia for responsive tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Advanced Observer Mocking for Radix UI and Floating UI compatibility
const createMockObserver = () => {
  return class MockObserver {
    observe = vi.fn()
    unobserve = vi.fn()
    disconnect = vi.fn()
    takeRecords = vi.fn(() => [])
    
    constructor() {
      // Accept any constructor arguments without failing
    }
  }
}

// Create specific observer mocks
const MockResizeObserver = createMockObserver()
const MockIntersectionObserver = createMockObserver()
const MockMutationObserver = createMockObserver()

// Install mocks globally and on window
global.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver
global.IntersectionObserver = MockIntersectionObserver as unknown as typeof IntersectionObserver
global.MutationObserver = MockMutationObserver as unknown as typeof MutationObserver

Object.defineProperty(window, 'ResizeObserver', {
  writable: true,
  configurable: true,
  value: MockResizeObserver,
})

Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  configurable: true,
  value: MockIntersectionObserver,
})

Object.defineProperty(window, 'MutationObserver', {
  writable: true,
  configurable: true,
  value: MockMutationObserver,
})

// Mock Element methods that observers might need
Object.defineProperty(Element.prototype, 'scrollIntoView', {
  value: vi.fn(),
  writable: true,
})

// Mock scrollTo
Object.defineProperty(window, 'scrollTo', {
  value: vi.fn(),
  writable: true,
})

// Mock Radix UI Pointer Events and other APIs that don't work in test environment
Object.defineProperty(HTMLElement.prototype, 'hasPointerCapture', {
  value: vi.fn(() => false),
  writable: true,
})

Object.defineProperty(HTMLElement.prototype, 'setPointerCapture', {
  value: vi.fn(),
  writable: true,
})

Object.defineProperty(HTMLElement.prototype, 'releasePointerCapture', {
  value: vi.fn(),
  writable: true,
})

// Mock getBoundingClientRect for layout calculations
Object.defineProperty(HTMLElement.prototype, 'getBoundingClientRect', {
  value: vi.fn(() => ({
    bottom: 0,
    height: 0,
    left: 0,
    right: 0,
    top: 0,
    width: 0,
    x: 0,
    y: 0,
  })),
  writable: true,
})

// Mock getComputedStyle
Object.defineProperty(window, 'getComputedStyle', {
  value: vi.fn(() => ({
    getPropertyValue: vi.fn(() => ''),
  })),
  writable: true,
})

// Mock requestAnimationFrame and cancelAnimationFrame
Object.defineProperty(window, 'requestAnimationFrame', {
  value: vi.fn((cb) => setTimeout(cb, 0)),
  writable: true,
})

Object.defineProperty(window, 'cancelAnimationFrame', {
  value: vi.fn(),
  writable: true,
})

// Suppress console errors for known test issues
const originalError = console.error
console.error = (...args: unknown[]) => {
  // Suppress Radix UI pointer capture warnings and observer warnings
  if (
    typeof args[0] === 'string' && 
    (args[0].includes('setPointerCapture') || 
     args[0].includes('releasePointerCapture') ||
     args[0].includes('hasPointerCapture') ||
     args[0].includes('ResizeObserver') ||
     args[0].includes('MutationObserver') ||
     args[0].includes('IntersectionObserver'))
  ) {
    return
  }
  originalError.apply(console, args)
} 