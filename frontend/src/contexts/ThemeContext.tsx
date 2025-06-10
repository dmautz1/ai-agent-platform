import { createContext, useContext } from 'react';
import { ThemeProvider as NextThemesProvider } from 'next-themes';

type Theme = 'dark' | 'light';

type ThemeProviderContextType = {
  theme: string;
  setTheme: (theme: Theme) => void;
};

const ThemeProviderContext = createContext<ThemeProviderContextType | undefined>(undefined);

// eslint-disable-next-line react-refresh/only-export-components
export const useTheme = () => {
  const context = useContext(ThemeProviderContext);

  if (context === undefined)
    throw new Error('useTheme must be used within a ThemeProvider');

  return context;
}

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: Theme;
  storageKey?: string;
}

export function ThemeProvider({
  children,
  defaultTheme = 'light',
  storageKey = 'vite-ui-theme',
  ...props
}: ThemeProviderProps) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme={defaultTheme}
      enableSystem={false}
      disableTransitionOnChange
      storageKey={storageKey}
      {...props}
    >
      {children}
    </NextThemesProvider>
  );
} 