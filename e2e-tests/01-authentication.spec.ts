import { test, expect } from '@playwright/test';
import { AuthHelper, NavigationHelper } from './helpers/test-helpers';
import { testUsers, selectors, timeouts } from './helpers/test-data';

test.describe('Authentication Workflow', () => {
  let authHelper: AuthHelper;
  let navHelper: NavigationHelper;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthHelper(page);
    navHelper = new NavigationHelper(page);
  });

  test('should redirect unauthenticated users to login page', async ({ page }) => {
    // Try to access dashboard without login
    await page.goto('/');
    
    // Should be redirected to auth page
    await page.waitForURL('/auth', { timeout: timeouts.pageLoad });
    
    // Login form should be visible
    await expect(page.locator(selectors.auth.loginForm)).toBeVisible();
  });

  test('should show login form on auth page', async ({ page }) => {
    await page.goto('/auth');
    
    // Verify all login form elements are present
    await expect(page.locator(selectors.auth.emailInput)).toBeVisible();
    await expect(page.locator(selectors.auth.passwordInput)).toBeVisible();
    await expect(page.locator(selectors.auth.loginButton)).toBeVisible();
    
    // Form should be properly labeled
    await expect(page.locator('label')).toContainText(['Email', 'Password']);
  });

  test('should handle invalid login credentials', async ({ page }) => {
    await page.goto('/auth');
    
    // Try invalid credentials
    await page.fill(selectors.auth.emailInput, 'invalid@example.com');
    await page.fill(selectors.auth.passwordInput, 'wrongpassword');
    await page.click(selectors.auth.loginButton);
    
    // Should show error message
    await expect(page.locator(selectors.ui.errorAlert)).toBeVisible({ timeout: timeouts.medium });
    
    // Should remain on auth page
    await expect(page).toHaveURL('/auth');
  });

  test('should handle empty login form submission', async ({ page }) => {
    await page.goto('/auth');
    
    // Try to submit empty form
    await page.click(selectors.auth.loginButton);
    
    // Should show validation errors or prevent submission
    const emailInput = page.locator(selectors.auth.emailInput);
    const passwordInput = page.locator(selectors.auth.passwordInput);
    
    // Check for HTML5 validation or custom error messages
    const emailIsInvalid = await emailInput.evaluate(el => !(el as HTMLInputElement).validity.valid);
    const passwordIsInvalid = await passwordInput.evaluate(el => !(el as HTMLInputElement).validity.valid);
    
    expect(emailIsInvalid || passwordIsInvalid).toBe(true);
  });

  test('should successfully login with valid credentials', async ({ page }) => {
    await authHelper.login(testUsers.admin);
    
    // Should be redirected to dashboard
    await expect(page).toHaveURL('/');
    
    // Should see authenticated UI elements
    await expect(page.locator(selectors.auth.logoutButton)).toBeVisible();
    
    // Should see dashboard content
    await expect(page.locator('h1, h2')).toContainText(['Dashboard', 'Jobs']);
  });

  test('should maintain session after page refresh', async ({ page }) => {
    await authHelper.login(testUsers.admin);
    
    // Refresh the page
    await page.reload();
    
    // Should still be logged in
    await expect(page.locator(selectors.auth.logoutButton)).toBeVisible();
    await expect(page).toHaveURL('/');
  });

  test('should successfully logout', async ({ page }) => {
    await authHelper.login(testUsers.admin);
    
    // Logout
    await authHelper.logout();
    
    // Should be redirected to auth page
    await expect(page).toHaveURL('/auth');
    
    // Should see login form
    await expect(page.locator(selectors.auth.loginForm)).toBeVisible();
    
    // Should not see authenticated elements
    await expect(page.locator(selectors.auth.logoutButton)).not.toBeVisible();
  });

  test('should handle session expiration', async ({ page }) => {
    await authHelper.login(testUsers.admin);
    
    // Simulate session expiration by clearing cookies/storage
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());
    await page.evaluate(() => sessionStorage.clear());
    
    // Try to access protected page
    await page.goto('/');
    
    // Should be redirected to login
    await page.waitForURL('/auth', { timeout: timeouts.pageLoad });
  });

  test('should handle multiple login attempts', async ({ page }) => {
    await page.goto('/auth');
    
    // First attempt with wrong password
    await page.fill(selectors.auth.emailInput, testUsers.admin.email);
    await page.fill(selectors.auth.passwordInput, 'wrongpassword');
    await page.click(selectors.auth.loginButton);
    
    // Wait for error
    await expect(page.locator(selectors.ui.errorAlert)).toBeVisible({ timeout: timeouts.medium });
    
    // Second attempt with correct credentials
    await page.fill(selectors.auth.passwordInput, testUsers.admin.password);
    await page.click(selectors.auth.loginButton);
    
    // Should succeed
    await page.waitForURL('/', { timeout: timeouts.pageLoad });
    await expect(page.locator(selectors.auth.logoutButton)).toBeVisible();
  });

  test('should login different user types', async ({ page }) => {
    // Test admin user
    await authHelper.login(testUsers.admin);
    await expect(page).toHaveURL('/');
    await authHelper.logout();
    
    // Test regular user
    await authHelper.login(testUsers.user);
    await expect(page).toHaveURL('/');
    await authHelper.logout();
  });

  test('should handle navigation between auth and protected pages', async ({ page }) => {
    // Start at auth page
    await page.goto('/auth');
    
    // Login
    await authHelper.login(testUsers.admin);
    
    // Navigate to different pages while authenticated
    await navHelper.goToJobCreation();
    await expect(page).toHaveURL('/schedule');
    
    await navHelper.goToDashboard();
    await expect(page).toHaveURL('/');
    
    // Logout should work from any page
    await authHelper.logout();
    await expect(page).toHaveURL('/auth');
  });

  test('should preserve intended destination after login', async ({ page }) => {
    // Try to access job creation page while logged out
    await page.goto('/schedule');
    
    // Should be redirected to auth
    await page.waitForURL('/auth', { timeout: timeouts.pageLoad });
    
    // Login
    await authHelper.login(testUsers.admin);
    
    // Should be able to access the intended destination
    await navHelper.goToJobCreation();
    await expect(page).toHaveURL('/schedule');
  });
}); 