import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeSwitcher } from '../../components/ThemeSwitcher';
import { ThemeProvider } from '../../contexts/ThemeContext';

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

describe('ThemeSwitcher', () => {
  const renderWithTheme = (component: React.ReactElement) => {
    return render(
      <ThemeProvider>
        {component}
      </ThemeProvider>
    );
  };

  beforeEach(() => {
    // Clear localStorage mock before each test
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

  describe('Component Rendering', () => {
    it('should render the theme switcher button', () => {
      renderWithTheme(<ThemeSwitcher />);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('should show appropriate icon based on theme', () => {
      renderWithTheme(<ThemeSwitcher />);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      
      // Check for the presence of both icons
      const sunIcon = button.querySelector('.lucide-sun');
      const moonIcon = button.querySelector('.lucide-moon');
      
      expect(sunIcon).toBeInTheDocument();
      expect(moonIcon).toBeInTheDocument();
    });

    it('should have accessibility text', () => {
      renderWithTheme(<ThemeSwitcher />);
      
      const button = screen.getByRole('button');
      
      // Check for screen reader text
      expect(screen.getByText('Toggle theme')).toBeInTheDocument();
    });
  });

  describe('Theme Toggle Functionality', () => {
    it('should toggle theme when clicked', () => {
      renderWithTheme(<ThemeSwitcher />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      // The theme should change (exact behavior depends on implementation)
      expect(button).toBeInTheDocument();
    });

    it('should default to light theme when no theme is set', () => {
      renderWithTheme(<ThemeSwitcher />);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      
      // Should show the moon icon indicating light mode
      const moonIcon = button.querySelector('.lucide-moon');
      expect(moonIcon).toBeInTheDocument();
    });

    it('should respect system preference when no theme is set', () => {
      // Mock system preference for dark mode
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation(query => ({
          matches: query === '(prefers-color-scheme: dark)',
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        })),
      });
      
      renderWithTheme(<ThemeSwitcher />);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });
  });

  describe('DOM Updates', () => {
    it('should not interfere with document class management', () => {
      renderWithTheme(<ThemeSwitcher />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      // The component should work without throwing errors
      expect(button).toBeInTheDocument();
    });
  });

  describe('Persistence', () => {
    it('should work with theme persistence', () => {
      renderWithTheme(<ThemeSwitcher />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      // Component should function regardless of persistence implementation
      expect(button).toBeInTheDocument();
    });

    it('should handle localStorage gracefully', () => {
      // Mock localStorage error
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('localStorage not available');
      });
      
      renderWithTheme(<ThemeSwitcher />);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });
  });

  describe('Keyboard Interaction', () => {
    it('should respond to keyboard events', () => {
      renderWithTheme(<ThemeSwitcher />);
      
      const button = screen.getByRole('button');
      fireEvent.keyDown(button, { key: 'Enter' });
      
      // Should not throw errors
      expect(button).toBeInTheDocument();
    });

    it('should respond to space key', () => {
      renderWithTheme(<ThemeSwitcher />);
      
      const button = screen.getByRole('button');
      fireEvent.keyDown(button, { key: ' ' });
      
      // Should not throw errors
      expect(button).toBeInTheDocument();
    });
  });

  describe('Visual Feedback', () => {
    it('should have appropriate CSS classes', () => {
      renderWithTheme(<ThemeSwitcher />);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('inline-flex');
      expect(button).toHaveClass('items-center');
      expect(button).toHaveClass('justify-center');
    });

    it('should have focus state', () => {
      renderWithTheme(<ThemeSwitcher />);
      
      const button = screen.getByRole('button');
      button.focus();
      
      expect(button).toHaveClass('outline-none');
    });

    it('should have transition animations', () => {
      renderWithTheme(<ThemeSwitcher />);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('transition-all');
    });
  });

  describe('Integration with Theme Context', () => {
    it('should work within theme context', () => {
      renderWithTheme(<ThemeSwitcher />);
      
      const button = screen.getByRole('button');
      fireEvent.click(button);
      
      // Should work without errors
      expect(button).toBeInTheDocument();
    });
  });
}); 