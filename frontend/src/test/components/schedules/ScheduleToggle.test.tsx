import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import userEvent from '@testing-library/user-event'
import ScheduleToggle from '../../../components/forms/JobForm/ScheduleToggle'
import { renderWithProviders } from '../../utils'
import '@testing-library/jest-dom'

// Mock responsive hooks
vi.mock('../../../lib/responsive', () => ({
  useBreakpoint: vi.fn(() => ({ isMobile: false })),
  touchButtonSizes: {
    base: 'h-12 w-12',
    sm: 'h-10 w-10',
    md: 'h-8 w-8'
  },
  responsiveTextSizes: {
    xs: 'text-xs sm:text-sm',
    sm: 'text-sm sm:text-base',
    base: 'text-base sm:text-lg',
    lg: 'text-lg sm:text-xl'
  }
}))

const mockOnModeChange = vi.fn()

describe('ScheduleToggle Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders with run now mode selected by default', () => {
    renderWithProviders(
      <ScheduleToggle 
        mode="now" 
        onModeChange={mockOnModeChange} 
      />
    )

    const runNowRadio = screen.getByRole('radio', { name: /run now/i })
    const scheduleRadio = screen.getByRole('radio', { name: /schedule/i })

    expect(runNowRadio).toBeChecked()
    expect(scheduleRadio).not.toBeChecked()
    expect(screen.getByText('Execute immediately')).toBeInTheDocument()
  })

  it('renders with schedule mode selected', () => {
    renderWithProviders(
      <ScheduleToggle 
        mode="schedule" 
        onModeChange={mockOnModeChange} 
      />
    )

    const runNowRadio = screen.getByRole('radio', { name: /run now/i })
    const scheduleRadio = screen.getByRole('radio', { name: /schedule/i })

    expect(scheduleRadio).toBeChecked()
    expect(runNowRadio).not.toBeChecked()
    expect(screen.getByText('Set up recurring execution')).toBeInTheDocument()
  })

  it('calls onModeChange when switching to schedule mode', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(
      <ScheduleToggle 
        mode="now" 
        onModeChange={mockOnModeChange} 
      />
    )

    const scheduleRadio = screen.getByRole('radio', { name: /schedule/i })
    await user.click(scheduleRadio)

    expect(mockOnModeChange).toHaveBeenCalledWith('schedule')
  })

  it('calls onModeChange when switching to run now mode', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(
      <ScheduleToggle 
        mode="schedule" 
        onModeChange={mockOnModeChange} 
      />
    )

    const runNowRadio = screen.getByRole('radio', { name: /run now/i })
    await user.click(runNowRadio)

    expect(mockOnModeChange).toHaveBeenCalledWith('now')
  })

  it('disables the toggle when disabled prop is true', () => {
    renderWithProviders(
      <ScheduleToggle 
        mode="now" 
        onModeChange={mockOnModeChange} 
        disabled={true}
      />
    )

    const runNowRadio = screen.getByRole('radio', { name: /run now/i })
    const scheduleRadio = screen.getByRole('radio', { name: /schedule/i })

    expect(runNowRadio).toBeDisabled()
    expect(scheduleRadio).toBeDisabled()
  })

  it('does not show labels when showLabels is false', () => {
    renderWithProviders(
      <ScheduleToggle 
        mode="now" 
        onModeChange={mockOnModeChange} 
        showLabels={false}
      />
    )

    expect(screen.queryByText('Execute immediately')).not.toBeInTheDocument()
    expect(screen.queryByText('Set up recurring execution')).not.toBeInTheDocument()
  })

  it('applies custom className', () => {
    renderWithProviders(
      <ScheduleToggle 
        mode="now" 
        onModeChange={mockOnModeChange} 
        className="custom-class"
      />
    )

    // Find the main container div by looking for the specific classes that get combined
    const container = document.querySelector('.custom-class')
    expect(container).toBeInTheDocument()
  })

  it('shows correct visual states for different modes', () => {
    const { rerender } = renderWithProviders(
      <ScheduleToggle 
        mode="now" 
        onModeChange={mockOnModeChange} 
      />
    )

    // Check run now mode styling
    expect(screen.getByRole('radio', { name: /run now/i })).toBeChecked()

    // Switch to schedule mode
    rerender(
      <ScheduleToggle 
        mode="schedule" 
        onModeChange={mockOnModeChange} 
      />
    )

    expect(screen.getByRole('radio', { name: /schedule/i })).toBeChecked()
  })

  it('renders lightning icon for run now option', () => {
    const { container } = renderWithProviders(
      <ScheduleToggle 
        mode="now" 
        onModeChange={mockOnModeChange} 
      />
    )

    // Check for SVG with lightning bolt path  
    const lightningPath = container.querySelector('path[d*="M13 10V3L4 14h7v7l9-11h-7z"]')
    expect(lightningPath).toBeInTheDocument()
  })

  it('renders clock icon for schedule option', () => {
    const { container } = renderWithProviders(
      <ScheduleToggle 
        mode="schedule" 
        onModeChange={mockOnModeChange} 
      />
    )

    // Check for SVG with clock path
    const clockPath = container.querySelector('path[d*="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"]')
    expect(clockPath).toBeInTheDocument()
  })

  it('handles keyboard navigation', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(
      <ScheduleToggle 
        mode="now" 
        onModeChange={mockOnModeChange} 
      />
    )

    const runNowRadio = screen.getByRole('radio', { name: /run now/i })
    const scheduleRadio = screen.getByRole('radio', { name: /schedule/i })

    // Focus on run now radio
    await user.tab()
    expect(runNowRadio).toHaveFocus()

    // Use arrow keys to navigate to schedule radio
    await user.keyboard('{ArrowDown}')
    expect(scheduleRadio).toHaveFocus()
    expect(mockOnModeChange).toHaveBeenCalledWith('schedule')
  })
}) 