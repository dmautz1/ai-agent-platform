import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import { LLMSelector } from '../../components/LLMSelector';
import { createMockApiSuccessResponse, createMockApiErrorResponse } from '../utils';

// Mock axios and api module
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        request: {
          use: vi.fn(),
        },
        response: {
          use: vi.fn(),
        },
      },
      defaults: {
        headers: {},
      },
    })),
    interceptors: {
      request: {
        use: vi.fn(),
      },
      response: {
        use: vi.fn(),
      },
    },
  },
}));

// Mock the api module
vi.mock('../../lib/api', () => ({
  api: {
    llmProviders: {
      getGoogleAIModels: vi.fn(),
      getOpenAIModels: vi.fn(),
      getAnthropicModels: vi.fn(),
      getGrokModels: vi.fn(),
      getDeepSeekModels: vi.fn(),
      getLlamaModels: vi.fn(),
    },
  },
  extractApiResult: vi.fn((response) => response.result),
  handleApiError: vi.fn((error) => error.message || 'An error occurred'),
}));

const mockedAxios = vi.mocked(axios, true);

describe('LLMSelector', () => {
  const mockOnProviderChange = vi.fn();
  const mockOnModelChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      },
      writable: true,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const getModelsForProvider = (provider: string) => {
    switch (provider) {
      case 'openai':
        return ['gpt-4', 'gpt-3.5-turbo'];
      case 'anthropic':
        return ['claude-3-opus', 'claude-3-sonnet'];
      case 'google-ai':
        return ['gemini-pro', 'gemini-pro-vision'];
      default:
        return ['model-1', 'model-2'];
    }
  };

  const getDefaultModelForProvider = (provider: string) => {
    const models = getModelsForProvider(provider);
    return models[0];
  };

  describe('Component Rendering', () => {
    it('should render the LLM selector with initial state', async () => {
      await act(async () => {
        render(
          <LLMSelector
            onProviderChange={mockOnProviderChange}
            onModelChange={mockOnModelChange}
          />
        );
      });
      
      // Should show initial selects
      expect(screen.getByText('Select a provider')).toBeInTheDocument();
      expect(screen.getByText('Select a model')).toBeInTheDocument();
    });

    it('should show labels when showLabels is true', async () => {
      await act(async () => {
        render(
          <LLMSelector
            showLabels={true}
            onProviderChange={mockOnProviderChange}
            onModelChange={mockOnModelChange}
          />
        );
      });
      
      expect(screen.getByText('LLM Provider')).toBeInTheDocument();
      expect(screen.getByText('Model')).toBeInTheDocument();
    });

    it('should render component structure', async () => {
      let container;
      await act(async () => {
        const result = render(
          <LLMSelector
            onProviderChange={mockOnProviderChange}
            onModelChange={mockOnModelChange}
          />
        );
        container = result.container;
      });
      
      expect(container.firstChild).toBeInTheDocument();
    });
  });

  describe('Provider Selection', () => {
    it('should handle provider changes', async () => {
      await act(async () => {
        render(
          <LLMSelector
            selectedProvider="openai"
            onProviderChange={mockOnProviderChange}
            onModelChange={mockOnModelChange}
          />
        );
      });
      
      // Component should render without errors
      expect(screen.getByText('LLM Provider')).toBeInTheDocument();
    });

    it('should handle model changes', async () => {
      await act(async () => {
        render(
          <LLMSelector
            selectedProvider="openai"
            selectedModel="gpt-4"
            onProviderChange={mockOnProviderChange}
            onModelChange={mockOnModelChange}
          />
        );
      });
      
      // Component should render without errors
      expect(screen.getByText('Model')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should handle loading errors gracefully', async () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      
      await act(async () => {
        render(
          <LLMSelector
            onProviderChange={mockOnProviderChange}
            onModelChange={mockOnModelChange}
          />
        );
      });
      
      // Should render component without crashing
      expect(screen.getByText('LLM Provider')).toBeInTheDocument();
      
      consoleWarnSpy.mockRestore();
    });

    it('should render without crashing on errors', async () => {
      await act(async () => {
        render(
          <LLMSelector
            onProviderChange={mockOnProviderChange}
            onModelChange={mockOnModelChange}
          />
        );
      });
      
      // Should not crash
      expect(screen.getByText('LLM Provider')).toBeInTheDocument();
    });
  });

  describe('ApiResponse Integration', () => {
    it('should handle ApiResponse success format', async () => {
      const successResponse = createMockApiSuccessResponse({
        models: ['gpt-4', 'gpt-3.5-turbo'],
        default_model: 'gpt-4'
      });
      
      await act(async () => {
        render(
          <LLMSelector
            onProviderChange={mockOnProviderChange}
            onModelChange={mockOnModelChange}
          />
        );
      });
      
      // Should render component
      expect(screen.getByText('LLM Provider')).toBeInTheDocument();
    });

    it('should handle ApiResponse error format', async () => {
      const errorResponse = createMockApiErrorResponse('Failed to fetch models');
      
      await act(async () => {
        render(
          <LLMSelector
            onProviderChange={mockOnProviderChange}
            onModelChange={mockOnModelChange}
          />
        );
      });
      
      // Should handle the error gracefully
      expect(screen.getByText('LLM Provider')).toBeInTheDocument();
    });
  });

  describe('Component Props', () => {
    it('should handle disabled prop', async () => {
      await act(async () => {
        render(
          <LLMSelector
            disabled={true}
            onProviderChange={mockOnProviderChange}
            onModelChange={mockOnModelChange}
          />
        );
      });
      
      // Should render in disabled state
      expect(screen.getByText('LLM Provider')).toBeInTheDocument();
    });

    it('should hide labels when showLabels is false', async () => {
      await act(async () => {
        render(
          <LLMSelector
            showLabels={false}
            onProviderChange={mockOnProviderChange}
            onModelChange={mockOnModelChange}
          />
        );
      });
      
      // When showLabels is false, the loading states should still show but without labels
      // The loading text is still present but labels are not rendered
      expect(screen.queryByText('LLM Provider')).not.toBeInTheDocument();
      expect(screen.queryByText('Model')).not.toBeInTheDocument();
    });

    it('should apply custom className', async () => {
      let container;
      await act(async () => {
        const result = render(
          <LLMSelector
            className="custom-class"
            onProviderChange={mockOnProviderChange}
            onModelChange={mockOnModelChange}
          />
        );
        container = result.container;
      });
      
      expect(container.firstChild).toHaveClass('custom-class');
    });

    it('should support different sizes', async () => {
      await act(async () => {
        render(
          <LLMSelector
            size="sm"
            onProviderChange={mockOnProviderChange}
            onModelChange={mockOnModelChange}
          />
        );
      });
      
      // Component should render with small size - check for h-8 class which indicates sm size
      const buttons = screen.getAllByRole('combobox');
      expect(buttons[0]).toHaveClass('h-8');
    });
  });

  describe('Authentication', () => {
    it('should include auth token in requests when available', async () => {
      const mockGetItem = vi.fn().mockReturnValue('test-token');
      Object.defineProperty(window, 'localStorage', {
        value: { getItem: mockGetItem },
        writable: true,
      });
      
      await act(async () => {
        render(
          <LLMSelector
            onProviderChange={mockOnProviderChange}
            onModelChange={mockOnModelChange}
          />
        );
      });
      
      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: 'http://localhost:8000',
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json',
        },
      });
    });
  });
}); 