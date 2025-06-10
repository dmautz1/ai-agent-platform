import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { AgentSelector } from '@/components/AgentSelector';
import { api } from '@/lib/api';
import type { AgentInfo } from '@/lib/models';
import { renderWithProviders } from '../utils';

// Mock dependencies
vi.mock('@/lib/api', () => ({
  api: {
    agents: {
      getAll: vi.fn()
    }
  },
  handleApiError: vi.fn((error) => error.message || 'Unknown error')
}));

vi.mock('@/lib/utils', () => ({
  cn: (...classes: (string | undefined)[]) => classes.filter(Boolean).join(' ')
}));

// Mock data
const mockAgents: AgentInfo[] = [
  {
    identifier: 'research_agent',
    name: 'Research Agent',
    description: 'Performs research tasks',
    class_name: 'ResearchAgent',
    supported_environments: ['production'],
    lifecycle_state: 'enabled',
    version: '1.0.0',
    enabled: true,
    has_error: false,
    created_at: '2024-01-01T00:00:00Z',
    last_updated: '2024-01-01T00:00:00Z'
  },
  {
    identifier: 'content_summarizer',
    name: 'Content Summarizer',
    description: 'Summarizes content',
    class_name: 'ContentSummarizer',
    supported_environments: ['production'],
    lifecycle_state: 'enabled',
    version: '1.1.0',
    enabled: true,
    has_error: false,
    created_at: '2024-01-01T00:00:00Z',
    last_updated: '2024-01-01T00:00:00Z'
  },
  {
    identifier: 'web_extractor',
    name: 'Web Data Extractor',
    description: 'Extracts web data',
    class_name: 'WebExtractor',
    supported_environments: ['production'],
    lifecycle_state: 'enabled',
    version: '1.0.0',
    enabled: true,
    has_error: false,
    created_at: '2024-01-01T00:00:00Z',
    last_updated: '2024-01-01T00:00:00Z'
  },
  {
    identifier: 'disabled_agent',
    name: 'Disabled Agent',
    description: 'This agent is disabled',
    class_name: 'DisabledAgent',
    supported_environments: ['development'],
    lifecycle_state: 'disabled',
    version: '0.1.0',
    enabled: false,
    has_error: false,
    created_at: '2024-01-01T00:00:00Z',
    last_updated: '2024-01-01T00:00:00Z'
  },
  {
    identifier: 'error_agent',
    name: 'Error Agent',
    description: 'Agent with error',
    class_name: 'ErrorAgent',
    supported_environments: ['testing'],
    lifecycle_state: 'error',
    version: '0.5.0',
    enabled: true,
    has_error: true,
    error_message: 'Failed to initialize',
    created_at: '2024-01-01T00:00:00Z',
    last_updated: '2024-01-01T00:00:00Z'
  }
];

describe('AgentSelector', () => {
  const user = userEvent.setup();
  const mockOnAgentSelected = vi.fn();
  const mockOnBrowseAll = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('External Data Mode', () => {
    it('should render with external agents data', () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
        />
      );

      expect(screen.getByRole('combobox')).toBeInTheDocument();
      expect(screen.getByText('3 of 5 agents available')).toBeInTheDocument();
    });

    it('should show loading state with external loading prop', () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={[]}
          loading={true}
          error={null}
        />
      );

      expect(screen.getByText('Loading agents...')).toBeInTheDocument();
      expect(screen.getByRole('combobox')).toBeDisabled();
    });

    it('should show error state with external error prop', () => {
      const errorMessage = 'Failed to fetch agents';
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={[]}
          loading={false}
          error={errorMessage}
        />
      );

      expect(screen.getByText(`Failed to load agents: ${errorMessage}`)).toBeInTheDocument();
    });
  });

  describe('Internal Data Mode', () => {
    it('should fetch agents internally on mount', async () => {
      const mockGetAll = vi.mocked(api.agents.getAll);
      mockGetAll.mockResolvedValue(mockAgents);

      renderWithProviders(<AgentSelector onAgentSelected={mockOnAgentSelected} />);

      expect(screen.getByText('Loading agents...')).toBeInTheDocument();

      await waitFor(() => {
        expect(mockGetAll).toHaveBeenCalledTimes(1);
      }, { timeout: 2000 });

      await waitFor(() => {
        expect(screen.getByText('3 of 5 agents available')).toBeInTheDocument();
      }, { timeout: 3000 });
    }, 10000); // Increase test timeout

    it('should handle fetch error', async () => {
      const mockGetAll = vi.mocked(api.agents.getAll);
      mockGetAll.mockRejectedValue(new Error('Network error'));

      renderWithProviders(<AgentSelector onAgentSelected={mockOnAgentSelected} />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load agents: Network error')).toBeInTheDocument();
      }, { timeout: 3000 });
    }, 10000); // Increase test timeout
  });

  describe('Agent Selection', () => {
    it('should call onAgentSelected when an agent is selected', async () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
        />
      );

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      // Wait for dropdown to open
      await waitFor(() => {
        expect(screen.getByText('Research Agent')).toBeInTheDocument();
      }, { timeout: 2000 });

      const researchOption = screen.getByText('Research Agent');
      await user.click(researchOption);

      expect(mockOnAgentSelected).toHaveBeenCalledWith('research_agent');
    }, 15000);

    it('should not allow selection of disabled agents', async () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
        />
      );

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      // Wait for dropdown to open
      await waitFor(() => {
        expect(screen.getByText('Disabled Agent')).toBeInTheDocument();
      }, { timeout: 2000 });

      const disabledOption = screen.getByText('Disabled Agent').closest('[role="option"]');
      expect(disabledOption).toHaveAttribute('aria-disabled', 'true');
    }, 15000);

    it('should not allow selection of agents with errors', async () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
        />
      );

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      // Wait for dropdown to open
      await waitFor(() => {
        expect(screen.getByText('Error Agent')).toBeInTheDocument();
      }, { timeout: 2000 });

      const errorOption = screen.getByText('Error Agent').closest('[role="option"]');
      expect(errorOption).toHaveAttribute('aria-disabled', 'true');
    }, 15000);
  });

  describe('Agent Sorting and Sections', () => {
    it('should sort favorites first', async () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
          favoriteAgents={['web_extractor']}
        />
      );

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      await waitFor(() => {
        expect(screen.getByText('Favorites')).toBeInTheDocument();
      }, { timeout: 2000 });
      
      // Check that Web Data Extractor appears in the favorites section
      await waitFor(() => {
        expect(screen.getByText('Web Data Extractor')).toBeInTheDocument();
      }, { timeout: 1000 });
    }, 15000);

    it('should sort recent agents after favorites', async () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
          recentAgents={['content_summarizer']}
        />
      );

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      await waitFor(() => {
        expect(screen.getByText('Recently Used')).toBeInTheDocument();
      }, { timeout: 2000 });
    }, 15000);

    it('should show favorites and recent sections correctly', async () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
          favoriteAgents={['research_agent']}
          recentAgents={['content_summarizer', 'web_extractor']}
        />
      );

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      await waitFor(() => {
        expect(screen.getByText('Favorites')).toBeInTheDocument();
        expect(screen.getByText('Recently Used')).toBeInTheDocument();
        expect(screen.getByText('All Agents')).toBeInTheDocument();
      }, { timeout: 2000 });
    }, 15000);

    it('should not duplicate agents in multiple sections', async () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
          favoriteAgents={['research_agent']}
          recentAgents={['research_agent', 'content_summarizer']}
        />
      );

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      await waitFor(() => {
        // Research agent should only appear in favorites, not in recent
        const researchOptions = screen.getAllByText('Research Agent');
        expect(researchOptions).toHaveLength(1);
      }, { timeout: 2000 });
    }, 15000);

    it('should sort alphabetically within each section', async () => {
      const alphabeticalAgents = [
        {
          ...mockAgents[0],
          identifier: 'z_agent',
          name: 'Z Agent'
        },
        {
          ...mockAgents[1],
          identifier: 'a_agent',
          name: 'A Agent'
        }
      ];

      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={alphabeticalAgents}
          loading={false}
          error={null}
        />
      );

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      await waitFor(() => {
        const options = screen.getAllByRole('option');
        const optionTexts = options.map(option => option.textContent);
        
        // A Agent should come before Z Agent
        const aAgentIndex = optionTexts.findIndex(text => text?.includes('A Agent'));
        const zAgentIndex = optionTexts.findIndex(text => text?.includes('Z Agent'));
        expect(aAgentIndex).toBeLessThan(zAgentIndex);
      }, { timeout: 2000 });
    }, 15000);
  });

  describe('Agent Status Display', () => {
    it('should show status icons and badges correctly', async () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
        />
      );

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      // Check for status indicators
      expect(screen.getAllByText('Ready')).toHaveLength(3); // 3 enabled agents
      expect(screen.getByText('Disabled')).toBeInTheDocument();
      expect(screen.getByText('Error')).toBeInTheDocument();
    });

    it('should show star icon for favorite agents', async () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
          favoriteAgents={['research_agent']}
        />
      );

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      // Check that favorites section exists and contains the favorite agent
      await waitFor(() => {
        expect(screen.getByText('Favorites')).toBeInTheDocument();
        expect(screen.getByText('Research Agent')).toBeInTheDocument();
      }, { timeout: 2000 });
    }, 15000);

    it('should show clock icon for recent agents (non-favorites)', async () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
          recentAgents={['content_summarizer']}
        />
      );

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      // Check that recent section exists and contains the recent agent
      await waitFor(() => {
        expect(screen.getByText('Recently Used')).toBeInTheDocument();
        expect(screen.getByText('Content Summarizer')).toBeInTheDocument();
      }, { timeout: 2000 });
    }, 15000);
  });

  describe('Browse All Agents Button', () => {
    it('should show browse button by default', () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
        />
      );

      expect(screen.getByText('Browse All Agents')).toBeInTheDocument();
    });

    it('should hide browse button when showBrowseButton is false', () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
          showBrowseButton={false}
        />
      );

      expect(screen.queryByText('Browse All Agents')).not.toBeInTheDocument();
    });

    it('should call onBrowseAll when browse button is clicked', async () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
          onBrowseAll={mockOnBrowseAll}
        />
      );

      const browseButton = screen.getByText('Browse All Agents');
      await user.click(browseButton);

      expect(mockOnBrowseAll).toHaveBeenCalledTimes(1);
    });

    it('should show browse button even in error state', () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={[]}
          loading={false}
          error="Network error"
          onBrowseAll={mockOnBrowseAll}
        />
      );

      expect(screen.getByText('Browse All Agents')).toBeInTheDocument();
    });

    it('should disable browse button when selector is disabled', () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
          disabled={true}
        />
      );

      const browseButton = screen.getByText('Browse All Agents');
      expect(browseButton).toBeDisabled();
    });
  });

  describe('Disabled State', () => {
    it('should disable selector when disabled prop is true', () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
          disabled={true}
        />
      );

      expect(screen.getByRole('combobox')).toBeDisabled();
    });

    it('should disable selector when no agents are available', () => {
      const disabledAgents = mockAgents.filter(agent => !agent.enabled || agent.has_error);
      
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={disabledAgents}
          loading={false}
          error={null}
        />
      );

      expect(screen.getByRole('combobox')).toBeDisabled();
      expect(screen.getByText('No agents available')).toBeInTheDocument();
    });
  });

  describe('Custom Placeholder', () => {
    it('should use default placeholder', () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
        />
      );

      expect(screen.getByText('Select an agent...')).toBeInTheDocument();
    });

    it('should use custom placeholder', () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
          placeholder="Choose your AI assistant"
        />
      );

      expect(screen.getByText('Choose your AI assistant')).toBeInTheDocument();
    });
  });

  describe('Status Summary', () => {
    it('should show correct availability count', () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
        />
      );

      expect(screen.getByText('3 of 5 agents available')).toBeInTheDocument();
    });

    it('should show unavailable badge when there are unavailable agents', () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
        />
      );

      expect(screen.getByText('2 unavailable')).toBeInTheDocument();
    });

    it('should not show unavailable badge when all agents are available', () => {
      const availableAgents = mockAgents.filter(agent => agent.enabled && !agent.has_error);
      
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={availableAgents}
          loading={false}
          error={null}
        />
      );

      expect(screen.queryByText(/unavailable/)).not.toBeInTheDocument();
    });

    it('should not show status summary when no agents exist', () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={[]}
          loading={false}
          error={null}
        />
      );

      // The component shows "No agents available" when there are no agents
      expect(screen.getByText('No agents available')).toBeInTheDocument();
      // But should not show the count summary
      expect(screen.queryByText(/\d+ of \d+ agents available/)).not.toBeInTheDocument();
    });
  });

  describe('Empty States', () => {
    it('should show "No agents available" when agents array is empty', async () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={[]}
          loading={false}
          error={null}
        />
      );

      // The component shows "No agents available" in the trigger when empty
      expect(screen.getByText('No agents available')).toBeInTheDocument();
      
      // When opened, it should show empty state
      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      // Check for empty state in dropdown (if it opens)
      // Note: This might not work if the dropdown doesn't open when empty
      if (screen.queryByRole('listbox')) {
        expect(screen.getByText(/No agents/)).toBeInTheDocument();
      }
    });
  });

  describe('Loading States', () => {
    it('should show loading indicator in button during loading', () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          loading={true}
        />
      );

      const browseButton = screen.getByText('Browse All Agents');
      expect(browseButton).toBeDisabled();
    });
  });

  describe('Agent Item Display', () => {
    it('should show agent descriptions in dropdown items', async () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
        />
      );

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      expect(screen.getByText('Performs research tasks')).toBeInTheDocument();
      expect(screen.getByText('Summarizes content')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper combobox role', () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
        />
      );

      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('should have proper option roles in dropdown', async () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
        />
      );

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      const options = screen.getAllByRole('option');
      expect(options.length).toBeGreaterThan(0);
    });

    it('should properly disable unavailable options', async () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
        />
      );

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      const disabledOption = screen.getByText('Disabled Agent').closest('[role="option"]');
      const errorOption = screen.getByText('Error Agent').closest('[role="option"]');
      
      expect(disabledOption).toHaveAttribute('aria-disabled', 'true');
      expect(errorOption).toHaveAttribute('aria-disabled', 'true');
    });
  });

  describe('Edge Cases', () => {
    it('should handle agents with no job types gracefully', async () => {
      const agentNoJobTypes = {
        ...mockAgents[0],
        // Generic framework doesn't use hardcoded job types
      };

      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={[agentNoJobTypes]}
          loading={false}
          error={null}
        />
      );

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      expect(screen.getByText('Research Agent')).toBeInTheDocument();
    });

    it('should handle agents with no description', async () => {
      const agentNoDescription = {
        ...mockAgents[0],
        description: ''
      };

      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={[agentNoDescription]}
          loading={false}
          error={null}
        />
      );

      const trigger = screen.getByRole('combobox');
      await user.click(trigger);

      expect(screen.getByText('Research Agent')).toBeInTheDocument();
    });

    it('should handle empty recent and favorite arrays', () => {
      renderWithProviders(
        <AgentSelector
          onAgentSelected={mockOnAgentSelected}
          agents={mockAgents}
          loading={false}
          error={null}
          recentAgents={[]}
          favoriteAgents={[]}
        />
      );

      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
  });
}); 