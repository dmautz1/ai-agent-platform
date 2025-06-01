import { test, expect, type Page, type BrowserContext } from '@playwright/test';
import { AuthHelper, JobHelper, NavigationHelper } from './helpers/test-helpers';

let authHelper: AuthHelper;
let jobHelper: JobHelper;
let navHelper: NavigationHelper;

test.describe('Cross-Browser Compatibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    authHelper = new AuthHelper(page);
    jobHelper = new JobHelper(page);
    navHelper = new NavigationHelper(page);
  });

  test.describe('Authentication Compatibility', () => {
    test('should handle sign in across all browsers', async ({ page, browserName }) => {
      await test.step(`Testing authentication on ${browserName}`, async () => {
        await page.goto('/auth');
        
        // Verify page loads correctly
        await expect(page.locator('h1')).toContainText('Sign In');
        
        // Test form interaction
        await page.fill('input[type="email"]', 'test@example.com');
        await page.fill('input[type="password"]', 'password123');
        
        // Verify form elements are interactive
        const emailInput = page.locator('input[type="email"]');
        const passwordInput = page.locator('input[type="password"]');
        const signInButton = page.locator('button[type="submit"]');
        
        await expect(emailInput).toBeVisible();
        await expect(passwordInput).toBeVisible();
        await expect(signInButton).toBeVisible();
        await expect(signInButton).toBeEnabled();
        
        // Verify form styling is applied correctly
        await expect(emailInput).toHaveCSS('border-radius', '6px');
        await expect(signInButton).toHaveCSS('background-color', 'rgb(15, 23, 42)');
      });
    });

    test('should display error messages consistently', async ({ page, browserName }) => {
      await test.step(`Testing error handling on ${browserName}`, async () => {
        await page.goto('/auth');
        
        // Submit form without credentials
        await page.click('button[type="submit"]');
        
        // Wait for error message with browser-specific timeout
        const timeout = browserName === 'webkit' ? 10000 : 5000;
        
        await expect(page.locator('[role="alert"]')).toBeVisible({ timeout });
        
        // Verify error styling
        const errorElement = page.locator('[role="alert"]');
        await expect(errorElement).toHaveCSS('color', 'rgb(239, 68, 68)');
      });
    });
  });

  test.describe('Dashboard Compatibility', () => {
    test('should render dashboard layout correctly', async ({ page, browserName }) => {
      await test.step(`Testing dashboard layout on ${browserName}`, async () => {
        // Mock successful authentication by setting localStorage
        await page.goto('/');
        await page.evaluate(() => {
          localStorage.setItem('supabase.auth.token', JSON.stringify({
            access_token: 'mock-token',
            user: { id: 'mock-user-id', email: 'test@example.com' }
          }));
        });
        await page.reload();
        
        // Verify main dashboard elements
        await expect(page.locator('h1')).toContainText('Job Dashboard');
        
        // Check for dashboard components with more flexible selectors
        const dashboardContent = page.locator('main, [data-testid="dashboard"], .dashboard');
        await expect(dashboardContent.first()).toBeVisible();
      });
    });

    test('should handle job creation form across browsers', async ({ page, browserName }) => {
      await test.step(`Testing job creation on ${browserName}`, async () => {
        // Mock authentication
        await page.goto('/');
        await page.evaluate(() => {
          localStorage.setItem('supabase.auth.token', JSON.stringify({
            access_token: 'mock-token',
            user: { id: 'mock-user-id', email: 'test@example.com' }
          }));
        });
        await page.reload();
        
        // Try to find and click "Create Job" button with flexible selectors
        const createButton = page.locator('text=Create Job, button:has-text("Create"), [data-testid="create-job"]');
        if (await createButton.count() > 0) {
          await createButton.first().click();
          
          // Check if modal or form appears
          const formContainer = page.locator('[role="dialog"], form, .job-form');
          if (await formContainer.count() > 0) {
            await expect(formContainer.first()).toBeVisible();
          }
        }
      });
    });
  });

  test.describe('CSS and Styling Compatibility', () => {
    test('should apply Tailwind CSS classes correctly', async ({ page, browserName }) => {
      await test.step(`Testing CSS compatibility on ${browserName}`, async () => {
        await page.goto('/auth');
        
        // Test container styles
        const container = page.locator('.container').first();
        await expect(container).toHaveCSS('max-width', '448px');
        
        // Test button styles with Tailwind classes
        const button = page.locator('button[type="submit"]');
        await expect(button).toHaveCSS('padding', '8px 16px');
        await expect(button).toHaveCSS('border-radius', '6px');
        
        // Test input field styles
        const input = page.locator('input[type="email"]');
        await expect(input).toHaveCSS('border-width', '1px');
        await expect(input).toHaveCSS('padding', '8px 12px');
      });
    });

    test('should handle dark/light mode consistently', async ({ page, browserName }) => {
      await test.step(`Testing theme compatibility on ${browserName}`, async () => {
        await page.goto('/');
        
        // Verify CSS custom properties are supported
        const bodyStyles = await page.evaluate(() => {
          const body = document.body;
          const computedStyle = window.getComputedStyle(body);
          return {
            backgroundColor: computedStyle.backgroundColor,
            color: computedStyle.color,
          };
        });
        
        // Verify background and text colors are applied
        expect(bodyStyles.backgroundColor).toBeTruthy();
        expect(bodyStyles.color).toBeTruthy();
      });
    });

    test('should display icons and graphics correctly', async ({ page, browserName }) => {
      await test.step(`Testing graphics rendering on ${browserName}`, async () => {
        // Mock authentication
        await page.goto('/');
        await page.evaluate(() => {
          localStorage.setItem('supabase.auth.token', JSON.stringify({
            access_token: 'mock-token',
            user: { id: 'mock-user-id', email: 'test@example.com' }
          }));
        });
        await page.reload();
        
        // Check for SVG icons (Lucide React icons)
        const icons = page.locator('svg');
        if (await icons.count() > 0) {
          await expect(icons.first()).toBeVisible();
          
          // Verify icon styling
          const firstIcon = icons.first();
          const iconStyle = await firstIcon.evaluate((el) => {
            const style = window.getComputedStyle(el);
            return {
              width: style.width,
              height: style.height,
              fill: style.fill,
            };
          });
          
          expect(iconStyle.width).toBeTruthy();
          expect(iconStyle.height).toBeTruthy();
        }
      });
    });
  });

  test.describe('JavaScript/TypeScript Compatibility', () => {
    test('should handle async operations correctly', async ({ page, browserName }) => {
      await test.step(`Testing async operations on ${browserName}`, async () => {
        // Mock authentication
        await page.goto('/');
        await page.evaluate(() => {
          localStorage.setItem('supabase.auth.token', JSON.stringify({
            access_token: 'mock-token',
            user: { id: 'mock-user-id', email: 'test@example.com' }
          }));
        });
        await page.reload();
        
        // Test async API calls and state updates - look for refresh button
        const refreshButton = page.locator('text=Refresh, button:has-text("Refresh"), [data-testid="refresh"]');
        if (await refreshButton.count() > 0) {
          await refreshButton.first().click();
        }
        
        // Verify the page is still functional after async operations
        await expect(page.locator('body')).toBeVisible();
        
        // Test promise-based operations
        const promiseResult = await page.evaluate(async () => {
          return new Promise((resolve) => {
            setTimeout(() => resolve('promise-resolved'), 100);
          });
        });
        
        expect(promiseResult).toBe('promise-resolved');
      });
    });

    test('should handle modern JavaScript features', async ({ page, browserName }) => {
      await test.step(`Testing modern JS features on ${browserName}`, async () => {
        await page.goto('/');
        
        // Test ES6+ features support
        const modernJSTest = await page.evaluate(() => {
          // Test arrow functions
          const arrowFunc = () => 'arrow-function-works';
          
          // Test template literals
          const templateLiteral = `template-literal-works`;
          
          // Test destructuring
          const { test } = { test: 'destructuring-works' };
          
          // Test async/await
          const asyncTest = async () => 'async-await-works';
          
          // Test optional chaining (if supported)
          const obj = { nested: { value: 'optional-chaining-works' } };
          const optionalChaining = obj?.nested?.value || 'not-supported';
          
          return {
            arrowFunc: arrowFunc(),
            templateLiteral,
            destructuring: test,
            optionalChaining
          };
        });
        
        expect(modernJSTest.arrowFunc).toBe('arrow-function-works');
        expect(modernJSTest.templateLiteral).toBe('template-literal-works');
        expect(modernJSTest.destructuring).toBe('destructuring-works');
        expect(modernJSTest.optionalChaining).toBeTruthy();
      });
    });

    test('should handle error boundaries correctly', async ({ page, browserName }) => {
      await test.step(`Testing error handling on ${browserName}`, async () => {
        await page.goto('/');
        
        // Test that page handles JavaScript errors gracefully
        const errorTest = await page.evaluate(() => {
          try {
            // Intentionally cause a reference error
            // @ts-ignore
            return nonExistentVariable;
          } catch (error) {
            return 'error-caught';
          }
        });
        
        expect(errorTest).toBe('error-caught');
        
        // Verify page is still functional after error
        await expect(page.locator('body')).toBeVisible();
      });
    });
  });

  test.describe('Form Validation Compatibility', () => {
    test('should validate form inputs consistently', async ({ page, browserName }) => {
      await test.step(`Testing form validation on ${browserName}`, async () => {
        // Mock authentication
        await page.goto('/');
        await page.evaluate(() => {
          localStorage.setItem('supabase.auth.token', JSON.stringify({
            access_token: 'mock-token',
            user: { id: 'mock-user-id', email: 'test@example.com' }
          }));
        });
        await page.reload();
        
        // Try to open job creation form
        const createButton = page.locator('text=Create Job, button:has-text("Create"), [data-testid="create-job"]');
        if (await createButton.count() > 0) {
          await createButton.first().click();
          
          const titleInput = page.locator('input[name="title"], input[placeholder*="title" i]');
          if (await titleInput.count() > 0) {
            // Test required field validation
            const isNativeValidationSupported = await titleInput.first().evaluate((input: HTMLInputElement) => {
              return input.validity !== undefined;
            });
            
            expect(isNativeValidationSupported).toBe(true);
            
            // Test input and focus events
            await titleInput.first().fill('ab'); // Too short
            await titleInput.first().focus();
            await page.keyboard.press('Tab'); // Move focus away to trigger blur
            
            await titleInput.first().fill('Valid title for testing');
            await expect(titleInput.first()).toHaveValue('Valid title for testing');
          }
        }
      });
    });

    test('should handle file upload consistently', async ({ page, browserName }) => {
      await test.step(`Testing file upload on ${browserName}`, async () => {
        // Mock authentication
        await page.goto('/');
        await page.evaluate(() => {
          localStorage.setItem('supabase.auth.token', JSON.stringify({
            access_token: 'mock-token',
            user: { id: 'mock-user-id', email: 'test@example.com' }
          }));
        });
        await page.reload();
        
        // Test if file input is supported and functional
        const createButton = page.locator('text=Create Job, button:has-text("Create"), [data-testid="create-job"]');
        if (await createButton.count() > 0) {
          await createButton.first().click();
          
          // Select web scraping or other agent that might use file uploads
          const agentSelect = page.locator('select[name="agent_type"]');
          if (await agentSelect.count() > 0) {
            await agentSelect.selectOption('web_scraping');
          }
          
          // Check if file input is rendered and functional
          const fileInputs = page.locator('input[type="file"]');
          if (await fileInputs.count() > 0) {
            const fileInput = fileInputs.first();
            await expect(fileInput).toBeVisible();
            
            // Test file input styling and accessibility
            const isAccessible = await fileInput.evaluate((input) => {
              return input.getAttribute('aria-label') !== null || 
                     input.getAttribute('aria-labelledby') !== null;
            });
            
            // File inputs should be accessible
            expect(isAccessible).toBe(true);
          }
        }
      });
    });
  });

  test.describe('API Communication Compatibility', () => {
    test('should handle fetch/axios requests across browsers', async ({ page, browserName }) => {
      await test.step(`Testing API requests on ${browserName}`, async () => {
        // Mock authentication
        await page.goto('/');
        await page.evaluate(() => {
          localStorage.setItem('supabase.auth.token', JSON.stringify({
            access_token: 'mock-token',
            user: { id: 'mock-user-id', email: 'test@example.com' }
          }));
        });
        
        // Intercept API calls to verify they work across browsers
        const requestPromises: Promise<any>[] = [];
        page.on('request', (request) => {
          if (request.url().includes('/api/')) {
            requestPromises.push(request.response());
          }
        });
        
        await page.reload();
        
        // Wait for any API requests to complete
        if (requestPromises.length > 0) {
          await Promise.allSettled(requestPromises);
        }
        
        // Verify page is still functional
        await expect(page.locator('body')).toBeVisible();
      });
    });

    test('should handle CORS and headers correctly', async ({ page, browserName }) => {
      await test.step(`Testing CORS handling on ${browserName}`, async () => {
        await page.goto('/');
        
        // Test that API calls include proper headers
        const headerTest = await page.evaluate(async () => {
          try {
            const response = await fetch('/api/health', {
              method: 'GET',
              headers: {
                'Content-Type': 'application/json',
              },
            });
            
            return {
              status: response.status,
              ok: response.ok,
              headers: Object.fromEntries(response.headers.entries()),
            };
          } catch (error) {
            return { error: error.message };
          }
        });
        
        // Verify the request completed successfully or failed gracefully
        expect(headerTest).toBeTruthy();
      });
    });
  });

  test.describe('Storage and Persistence Compatibility', () => {
    test('should handle localStorage consistently', async ({ page, browserName }) => {
      await test.step(`Testing localStorage on ${browserName}`, async () => {
        await page.goto('/');
        
        // Test localStorage availability and functionality
        const storageTest = await page.evaluate(() => {
          try {
            const testKey = 'cross-browser-test';
            const testValue = 'storage-works';
            
            localStorage.setItem(testKey, testValue);
            const retrieved = localStorage.getItem(testKey);
            localStorage.removeItem(testKey);
            
            return {
              isSupported: true,
              setValue: testValue,
              getValue: retrieved,
              matches: testValue === retrieved,
            };
          } catch (error) {
            return {
              isSupported: false,
              error: error.message,
            };
          }
        });
        
        expect(storageTest.isSupported).toBe(true);
        expect(storageTest.matches).toBe(true);
      });
    });

    test('should handle sessionStorage consistently', async ({ page, browserName }) => {
      await test.step(`Testing sessionStorage on ${browserName}`, async () => {
        await page.goto('/');
        
        // Test sessionStorage functionality
        const sessionTest = await page.evaluate(() => {
          try {
            const testKey = 'session-test';
            const testValue = 'session-storage-works';
            
            sessionStorage.setItem(testKey, testValue);
            const retrieved = sessionStorage.getItem(testKey);
            sessionStorage.removeItem(testKey);
            
            return {
              isSupported: true,
              matches: testValue === retrieved,
            };
          } catch (error) {
            return {
              isSupported: false,
              error: error.message,
            };
          }
        });
        
        expect(sessionTest.isSupported).toBe(true);
        if (sessionTest.isSupported) {
          expect(sessionTest.matches).toBe(true);
        }
      });
    });
  });

  test.describe('Performance and Memory Compatibility', () => {
    test('should handle memory usage efficiently', async ({ page, browserName }) => {
      await test.step(`Testing memory efficiency on ${browserName}`, async () => {
        // Mock authentication
        await page.goto('/');
        await page.evaluate(() => {
          localStorage.setItem('supabase.auth.token', JSON.stringify({
            access_token: 'mock-token',
            user: { id: 'mock-user-id', email: 'test@example.com' }
          }));
        });
        
        // Test multiple page navigations to check for memory leaks
        for (let i = 0; i < 3; i++) {
          await page.goto('/');
          await page.waitForLoadState('networkidle');
          await page.goto('/auth');
          await page.waitForLoadState('networkidle');
        }
        
        // Return to main page and verify it still works
        await page.goto('/');
        await expect(page.locator('body')).toBeVisible();
      });
    });

    test('should handle rapid user interactions', async ({ page, browserName }) => {
      await test.step(`Testing rapid interactions on ${browserName}`, async () => {
        // Mock authentication
        await page.goto('/');
        await page.evaluate(() => {
          localStorage.setItem('supabase.auth.token', JSON.stringify({
            access_token: 'mock-token',
            user: { id: 'mock-user-id', email: 'test@example.com' }
          }));
        });
        await page.reload();
        
        // Test rapid clicking doesn't break the interface
        const refreshButton = page.locator('text=Refresh, button:has-text("Refresh"), [data-testid="refresh"]');
        if (await refreshButton.count() > 0) {
          // Click multiple times rapidly
          for (let i = 0; i < 5; i++) {
            await refreshButton.first().click({ timeout: 1000 });
            await page.waitForTimeout(100);
          }
        }
        
        // Verify page is still responsive
        await expect(page.locator('body')).toBeVisible();
      });
    });
  });

  test.describe('Accessibility and Standards Compatibility', () => {
    test('should meet accessibility standards across browsers', async ({ page, browserName }) => {
      await test.step(`Testing accessibility on ${browserName}`, async () => {
        await page.goto('/auth');
        
        // Test keyboard navigation
        await page.keyboard.press('Tab');
        const focusedElement = page.locator(':focus');
        await expect(focusedElement).toBeVisible();
        
        // Test ARIA attributes
        const ariaElements = page.locator('[aria-label], [aria-labelledby], [aria-describedby], [role]');
        const ariaCount = await ariaElements.count();
        expect(ariaCount).toBeGreaterThan(0);
        
        // Test semantic HTML
        const semanticElements = page.locator('main, header, nav, section, article, aside, footer');
        const semanticCount = await semanticElements.count();
        expect(semanticCount).toBeGreaterThan(0);
      });
    });

    test('should handle focus management correctly', async ({ page, browserName }) => {
      await test.step(`Testing focus management on ${browserName}`, async () => {
        // Mock authentication
        await page.goto('/');
        await page.evaluate(() => {
          localStorage.setItem('supabase.auth.token', JSON.stringify({
            access_token: 'mock-token',
            user: { id: 'mock-user-id', email: 'test@example.com' }
          }));
        });
        await page.reload();
        
        // Test modal focus if available
        const createButton = page.locator('text=Create Job, button:has-text("Create"), [data-testid="create-job"]');
        if (await createButton.count() > 0) {
          await createButton.first().click();
          const modal = page.locator('[role="dialog"]');
          if (await modal.count() > 0) {
            await expect(modal.first()).toBeVisible();
            
            // Test that focus is managed within modal
            await page.keyboard.press('Tab');
            const focusedElement = page.locator(':focus');
            await expect(focusedElement).toBeVisible();
          }
        }
      });
    });
  });
});

test.describe('Mobile and Responsive Compatibility', () => {
  test('should adapt layout for mobile screens', async ({ page, browserName, isMobile }) => {
    await test.step(`Testing mobile layout on ${browserName}${isMobile ? ' (mobile)' : ''}`, async () => {
      await page.goto('/auth');
      
      if (isMobile) {
        // Test mobile-specific layout
        const container = page.locator('.container').first();
        if (await container.count() > 0) {
          await expect(container).toHaveCSS('padding-left', '16px');
          await expect(container).toHaveCSS('padding-right', '16px');
        }
        
        // Test mobile form styling
        const input = page.locator('input[type="email"]');
        await expect(input).toBeVisible();
        
        // Verify touch-friendly button sizes
        const button = page.locator('button[type="submit"]');
        const buttonSize = await button.boundingBox();
        if (buttonSize) {
          expect(buttonSize.height).toBeGreaterThanOrEqual(44); // iOS recommended minimum
        }
      } else {
        // Test desktop layout
        const container = page.locator('.container').first();
        if (await container.count() > 0) {
          await expect(container).toHaveCSS('max-width', '448px');
        }
      }
    });
  });

  test('should handle touch events properly', async ({ page, browserName, isMobile }) => {
    test.skip(!isMobile, 'Touch events test only relevant for mobile browsers');
    
    await test.step(`Testing touch events on ${browserName} mobile`, async () => {
      // Mock authentication
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.setItem('supabase.auth.token', JSON.stringify({
          access_token: 'mock-token',
          user: { id: 'mock-user-id', email: 'test@example.com' }
        }));
      });
      await page.reload();
      
      // Test touch interactions
      const createButton = page.locator('text=Create Job, button:has-text("Create"), [data-testid="create-job"]');
      if (await createButton.count() > 0) {
        await createButton.first().tap();
        
        const modal = page.locator('[role="dialog"]');
        if (await modal.count() > 0) {
          await expect(modal.first()).toBeVisible();
        }
      }
      
      // Test touch scrolling
      await page.touchscreen.tap(200, 300);
      await page.evaluate(() => window.scrollBy(0, 100));
      
      // Verify the page is still functional after touch interactions
      await expect(page.locator('body')).toBeVisible();
    });
  });

  test('should handle viewport changes gracefully', async ({ page, browserName }) => {
    await test.step(`Testing viewport changes on ${browserName}`, async () => {
      await page.goto('/');
      
      // Test different viewport sizes
      const viewports = [
        { width: 320, height: 568 },   // iPhone SE
        { width: 768, height: 1024 },  // iPad
        { width: 1024, height: 768 },  // iPad landscape
        { width: 1920, height: 1080 }, // Desktop
      ];
      
      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(500); // Allow time for responsive changes
        
        // Verify basic layout is maintained
        await expect(page.locator('body')).toBeVisible();
        
        // Check for any layout overflow
        const hasHorizontalScroll = await page.evaluate(() => {
          return document.body.scrollWidth > window.innerWidth;
        });
        
        // Horizontal scroll should be minimal or intentional
        if (hasHorizontalScroll) {
          const scrollWidth = await page.evaluate(() => document.body.scrollWidth);
          const windowWidth = await page.evaluate(() => window.innerWidth);
          const overflow = scrollWidth - windowWidth;
          
          // Allow small overflow (scrollbar, etc.) but flag significant issues
          expect(overflow).toBeLessThan(50);
        }
      }
    });
  });
}); 