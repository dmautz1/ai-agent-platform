import { useState, useEffect } from 'react';

// Breakpoint definitions matching Tailwind CSS
export const breakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
} as const;

export type Breakpoint = keyof typeof breakpoints;

/**
 * Hook to detect current screen size and breakpoint
 */
export const useBreakpoint = () => {
  const [breakpoint, setBreakpoint] = useState<Breakpoint>('2xl');
  const [isMobile, setIsMobile] = useState(false);
  const [isTablet, setIsTablet] = useState(false);
  const [isDesktop, setIsDesktop] = useState(true);

  useEffect(() => {
    const calculateBreakpoint = () => {
      const width = window.innerWidth;
      
      if (width < breakpoints.sm) {
        setBreakpoint('sm');
        setIsMobile(true);
        setIsTablet(false);
        setIsDesktop(false);
      } else if (width < breakpoints.md) {
        setBreakpoint('sm');
        setIsMobile(true);
        setIsTablet(false);
        setIsDesktop(false);
      } else if (width < breakpoints.lg) {
        setBreakpoint('md');
        setIsMobile(false);
        setIsTablet(true);
        setIsDesktop(false);
      } else if (width < breakpoints.xl) {
        setBreakpoint('lg');
        setIsMobile(false);
        setIsTablet(false);
        setIsDesktop(true);
      } else if (width < breakpoints['2xl']) {
        setBreakpoint('xl');
        setIsMobile(false);
        setIsTablet(false);
        setIsDesktop(true);
      } else {
        setBreakpoint('2xl');
        setIsMobile(false);
        setIsTablet(false);
        setIsDesktop(true);
      }
    };

    calculateBreakpoint();
    window.addEventListener('resize', calculateBreakpoint);
    
    return () => window.removeEventListener('resize', calculateBreakpoint);
  }, []);

  return {
    breakpoint,
    isMobile,
    isTablet,
    isDesktop,
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
  };
};

/**
 * Hook for responsive values based on breakpoints
 */
export const useResponsiveValue = <T>(values: Partial<Record<Breakpoint, T>>): T | undefined => {
  const { breakpoint } = useBreakpoint();
  
  // Find the value for current breakpoint or closest smaller one
  const breakpointOrder: Breakpoint[] = ['sm', 'md', 'lg', 'xl', '2xl'];
  const currentIndex = breakpointOrder.indexOf(breakpoint);
  
  for (let i = currentIndex; i >= 0; i--) {
    const bp = breakpointOrder[i];
    if (values[bp] !== undefined) {
      return values[bp];
    }
  }
  
  return undefined;
};

/**
 * Hook to detect if device supports touch
 */
export const useTouchDevice = () => {
  const [isTouch, setIsTouch] = useState(false);

  useEffect(() => {
    const checkTouch = () => {
      setIsTouch('ontouchstart' in window || navigator.maxTouchPoints > 0);
    };

    checkTouch();
    window.addEventListener('touchstart', checkTouch, { once: true });
    
    return () => window.removeEventListener('touchstart', checkTouch);
  }, []);

  return isTouch;
};

/**
 * Responsive container class generator
 */
export const getResponsiveContainer = (customClasses?: string) => {
  return `container mx-auto px-4 sm:px-6 lg:px-8 ${customClasses || ''}`.trim();
};

/**
 * Responsive grid class generator
 */
export const getResponsiveGrid = (
  columns: Partial<Record<Breakpoint, number>>,
  gap = 4
) => {
  const classes = [`grid gap-${gap}`];
  
  Object.entries(columns).forEach(([bp, cols]) => {
    if (bp === 'sm') {
      classes.push(`grid-cols-${cols}`);
    } else {
      classes.push(`${bp}:grid-cols-${cols}`);
    }
  });
  
  return classes.join(' ');
};

/**
 * Responsive text size classes
 */
export const responsiveTextSizes = {
  xs: 'text-xs',
  sm: 'text-xs sm:text-sm',
  base: 'text-sm sm:text-base',
  lg: 'text-base sm:text-lg',
  xl: 'text-lg sm:text-xl',
  '2xl': 'text-xl sm:text-2xl',
  '3xl': 'text-2xl sm:text-3xl',
  '4xl': 'text-3xl sm:text-4xl',
} as const;

/**
 * Touch-friendly button sizes
 */
export const touchButtonSizes = {
  sm: 'h-10 px-4 sm:h-8 sm:px-3', // Larger on mobile
  default: 'h-12 px-6 sm:h-9 sm:px-4',
  lg: 'h-14 px-8 sm:h-10 sm:px-6',
} as const;

/**
 * Mobile-first spacing utilities
 */
export const responsiveSpacing = {
  section: 'py-8 sm:py-12 lg:py-16',
  component: 'py-4 sm:py-6 lg:py-8',
  element: 'py-2 sm:py-3 lg:py-4',
} as const;

/**
 * Responsive padding for containers
 */
export const responsivePadding = {
  page: 'p-4 sm:p-6 lg:p-8',
  section: 'px-4 py-6 sm:px-6 sm:py-8 lg:px-8 lg:py-12',
  card: 'p-4 sm:p-6',
} as const;

/**
 * Mobile navigation helpers
 */
export const mobileNavigation = {
  drawer: 'fixed inset-y-0 left-0 z-50 w-full max-w-xs transform bg-background shadow-xl transition-transform duration-300 ease-in-out',
  overlay: 'fixed inset-0 z-40 bg-black bg-opacity-25 transition-opacity duration-300 ease-in-out',
  trigger: 'inline-flex h-12 w-12 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-ring lg:hidden',
} as const;

/**
 * Responsive table utilities
 */
export const responsiveTable = {
  container: 'overflow-x-auto scrollbar-thin scrollbar-thumb-border scrollbar-track-background',
  cell: 'px-3 py-4 sm:px-4 sm:py-3 text-sm',
  header: 'px-3 py-3 sm:px-4 sm:py-4 text-xs font-medium uppercase tracking-wider',
  mobileCard: 'block rounded-lg border bg-card p-4 shadow-sm sm:hidden',
  desktopTable: 'hidden sm:table',
} as const;

/**
 * Form responsive utilities
 */
export const responsiveForm = {
  container: 'space-y-4 sm:space-y-6',
  field: 'space-y-1 sm:space-y-2',
  input: 'h-12 px-4 text-base sm:h-9 sm:px-3 sm:text-sm',
  label: 'text-sm font-medium sm:text-sm',
  button: 'h-12 px-6 text-base font-medium sm:h-9 sm:px-4 sm:text-sm',
} as const;

/**
 * Modal/Dialog responsive utilities
 */
export const responsiveDialog = {
  overlay: 'fixed inset-0 z-50 bg-background/80 backdrop-blur-sm',
  content: 'fixed left-[50%] top-[50%] z-50 w-full max-w-[calc(100vw-2rem)] max-h-[calc(100vh-2rem)] translate-x-[-50%] translate-y-[-50%] border bg-background shadow-lg duration-200 sm:max-w-lg sm:rounded-lg',
  mobileFullScreen: 'h-full w-full rounded-none sm:h-auto sm:rounded-lg',
  header: 'px-4 py-6 sm:px-6',
  body: 'px-4 pb-4 sm:px-6 sm:pb-6',
} as const; 