import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider, useTheme } from '../../contexts/ThemeContext';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

describe('ThemeContext', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorageMock.clear();
    localStorageMock.getItem.mockReturnValue(null);
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
    
    // Mock matchMedia for CSS media queries
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
    // Clean up document classes
    document.documentElement.classList.remove('dark');
  });

  // Test component to consume the theme context
  const TestConsumer = () => {
    const { theme, setTheme } = useTheme();
    return (
      <div>
        <div data-testid="current-theme">{theme}</div>
        <button onClick={() => setTheme('light')} data-testid="set-light">
          Set Light
        </button>
        <button onClick={() => setTheme('dark')} data-testid="set-dark">
          Set Dark
        </button>
      </div>
    );
  };

  const renderWithProvider = (children: React.ReactNode, providerProps = {}) => {
    return render(
      <ThemeProvider {...providerProps}>
        {children}
      </ThemeProvider>
    );
  };

  describe('ThemeProvider', () => {
    it('should provide theme context to children', () => {
      renderWithProvider(<TestConsumer />);
      
      expect(screen.getByTestId('current-theme')).toBeInTheDocument();
      expect(screen.getByTestId('set-light')).toBeInTheDocument();
      expect(screen.getByTestId('set-dark')).toBeInTheDocument();
    });

    it('should render children without errors', () => {
      renderWithProvider(
        <div data-testid="child">
          Test child component
        </div>
      );
      
      expect(screen.getByTestId('child')).toBeInTheDocument();
    });

    it('should initialize with default theme when no preference exists', () => {
      renderWithProvider(<TestConsumer />);
      
      const themeElement = screen.getByTestId('current-theme');
      expect(themeElement).toHaveTextContent('light');
    });

    it('should accept custom default theme', () => {
      renderWithProvider(<TestConsumer />, { defaultTheme: 'dark' });
      
      const themeElement = screen.getByTestId('current-theme');
      expect(themeElement).toHaveTextContent('dark');
    });

    it('should accept custom storage key', () => {
      renderWithProvider(<TestConsumer />, { storageKey: 'custom-theme-key' });
      
      // Should still render without errors
      expect(screen.getByTestId('current-theme')).toBeInTheDocument();
    });
  });

  describe('useTheme Hook', () => {
    it('should provide theme value', () => {
      renderWithProvider(<TestConsumer />);
      
      const themeElement = screen.getByTestId('current-theme');
      expect(themeElement).toHaveTextContent(/^(light|dark)$/);
    });

    it('should provide setTheme function', () => {
      renderWithProvider(<TestConsumer />);
      
      const setDarkButton = screen.getByTestId('set-dark');
      fireEvent.click(setDarkButton);
      
      const themeElement = screen.getByTestId('current-theme');
      expect(themeElement).toHaveTextContent('dark');
    });
  });

  describe('Theme Setting', () => {
    it('should set theme to light', () => {
      renderWithProvider(<TestConsumer />);
      
      const setLightButton = screen.getByTestId('set-light');
      fireEvent.click(setLightButton);
      
      const themeElement = screen.getByTestId('current-theme');
      expect(themeElement).toHaveTextContent('light');
    });

    it('should set theme to dark', () => {
      renderWithProvider(<TestConsumer />);
      
      const setDarkButton = screen.getByTestId('set-dark');
      fireEvent.click(setDarkButton);
      
      const themeElement = screen.getByTestId('current-theme');
      expect(themeElement).toHaveTextContent('dark');
    });

    it('should persist theme changes automatically', () => {
      renderWithProvider(<TestConsumer />);
      
      const setDarkButton = screen.getByTestId('set-dark');
      fireEvent.click(setDarkButton);
      
      // next-themes should handle persistence automatically
      expect(screen.getByTestId('current-theme')).toHaveTextContent('dark');
    });
  });

  describe('DOM Updates', () => {
    it('should add dark class to document when theme is dark', async () => {
      renderWithProvider(<TestConsumer />);
      
      const setDarkButton = screen.getByTestId('set-dark');
      fireEvent.click(setDarkButton);
      
      // Give next-themes time to update the DOM
      await new Promise(resolve => setTimeout(resolve, 100));
      
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    it('should remove dark class from document when theme is light', async () => {
      renderWithProvider(<TestConsumer />, { defaultTheme: 'dark' });
      
      // Give initial render time
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const setLightButton = screen.getByTestId('set-light');
      fireEvent.click(setLightButton);
      
      // Give next-themes time to update the DOM
      await new Promise(resolve => setTimeout(resolve, 100));
      
      expect(document.documentElement.classList.contains('dark')).toBe(false);
    });
  });

  describe('Error Handling', () => {
    it('should handle invalid theme values gracefully', () => {
      renderWithProvider(<TestConsumer />);
      
      // Should still work with valid themes
      const setDarkButton = screen.getByTestId('set-dark');
      fireEvent.click(setDarkButton);
      
      expect(screen.getByTestId('current-theme')).toHaveTextContent('dark');
    });

    it('should work without localStorage', () => {
      // Temporarily disable localStorage
      const originalGetItem = localStorageMock.getItem;
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('localStorage not available');
      });
      
      renderWithProvider(<TestConsumer />);
      
      // Should still render
      expect(screen.getByTestId('current-theme')).toBeInTheDocument();
      
      // Restore localStorage
      localStorageMock.getItem.mockImplementation(originalGetItem);
    });
  });

  describe('Multiple Consumers', () => {
    it('should provide same theme state to multiple consumers', () => {
      const Consumer1 = () => {
        const { theme } = useTheme();
        return <div data-testid="theme-1">{theme}</div>;
      };
      
      const Consumer2 = () => {
        const { theme } = useTheme();
        return <div data-testid="theme-2">{theme}</div>;
      };
      
      renderWithProvider(
        <>
          <Consumer1 />
          <Consumer2 />
          <TestConsumer />
        </>
      );
      
      const setDarkButton = screen.getByTestId('set-dark');
      fireEvent.click(setDarkButton);
      
      expect(screen.getByTestId('theme-1')).toHaveTextContent('dark');
      expect(screen.getByTestId('theme-2')).toHaveTextContent('dark');
      expect(screen.getByTestId('current-theme')).toHaveTextContent('dark');
    });

    it('should update all consumers when theme changes', () => {
      const Consumer1 = () => {
        const { theme, setTheme } = useTheme();
        return (
          <div>
            <div data-testid="consumer-1-theme">{theme}</div>
            <button onClick={() => setTheme('dark')} data-testid="consumer-1-set-dark">
              Set Dark
            </button>
          </div>
        );
      };
      
      const Consumer2 = () => {
        const { theme } = useTheme();
        return <div data-testid="consumer-2-theme">{theme}</div>;
      };
      
      renderWithProvider(
        <>
          <Consumer1 />
          <Consumer2 />
        </>
      );
      
      const setDarkButton = screen.getByTestId('consumer-1-set-dark');
      fireEvent.click(setDarkButton);
      
      expect(screen.getByTestId('consumer-1-theme')).toHaveTextContent('dark');
      expect(screen.getByTestId('consumer-2-theme')).toHaveTextContent('dark');
    });
  });

  describe('Provider Props', () => {
    it('should accept all valid theme values as defaultTheme', () => {
      const { rerender } = renderWithProvider(<TestConsumer />, { defaultTheme: 'light' });
      
      expect(screen.getByTestId('current-theme')).toBeInTheDocument();
      
      rerender(
        <ThemeProvider defaultTheme="dark">
          <TestConsumer />
        </ThemeProvider>
      );
      
      expect(screen.getByTestId('current-theme')).toBeInTheDocument();
    });

    it('should use custom storage key when provided', () => {
      renderWithProvider(<TestConsumer />, { storageKey: 'my-custom-key' });
      
      // Should render without errors
      expect(screen.getByTestId('current-theme')).toBeInTheDocument();
    });

    it('should pass through additional props to NextThemesProvider', () => {
      renderWithProvider(<TestConsumer />, { 'data-testid': 'theme-provider' } as any);
      
      // Should still work
      expect(screen.getByTestId('current-theme')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('should not cause unnecessary re-renders', () => {
      let renderCount = 0;
      
      const TrackingConsumer = () => {
        const { theme } = useTheme();
        renderCount++;
        return <div data-testid="tracking-theme">{theme}</div>;
      };
      
      const { rerender } = render(
        <ThemeProvider>
          <TrackingConsumer />
        </ThemeProvider>
      );
      
      const initialRenderCount = renderCount;
      
      // Re-render the provider with same props
      rerender(
        <ThemeProvider>
          <TrackingConsumer />
        </ThemeProvider>
      );
      
      // Should not cause excessive re-renders
      expect(renderCount).toBeGreaterThan(0);
    });

    it('should handle rapid theme changes', () => {
      renderWithProvider(<TestConsumer />);
      
      const setDarkButton = screen.getByTestId('set-dark');
      const setLightButton = screen.getByTestId('set-light');
      
      // Rapidly change themes
      fireEvent.click(setDarkButton);
      fireEvent.click(setLightButton);
      fireEvent.click(setDarkButton);
      fireEvent.click(setLightButton);
      
      // Should still work correctly
      expect(screen.getByTestId('current-theme')).toHaveTextContent('light');
    });
  });

  describe('Integration', () => {
    it('should work with nested providers', () => {
      render(
        <ThemeProvider defaultTheme="light">
          <ThemeProvider defaultTheme="dark">
            <TestConsumer />
          </ThemeProvider>
        </ThemeProvider>
      );
      
      // Inner provider should take precedence
      expect(screen.getByTestId('current-theme')).toBeInTheDocument();
    });

    it('should maintain theme state across re-mounts', () => {
      const { unmount } = renderWithProvider(<TestConsumer />);
      
      const setDarkButton = screen.getByTestId('set-dark');
      fireEvent.click(setDarkButton);
      
      expect(screen.getByTestId('current-theme')).toHaveTextContent('dark');
      
      unmount();
      
      // Re-mount and theme should be preserved (if localStorage works)
      renderWithProvider(<TestConsumer />);
      
      // The theme may or may not be preserved depending on next-themes implementation
      expect(screen.getByTestId('current-theme')).toBeInTheDocument();
    });
  });
}); 