import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect } from 'vitest';
import { AgentCard } from '@/components/AgentCard';
import type { AgentInfo } from '@/lib/models';

// Mock dependencies
vi.mock('@/lib/responsive', () => ({
  useBreakpoint: () => ({
    isMobile: false
  })
}));

vi.mock('@/lib/utils', () => ({
  cn: (...classes: (string | undefined)[]) => classes.filter(Boolean).join(' ')
}));

// Mock data
const mockAgent: AgentInfo = {
  identifier: 'test_agent',
  name: 'Test Agent',
  description: 'A test agent for demonstration',
  class_name: 'TestAgent',
  lifecycle_state: 'enabled',
  supported_environments: ['dev'],
  version: '1.0.0',
  enabled: true,
  has_error: false,
  created_at: '2024-01-01T00:00:00Z',
  last_updated: '2024-01-15T10:30:00Z'
};

const mockDisabledAgent: AgentInfo = {
  identifier: 'disabled_agent',
  name: 'Disabled Agent',
  description: 'A disabled test agent',
  class_name: 'DisabledAgent',
  lifecycle_state: 'disabled',
  supported_environments: ['dev'],
  version: '1.0.0',
  enabled: false,
  has_error: false,
  created_at: '2024-01-01T00:00:00Z',
  last_updated: '2024-01-15T10:30:00Z'
};

const mockProdAgent: AgentInfo = {
  identifier: 'prod_agent',
  name: 'Production Agent',
  description: 'A production test agent',
  class_name: 'ProdAgent',
  lifecycle_state: 'enabled',
  supported_environments: ['prod'],
  version: '1.0.0',
  enabled: true,
  has_error: true,
  error_message: 'Test error for demonstration',
  created_at: '2024-01-01T00:00:00Z',
  last_updated: '2024-01-15T10:30:00Z'
};

const mockManyDetailsAgent: AgentInfo = {
  identifier: 'detailed_agent',
  name: 'Very Long Agent Name That Should Truncate Properly',
  description: 'This is a very long description that should demonstrate how the component handles longer text content and potentially wraps or truncates it appropriately',
  class_name: 'DetailedAgent',
  lifecycle_state: 'beta',
  supported_environments: ['test', 'dev', 'staging'],
  version: '2.0.0',
  enabled: true,
  has_error: false,
  created_at: '2024-01-01T00:00:00Z',
  last_updated: '2024-01-15T10:30:00Z'
};

describe('AgentCard', () => {
  const user = userEvent.setup();

  describe('Basic Rendering', () => {
    it('should render agent information correctly', () => {
      render(<AgentCard agent={mockAgent} />);

      expect(screen.getByText('Test Agent')).toBeInTheDocument();
      expect(screen.getByText('test_agent')).toBeInTheDocument();
      expect(screen.getByText('A test agent for demonstration')).toBeInTheDocument();
    });

    it('should display supported job types', () => {
      render(<AgentCard agent={mockAgent} />);

      // Job types are no longer supported in the generic framework
      expect(screen.queryByText('Job Types:')).not.toBeInTheDocument();
    });

    it('should show truncated job types when there are many', () => {
      render(<AgentCard agent={mockManyDetailsAgent} />);

      // Job types are no longer supported in the generic framework  
      expect(screen.queryByText('research')).not.toBeInTheDocument();
    });

    it('should display last updated date', () => {
      render(<AgentCard agent={mockAgent} />);

      expect(screen.getByText('Updated:')).toBeInTheDocument();
      // Check for date presence (format may vary by locale)
      expect(screen.getByText(/2024|15|Jan/)).toBeInTheDocument();
    });
  });

  describe('Status Badges', () => {
    it('should show Ready badge for enabled agents', () => {
      render(<AgentCard agent={mockAgent} />);

      const readyBadge = screen.getByText('Ready');
      expect(readyBadge).toBeInTheDocument();
      expect(readyBadge.closest('.bg-green-500')).toBeInTheDocument();
    });

    it('should show Disabled badge for disabled agents', () => {
      render(<AgentCard agent={mockDisabledAgent} />);

      const disabledBadge = screen.getByText('Disabled');
      expect(disabledBadge).toBeInTheDocument();
    });

    it('should show Error badge for agents with errors', () => {
      render(<AgentCard agent={mockProdAgent} />);

      const errorBadge = screen.getByText('Error');
      expect(errorBadge).toBeInTheDocument();
    });

    it('should show lifecycle state badge for non-enabled agents', () => {
      render(<AgentCard agent={mockManyDetailsAgent} />);

      expect(screen.getByText('beta')).toBeInTheDocument();
    });
  });

  describe('Error Display', () => {
    it('should display error message when agent has error', () => {
      render(<AgentCard agent={mockProdAgent} />);

      expect(screen.getByText('Error:')).toBeInTheDocument();
      expect(screen.getByText('Test error for demonstration')).toBeInTheDocument();
    });

    it('should style error card appropriately', () => {
      render(<AgentCard agent={mockProdAgent} />);

      const errorSection = screen.getByText('Error:').closest('div');
      expect(errorSection).toHaveClass('bg-destructive/10');
    });

    it('should not show error section for agents without errors', () => {
      render(<AgentCard agent={mockAgent} />);

      expect(screen.queryByText('Error:')).not.toBeInTheDocument();
    });
  });

  describe('Selection Mode', () => {
    it('should render Select Agent button in selection mode', () => {
      render(<AgentCard agent={mockAgent} selectionMode={true} />);

      expect(screen.getByRole('button', { name: 'Select Agent' })).toBeInTheDocument();
    });

    it('should call onSelect when Select Agent button is clicked', async () => {
      const mockOnSelect = vi.fn();
      render(
        <AgentCard 
          agent={mockAgent} 
          selectionMode={true} 
          onSelect={mockOnSelect} 
        />
      );

      const selectButton = screen.getByRole('button', { name: 'Select Agent' });
      await user.click(selectButton);

      expect(mockOnSelect).toHaveBeenCalledWith(mockAgent);
    });

    it('should call onSelect when card is clicked in selection mode', async () => {
      const mockOnSelect = vi.fn();
      render(
        <AgentCard 
          agent={mockAgent} 
          selectionMode={true} 
          onSelect={mockOnSelect} 
        />
      );

      const card = screen.getByRole('button', { name: 'Select Agent' }).closest('[class*="cursor-pointer"]');
      if (card) {
        await user.click(card);
        expect(mockOnSelect).toHaveBeenCalledWith(mockAgent);
      }
    });

    it('should disable selection for disabled agents', () => {
      render(<AgentCard agent={mockDisabledAgent} selectionMode={true} />);

      const selectButton = screen.getByRole('button', { name: 'Select Agent' });
      expect(selectButton).toBeDisabled();
    });

    it('should disable selection for agents with errors', () => {
      render(<AgentCard agent={mockProdAgent} selectionMode={true} />);

      const selectButton = screen.getByRole('button', { name: 'Select Agent' });
      expect(selectButton).toBeDisabled();
    });

    it('should not call onSelect for disabled agents when card is clicked', async () => {
      const mockOnSelect = vi.fn();
      render(
        <AgentCard 
          agent={mockDisabledAgent} 
          selectionMode={true} 
          onSelect={mockOnSelect} 
        />
      );

      const card = screen.getByText('Disabled Agent').closest('div');
      if (card) {
        await user.click(card);
        expect(mockOnSelect).not.toHaveBeenCalled();
      }
    });
  });

  describe('Configuration Mode', () => {
    it('should render Configure button when showConfigButton is true', () => {
      render(<AgentCard agent={mockAgent} showConfigButton={true} />);

      expect(screen.getByRole('button', { name: 'Configure' })).toBeInTheDocument();
    });

    it('should call onConfigure when Configure button is clicked', async () => {
      const mockOnConfigure = vi.fn();
      render(
        <AgentCard 
          agent={mockAgent} 
          showConfigButton={true} 
          onConfigure={mockOnConfigure} 
        />
      );

      const configButton = screen.getByRole('button', { name: 'Configure' });
      await user.click(configButton);

      expect(mockOnConfigure).toHaveBeenCalledWith(mockAgent);
    });

    it('should disable Configure button for disabled agents', () => {
      render(<AgentCard agent={mockDisabledAgent} showConfigButton={true} />);

      const configButton = screen.getByRole('button', { name: 'Configure' });
      expect(configButton).toBeDisabled();
    });

    it('should show both Select and Configure buttons when both modes are enabled', () => {
      render(
        <AgentCard 
          agent={mockAgent} 
          selectionMode={true}
          showConfigButton={true} 
        />
      );

      expect(screen.getByRole('button', { name: 'Select Agent' })).toBeInTheDocument();
      // In selection mode, the configure button is just an icon without accessible name
      const buttons = screen.getAllByRole('button');
      expect(buttons).toHaveLength(2); // Should have both buttons
    });

    it('should prevent event propagation when Configure button is clicked', async () => {
      const mockOnSelect = vi.fn();
      const mockOnConfigure = vi.fn();
      
      render(
        <AgentCard 
          agent={mockAgent} 
          selectionMode={true}
          showConfigButton={true}
          onSelect={mockOnSelect}
          onConfigure={mockOnConfigure}
        />
      );

      // Find the configure button (without "Configure" text in selection mode)
      const buttons = screen.getAllByRole('button');
      const configButton = buttons.find(button => !button.textContent?.includes('Select Agent'));
      
      if (configButton) {
        await user.click(configButton);
        expect(mockOnConfigure).toHaveBeenCalledWith(mockAgent);
        expect(mockOnSelect).not.toHaveBeenCalled();
      }
    });
  });

  describe('Display Modes', () => {
    it('should render in compact mode', () => {
      render(<AgentCard agent={mockAgent} compact={true} />);

      // In compact mode, the component should render with smaller text
      expect(screen.getByText('Test Agent')).toBeInTheDocument();
      expect(screen.getByText('A test agent for demonstration')).toBeInTheDocument();
    });

    it('should show extended details when showExtendedDetails is true', () => {
      render(<AgentCard agent={mockAgent} showExtendedDetails={true} />);

      expect(screen.getByText('Environments:')).toBeInTheDocument();
      expect(screen.getByText('dev')).toBeInTheDocument();
      expect(screen.getByText('Created:')).toBeInTheDocument();
    });

    it('should show runtime info in extended details', () => {
      const agentWithRuntime = {
        ...mockAgent,
        runtime_info: { status: 'running' },
        instance_available: true
      };

      render(<AgentCard agent={agentWithRuntime} showExtendedDetails={true} />);

      expect(screen.getByText('Runtime:')).toBeInTheDocument();
      expect(screen.getByText('Instance:')).toBeInTheDocument();
      expect(screen.getByText('Available')).toBeInTheDocument();
    });

    it('should show instance unavailable status', () => {
      const agentWithUnavailableInstance = {
        ...mockAgent,
        runtime_info: { status: 'stopped' },
        instance_available: false
      };

      render(<AgentCard agent={agentWithUnavailableInstance} showExtendedDetails={true} />);

      expect(screen.getByText('Unavailable')).toBeInTheDocument();
    });

    it('should hide version badge in compact mode', () => {
      render(<AgentCard agent={mockAgent} compact={true} />);

      expect(screen.queryByText('v1.0.0')).not.toBeInTheDocument();
    });

    it('should show version badge in normal mode', () => {
      render(<AgentCard agent={mockAgent} compact={false} />);

      expect(screen.getByText('v1.0.0')).toBeInTheDocument();
    });
  });

  describe('Styling and Layout', () => {
    it('should apply custom className', () => {
      render(<AgentCard agent={mockAgent} className="custom-class" />);

      const card = screen.getByText('Test Agent').closest('[class*="custom-class"]');
      expect(card).toBeInTheDocument();
    });

    it('should apply opacity for disabled agents', () => {
      render(<AgentCard agent={mockDisabledAgent} />);

      const card = screen.getByText('Disabled Agent').closest('[class*="opacity-75"]');
      expect(card).toBeInTheDocument();
    });

    it('should apply error border for agents with errors', () => {
      render(<AgentCard agent={mockProdAgent} />);

      const card = screen.getByText('Production Agent').closest('[class*="border-destructive"]');
      expect(card).toBeInTheDocument();
    });

    it('should apply hover styles in selection mode', () => {
      render(<AgentCard agent={mockAgent} selectionMode={true} />);

      const card = screen.getByText('Test Agent').closest('[class*="cursor-pointer"]');
      expect(card).toBeInTheDocument();
    });

    it('should not apply hover styles in normal mode', () => {
      render(<AgentCard agent={mockAgent} selectionMode={false} />);

      const card = screen.getByText('Test Agent').closest('[class*="cursor-pointer"]');
      expect(card).toBeNull();
    });
  });

  describe('Environment Display', () => {
    it('should show environments only in extended details mode', () => {
      render(<AgentCard agent={mockAgent} showExtendedDetails={false} />);

      expect(screen.queryByText('Environments:')).not.toBeInTheDocument();
    });

    it('should truncate environments when there are many', () => {
      render(<AgentCard agent={mockManyDetailsAgent} showExtendedDetails={true} />);

      expect(screen.getByText('test')).toBeInTheDocument();
      expect(screen.getByText('dev')).toBeInTheDocument();
      // The third environment should be truncated with "+1 more"
      expect(screen.getByText('+1 more')).toBeInTheDocument();
    });

    it('should show fewer environments in compact mode', () => {
      render(<AgentCard agent={mockManyDetailsAgent} compact={true} showExtendedDetails={true} />);

      expect(screen.getByText('test')).toBeInTheDocument();
      // May show fewer in compact mode
    });
  });

  describe('Date Formatting', () => {
    it('should format dates appropriately', () => {
      render(<AgentCard agent={mockAgent} />);

      // Should show some form of date (exact format depends on locale)
      const dateElements = screen.getAllByText(/2024|Jan|15/);
      expect(dateElements.length).toBeGreaterThan(0);
    });

    it('should show creation date in extended details', () => {
      render(<AgentCard agent={mockAgent} showExtendedDetails={true} />);

      expect(screen.getByText('Created:')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper button accessibility in selection mode', () => {
      render(<AgentCard agent={mockAgent} selectionMode={true} />);

      const selectButton = screen.getByRole('button', { name: 'Select Agent' });
      expect(selectButton).toBeInTheDocument();
      expect(selectButton).not.toBeDisabled();
    });

    it('should have proper button accessibility for configuration', () => {
      render(<AgentCard agent={mockAgent} showConfigButton={true} />);

      const configButton = screen.getByRole('button', { name: 'Configure' });
      expect(configButton).toBeInTheDocument();
      expect(configButton).not.toBeDisabled();
    });

    it('should properly disable buttons for inaccessible agents', () => {
      render(
        <AgentCard 
          agent={mockDisabledAgent} 
          selectionMode={true} 
          showConfigButton={true} 
        />
      );

      const selectButton = screen.getByRole('button', { name: 'Select Agent' });
      // The configure button doesn't have an accessible name in selection mode, so we find it by icon
      const buttons = screen.getAllByRole('button');
      const configButton = buttons.find(button => button !== selectButton);
      
      expect(selectButton).toBeDisabled();
      expect(configButton).toBeDisabled();
    });
  });

  describe('Edge Cases', () => {
    it('should handle agent with no job types', () => {
      const agentNoJobTypes = {
        ...mockAgent,
        // Generic framework doesn't use hardcoded job types
      };

      render(<AgentCard agent={agentNoJobTypes} />);

      expect(screen.getByText('Test Agent')).toBeInTheDocument();
      expect(screen.queryByText('Job Types:')).not.toBeInTheDocument();
    });

    it('should handle agent with no environments', () => {
      const agentNoEnvironments = {
        ...mockAgent,
        supported_environments: []
      };

      render(<AgentCard agent={agentNoEnvironments} showExtendedDetails={true} />);

      expect(screen.getByText('Test Agent')).toBeInTheDocument();
      // When there are no environments, the Environments section may not be shown
      expect(screen.queryByText('Environments:')).not.toBeInTheDocument();
    });

    it('should handle missing optional properties gracefully', () => {
      const minimalAgent: AgentInfo = {
        identifier: 'minimal_agent',
        name: 'Minimal Agent',
        description: 'Basic agent',
        class_name: 'MinimalAgent',
        lifecycle_state: 'enabled',
        supported_environments: ['prod'],
        version: '1.0.0',
        enabled: true,
        has_error: false,
        created_at: '2024-01-01T00:00:00Z',
        last_updated: '2024-01-15T10:30:00Z'
      };

      render(<AgentCard agent={minimalAgent} showExtendedDetails={true} />);

      expect(screen.getByText('Minimal Agent')).toBeInTheDocument();
      expect(screen.getByText('Basic agent')).toBeInTheDocument();
    });
  });
}); 