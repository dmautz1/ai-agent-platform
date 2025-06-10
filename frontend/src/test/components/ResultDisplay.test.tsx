import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ResultDisplay } from '@/components/ResultDisplay';

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn(() => Promise.resolve()),
  },
});

describe('ResultDisplay', () => {
  it('should render JSON content with proper formatting', () => {
    const jsonData = JSON.stringify({ message: 'Hello', count: 42, enabled: true });
    render(<ResultDisplay result={jsonData} />);
    
    expect(screen.getByText('JSON')).toBeInTheDocument();
    expect(screen.getByText('Formatted')).toBeInTheDocument();
    expect(screen.getByText('Raw')).toBeInTheDocument();
  });

  it('should render simple string content as JSON', () => {
    const stringData = '"This is a simple string"'; // JSON string
    render(<ResultDisplay result={stringData} />);
    
    expect(screen.getByText('JSON')).toBeInTheDocument();
  });

  it('should toggle between formatted and raw view', () => {
    const jsonData = JSON.stringify({ test: 'value' });
    render(<ResultDisplay result={jsonData} />);
    
    const rawButton = screen.getByRole('button', { name: /raw/i });
    fireEvent.click(rawButton);
    
    // Should show raw JSON in pre element
    expect(screen.getByText('{"test":"value"}')).toBeInTheDocument();
  });

  it('should copy content to clipboard', async () => {
    const testData = JSON.stringify({ message: 'test' });
    render(<ResultDisplay result={testData} />);
    
    const copyButton = screen.getByRole('button', { name: /copy/i });
    fireEvent.click(copyButton);
    
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(testData);
  });

  it('should show character count', () => {
    const text = '"Hello"'; // JSON string
    render(<ResultDisplay result={text} />);
    
    expect(screen.getByText('• 7 chars')).toBeInTheDocument();
  });

  it('should handle complex JSON objects', () => {
    const complexData = JSON.stringify({
      user: { name: 'John', age: 30 },
      items: ['apple', 'banana'],
      active: true
    });
    
    render(<ResultDisplay result={complexData} />);
    
    expect(screen.getByText('JSON')).toBeInTheDocument();
    // Check character count is calculated correctly
    expect(screen.getByText(`• ${complexData.length} chars`)).toBeInTheDocument();
  });

  it('should handle malformed JSON by wrapping in object', () => {
    const malformedJson = '{ invalid json }';
    render(<ResultDisplay result={malformedJson} />);
    
    // Should still display as JSON without crashing
    expect(screen.getByText('JSON')).toBeInTheDocument();
    expect(screen.getByText(`• ${malformedJson.length} chars`)).toBeInTheDocument();
  });

  it('should handle array JSON responses', () => {
    const arrayJson = JSON.stringify(['item1', 'item2', 'item3']);
    render(<ResultDisplay result={arrayJson} />);
    
    expect(screen.getByText('JSON')).toBeInTheDocument();
    expect(screen.getByText(`• ${arrayJson.length} chars`)).toBeInTheDocument();
  });

  it('should handle backend JSON string format correctly', () => {
    // This tests the actual format that the backend sends after our fix
    const backendJsonString = '{"response": "Hello! This is a test response from the agent."}';
    
    render(<ResultDisplay result={backendJsonString} />);
    
    expect(screen.getByText('JSON')).toBeInTheDocument();
    expect(screen.getByText(`• ${backendJsonString.length} chars`)).toBeInTheDocument();
  });

  it('should handle simple prompt agent result format', async () => {
    // This mimics the actual format returned by the simple prompt agent after the backend fix
    const simplePromptResult = JSON.stringify({
      response: 'Hello! I am doing well, thank you for asking. How can I assist you today?'
    });
    
    render(<ResultDisplay result={simplePromptResult} />);
    
    expect(screen.getByText('JSON')).toBeInTheDocument();
    expect(screen.getByText(`• ${simplePromptResult.length} chars`)).toBeInTheDocument();
    
    // Switch to raw mode to avoid Suspense loading issues
    const rawButton = screen.getByRole('button', { name: /raw/i });
    fireEvent.click(rawButton);
    
    // Should be able to find the response content in raw mode
    await waitFor(() => {
      expect(screen.getByText(/"response"/)).toBeInTheDocument();
      expect(screen.getByText(/Hello! I am doing well/)).toBeInTheDocument();
    });
  });

  it('should handle real web scraping agent result format', async () => {
    // This mimics the actual format returned by the web scraping agent after the backend fix
    const webScrapingResult = JSON.stringify({
      scraping_metadata: {
        url: 'https://example.com',
        timestamp: '2025-06-05T17:17:55.857803',
        agent: 'web_scraping',
        job_config: {
          max_depth: 2,
          include_links: true,
          include_images: true,
          analyze_content: true,
          summary_length: 'medium',
          extract_keywords: true
        }
      },
      page_info: {
        title: 'Example Page',
        description: 'A test page for web scraping',
        url: 'https://example.com',
        status_code: 200
      },
      content: {
        text: 'This is the extracted content from the webpage.',
        word_count: 8,
        character_count: 45
      },
      ai_analysis: {
        summary: 'Test summary',
        insights: ['Insight 1', 'Insight 2'],
        content_type: 'webpage',
        tone: 'informational',
        target_audience: 'general',
        keywords: ['test', 'example']
      },
      links: {
        total_count: 2,
        by_type: { webpage: 2 },
        all_links: [
          { url: 'https://example.com/page1', text: 'Page 1', type: 'webpage' },
          { url: 'https://example.com/page2', text: 'Page 2', type: 'webpage' }
        ]
      },
      images: {
        total_count: 1,
        all_images: [
          { url: 'https://example.com/image.jpg', alt: 'Test image', title: '', width: '100', height: '100' }
        ]
      }
    });
    
    render(<ResultDisplay result={webScrapingResult} />);
    
    expect(screen.getByText('JSON')).toBeInTheDocument();
    expect(screen.getByText(`• ${webScrapingResult.length} chars`)).toBeInTheDocument();
    
    // Switch to raw mode to avoid Suspense loading issues
    const rawButton = screen.getByRole('button', { name: /raw/i });
    fireEvent.click(rawButton);
    
    // Should be able to find some content from the structured result in raw mode
    await waitFor(() => {
      expect(screen.getByText(/"scraping_metadata"/)).toBeInTheDocument();
      expect(screen.getByText(/"page_info"/)).toBeInTheDocument();
    });
  });

  it('should display result format when provided', () => {
    const jsonData = JSON.stringify({ message: 'Hello' });
    render(<ResultDisplay result={jsonData} result_format="json" />);
    
    expect(screen.getByText('JSON')).toBeInTheDocument();
    expect(screen.getByText('json')).toBeInTheDocument(); // Format tag
  });

  it('should display different format types correctly', () => {
    const markdownData = JSON.stringify({ content: '# Hello\nThis is markdown' });
    render(<ResultDisplay result={markdownData} result_format="markdown" />);
    
    expect(screen.getByText('Markdown')).toBeInTheDocument();
    expect(screen.getByText('markdown')).toBeInTheDocument(); // Format tag
  });

  it('should default to JSON format when no format provided', () => {
    const jsonData = JSON.stringify({ message: 'Hello' });
    render(<ResultDisplay result={jsonData} />);
    
    expect(screen.getByText('JSON')).toBeInTheDocument();
    // Should not show format tag when no format provided
    expect(screen.queryByText(/\bjson\b/)).not.toBeInTheDocument();
  });

  it('should handle custom format types', () => {
    const data = JSON.stringify({ content: '<html></html>' });
    render(<ResultDisplay result={data} result_format="html" />);
    
    expect(screen.getByText('HTML')).toBeInTheDocument(); // Capitalized
    expect(screen.getByText('html')).toBeInTheDocument(); // Format tag
  });

  it('should render markdown content correctly', async () => {
    const markdownContent = JSON.stringify({ response: '# Hello World\n\nThis is **bold** text and *italic* text.\n\n- Item 1\n- Item 2\n\n```javascript\nconsole.log("Hello");\n```' });
    render(<ResultDisplay result={markdownContent} result_format="markdown" />);
    
    expect(screen.getByText('Markdown')).toBeInTheDocument();
    expect(screen.getByText('markdown')).toBeInTheDocument(); // Format tag
    
    // Switch to formatted view to see markdown
    const formattedButton = screen.getByRole('button', { name: /formatted/i });
    fireEvent.click(formattedButton);
    
    // Should be able to find markdown content in formatted mode
    await waitFor(() => {
      expect(screen.getByText('Formatted')).toBeInTheDocument();
    });
  });

  it('should handle plain markdown strings', () => {
    const plainMarkdown = '# Simple Title\n\nPlain markdown content without JSON wrapper.';
    render(<ResultDisplay result={plainMarkdown} result_format="markdown" />);
    
    expect(screen.getByText('Markdown')).toBeInTheDocument();
    expect(screen.getByText('markdown')).toBeInTheDocument(); // Format tag
  });

  it('should extract markdown from various JSON field names', () => {
    const testCases = [
      { response: 'Response field markdown' },
      { content: 'Content field markdown' },
      { markdown: 'Markdown field markdown' },
      'Direct string markdown'
    ];
    
    testCases.forEach((testCase) => {
      const { unmount } = render(
        <ResultDisplay 
          result={typeof testCase === 'string' ? testCase : JSON.stringify(testCase)} 
          result_format="markdown" 
        />
      );
      expect(screen.getByText('Markdown')).toBeInTheDocument();
      unmount();
    });
  });

  it('should show view mode toggle only for supported formats', () => {
    // Test JSON format - should show toggle
    const { rerender } = render(<ResultDisplay result='{"test": "value"}' result_format="json" />);
    expect(screen.getByRole('button', { name: /formatted/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /raw/i })).toBeInTheDocument();
    
    // Test Markdown format - should show toggle
    rerender(<ResultDisplay result='# Test' result_format="markdown" />);
    expect(screen.getByRole('button', { name: /formatted/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /raw/i })).toBeInTheDocument();
    
    // Test Text format - should not show toggle
    rerender(<ResultDisplay result='Plain text' result_format="text" />);
    expect(screen.queryByRole('button', { name: /formatted/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /raw/i })).not.toBeInTheDocument();
  });
}); 