import React, { useState, Suspense, lazy } from 'react';
import { useTheme } from 'next-themes';
import { darkTheme } from '@uiw/react-json-view/dark';
import { lightTheme } from '@uiw/react-json-view/light';
import { Button } from '@/components/ui/button';
import { 
  Eye, 
  Code, 
  FileJson,
  FileText,
  Copy,
  Check
} from 'lucide-react';

// Dynamic imports for heavy components
const JsonView = lazy(() => import('@uiw/react-json-view').then(mod => ({ default: mod.default })));
const ReactMarkdown = lazy(() => import('react-markdown'));

// Loading component for suspense fallbacks
const LoadingSpinner = () => (
  <div className="flex items-center justify-center p-4">
    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900 dark:border-gray-100"></div>
  </div>
);

// Markdown Display Component
const MarkdownDisplay: React.FC<{ content: string }> = ({ content }) => {
  const { theme } = useTheme();
  
  // Extract markdown content from JSON if needed
  const getMarkdownContent = (content: string): string => {
    try {
      const parsed = JSON.parse(content);
      // Check for common markdown content fields
      if (typeof parsed === 'string') {
        return parsed;
      } else if (parsed.response && typeof parsed.response === 'string') {
        return parsed.response;
      } else if (parsed.content && typeof parsed.content === 'string') {
        return parsed.content;
      } else if (parsed.markdown && typeof parsed.markdown === 'string') {
        return parsed.markdown;
      } else {
        // If it's an object with unknown structure, convert to readable text
        return JSON.stringify(parsed, null, 2);
      }
    } catch {
      // If not JSON, treat as plain markdown
      return content;
    }
  };

  const markdownContent = getMarkdownContent(content);
  
  return (
    <div className={`p-4 ${
      theme === 'dark' 
        ? 'prose prose-sm prose-invert max-w-none prose-headings:text-white prose-p:text-gray-300 prose-strong:text-white prose-code:text-gray-300 prose-pre:bg-gray-800' 
        : 'prose prose-sm prose-gray max-w-none'
    } markdown-content`}>
      <Suspense fallback={<LoadingSpinner />}>
        <ReactMarkdown
          components={{
            // Custom styling for code blocks
            code: ({ children, className, ...props }: any) => {
              const isInline = !className?.includes('language-');
              return isInline ? (
                <code
                  className={`${className || ''} px-1 py-0.5 rounded text-xs font-mono ${
                    theme === 'dark' 
                      ? 'bg-gray-800 text-gray-300' 
                      : 'bg-gray-100 text-gray-800'
                  }`}
                  {...props}
                >
                  {children}
                </code>
              ) : (
                <pre className={`${className || ''} p-3 rounded-md overflow-x-auto ${
                  theme === 'dark' 
                    ? 'bg-gray-800 text-gray-300' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  <code {...props}>{children}</code>
                </pre>
              );
            },
            // Custom styling for headings
            h1: ({ children, ...props }: any) => (
              <h1 className={`text-2xl font-bold mb-4 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`} {...props}>
                {children}
              </h1>
            ),
            h2: ({ children, ...props }: any) => (
              <h2 className={`text-xl font-semibold mb-3 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`} {...props}>
                {children}
              </h2>
            ),
            h3: ({ children, ...props }: any) => (
              <h3 className={`text-lg font-medium mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`} {...props}>
                {children}
              </h3>
            ),
            // Custom styling for paragraphs
            p: ({ children, ...props }: any) => (
              <p className={`mb-4 leading-relaxed ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`} {...props}>
                {children}
              </p>
            ),
            // Custom styling for lists
            ul: ({ children, ...props }: any) => (
              <ul className={`list-disc list-inside mb-4 space-y-1 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`} {...props}>
                {children}
              </ul>
            ),
            ol: ({ children, ...props }: any) => (
              <ol className={`list-decimal list-inside mb-4 space-y-1 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`} {...props}>
                {children}
              </ol>
            ),
            li: ({ children, ...props }: any) => (
              <li className="mb-1" {...props}>
                {children}
              </li>
            ),
            // Custom styling for blockquotes
            blockquote: ({ children, ...props }: any) => (
              <blockquote 
                className={`border-l-4 pl-4 py-2 my-4 italic ${
                  theme === 'dark' 
                    ? 'border-gray-600 bg-gray-800/50 text-gray-300' 
                    : 'border-gray-300 bg-gray-50 text-gray-700'
                }`}
                {...props}
              >
                {children}
              </blockquote>
            ),
            // Custom styling for strong/bold text
            strong: ({ children, ...props }: any) => (
              <strong className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`} {...props}>
                {children}
              </strong>
            ),
            // Custom styling for emphasis/italic text  
            em: ({ children, ...props }: any) => (
              <em className={`italic ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`} {...props}>
                {children}
              </em>
            ),
            // Custom styling for links
            a: ({ children, ...props }: any) => (
              <a 
                className={`underline hover:no-underline ${
                  theme === 'dark' 
                    ? 'text-blue-400 hover:text-blue-300' 
                    : 'text-blue-600 hover:text-blue-800'
                }`}
                {...props}
              >
                {children}
              </a>
            ),
            // Custom styling for tables
            table: ({ children, ...props }: any) => (
              <div className="overflow-x-auto my-4">
                <table 
                  className={`min-w-full border-collapse ${
                    theme === 'dark' ? 'border-gray-700' : 'border-gray-300'
                  }`}
                  {...props}
                >
                  {children}
                </table>
              </div>
            ),
            th: ({ children, ...props }: any) => (
              <th 
                className={`border px-3 py-2 text-left font-semibold ${
                  theme === 'dark' 
                    ? 'border-gray-700 bg-gray-800 text-white' 
                    : 'border-gray-300 bg-gray-100 text-gray-900'
                }`}
                {...props}
              >
                {children}
              </th>
            ),
            td: ({ children, ...props }: any) => (
              <td 
                className={`border px-3 py-2 ${
                  theme === 'dark' 
                    ? 'border-gray-700 text-gray-300' 
                    : 'border-gray-300 text-gray-700'
                }`}
                {...props}
              >
                {children}
              </td>
            ),
            // Custom styling for horizontal rule
            hr: ({ ...props }: any) => (
              <hr 
                className={`my-6 border-t ${
                  theme === 'dark' ? 'border-gray-600' : 'border-gray-300'
                }`}
                {...props}
              />
            ),
          }}
        >
          {markdownContent}
        </ReactMarkdown>
      </Suspense>
    </div>
  );
};

interface ResultDisplayProps {
  result: string; // Always expect a string containing data
  result_format?: string; // Format of the result data
  className?: string;
}

export const ResultDisplay: React.FC<ResultDisplayProps> = ({ result, result_format, className }) => {
  const { theme } = useTheme();
  const [viewMode, setViewMode] = useState<'formatted' | 'raw'>('formatted');
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied'>('idle');
  
  // Parse JSON safely - result is always a string containing JSON or other data
  const parseJsonSafely = (jsonString: string) => {
    try {
      return JSON.parse(jsonString);
    } catch {
      // If parsing fails, wrap the string in an object to prevent character-by-character display
      return { value: jsonString, _isStringValue: true };
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(result);
      setCopyStatus('copied');
      setTimeout(() => setCopyStatus('idle'), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  // Get display format and icon
  const getFormatInfo = () => {
    const format = result_format || 'json';
    const formatDisplay = format.charAt(0).toUpperCase() + format.slice(1);
    
    switch (format.toLowerCase()) {
      case 'json':
        return { display: 'JSON', icon: FileJson };
      case 'markdown':
        return { display: 'Markdown', icon: FileText };
      case 'text':
        return { display: 'Text', icon: FileText };
      case 'html':
        return { display: 'HTML', icon: FileJson };
      default:
        return { display: formatDisplay, icon: FileJson };
    }
  };

  const formatInfo = getFormatInfo();
  const FormatIcon = formatInfo.icon;

  const jsonData = parseJsonSafely(result);

  // Determine if we should show formatted view for this format
  const hasFormattedView = ['json', 'markdown'].includes((result_format || 'json').toLowerCase());

  return (
    <div className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-md border">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 text-sm font-medium text-blue-600 dark:text-blue-400">
            <FormatIcon className="h-4 w-4" />
            <span>{formatInfo.display}</span>
          </div>
          <div className="text-xs text-muted-foreground">
            • {result.length} chars
            {result_format && (
              <span className="ml-1 px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs font-medium">
                {result_format}
              </span>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Copy Button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={copyToClipboard}
            className="h-8 px-2 text-xs"
          >
            {copyStatus === 'copied' ? (
              <>
                <Check className="h-3 w-3 mr-1 text-green-600" />
                Copied
              </>
            ) : (
              <>
                <Copy className="h-3 w-3 mr-1" />
                Copy
              </>
            )}
          </Button>
          
          {/* View Mode Toggle - only show if we have a formatted view */}
          {hasFormattedView && (
            <div className="flex items-center gap-1 border rounded-md p-1">
              <Button
                variant={viewMode === 'formatted' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('formatted')}
                className="h-6 px-2 text-xs"
              >
                <Eye className="h-3 w-3 mr-1" />
                Formatted
              </Button>
              <Button
                variant={viewMode === 'raw' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('raw')}
                className="h-6 px-2 text-xs"
              >
                <Code className="h-3 w-3 mr-1" />
                Raw
              </Button>
            </div>
          )}
        </div>
      </div>
      
      {/* Content Display */}
      <div className="border rounded-md overflow-hidden">
        <div className="max-h-96 overflow-auto">
          {viewMode === 'formatted' && hasFormattedView ? (
            <div className="rounded-md overflow-hidden">
              <Suspense fallback={<LoadingSpinner />}>
                {result_format?.toLowerCase() === 'json' && (
                  <JsonView 
                    value={jsonData}
                    displayDataTypes={false}
                    displayObjectSize={true}
                    enableClipboard={false}
                    collapsed={false}
                    shortenTextAfterLength={100}
                    style={theme === 'dark' ? darkTheme : lightTheme}
                    className={'p-4'}
                  />
                )}
                {result_format?.toLowerCase() === 'markdown' && (
                  <MarkdownDisplay content={result} />
                )}
              </Suspense>
            </div>
          ) : (
            <div className="p-4 bg-muted">
              <pre className="text-sm whitespace-pre-wrap break-words font-mono">
                {result}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}; 