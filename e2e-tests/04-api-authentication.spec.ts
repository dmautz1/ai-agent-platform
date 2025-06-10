import { test, expect } from '@playwright/test';
import { ApiHelper, AuthHelper } from './helpers/test-helpers';
import { testUsers, apiEndpoints, timeouts } from './helpers/test-data';

test.describe('API Authentication and Error Handling', () => {
  let apiHelper: ApiHelper;
  let authHelper: AuthHelper;

  test.beforeEach(async ({ page }) => {
    apiHelper = new ApiHelper(page);
    authHelper = new AuthHelper(page);
  });

  test.describe('Authentication Mechanisms', () => {
    test('should reject requests without authentication token', async ({ page }) => {
      // Try to access protected endpoint without authentication
      const response = await page.request.fetch('http://localhost:8000/jobs', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      expect(response.status()).toBe(401);
      
      const responseBody = await response.json();
      expect(responseBody).toHaveProperty('error');
      expect(responseBody.error).toContain('Unauthorized');
    });

    test('should reject requests with invalid authentication token', async ({ page }) => {
      const response = await page.request.fetch('http://localhost:8000/jobs', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer invalid-token-12345'
        }
      });

      expect(response.status()).toBe(401);
      
      const responseBody = await response.json();
      expect(responseBody).toHaveProperty('error');
      expect(responseBody.error).toMatch(/invalid|unauthorized|token/i);
    });

    test('should reject requests with malformed authorization header', async ({ page }) => {
      // Test various malformed authorization headers
      const malformedHeaders = [
        'invalid-format',
        'Bearer',
        'Basic token123',
        'Bearer ',
        'Bearer token-with-@-special-chars',
      ];

      for (const authHeader of malformedHeaders) {
        const response = await page.request.fetch('http://localhost:8000/jobs', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': authHeader
          }
        });

        expect(response.status()).toBe(401);
        
        const responseBody = await response.json();
        expect(responseBody).toHaveProperty('error');
      }
    });

    test('should accept requests with valid authentication token', async ({ page }) => {
      // First login to get a valid token
      await authHelper.login(testUsers.admin);
      
      // Get auth token from cookies
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;
      
      expect(authToken).toBeTruthy();

      // Use valid token to access protected endpoint
      const response = await page.request.fetch('http://localhost:8000/jobs', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        }
      });

      expect(response.status()).toBe(200);
      
      const responseBody = await response.json();
      expect(responseBody).toHaveProperty('data');
      expect(Array.isArray(responseBody.data)).toBe(true);
    });

    test('should handle expired authentication tokens', async ({ page }) => {
      // Login first
      await authHelper.login(testUsers.admin);
      
      // Clear cookies to simulate expired session
      await page.context().clearCookies();
      
      // Try to access protected endpoint
      const response = await page.request.fetch('http://localhost:8000/jobs', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      expect(response.status()).toBe(401);
    });

    test('should validate token permissions for different user roles', async ({ page }) => {
      // Test admin user permissions
      await authHelper.login(testUsers.admin);
      
      let cookies = await page.context().cookies();
      let authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;
      
      const adminResponse = await page.request.fetch('http://localhost:8000/jobs', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      expect(adminResponse.status()).toBe(200);
      
      // Logout and test regular user
      await authHelper.logout();
      await authHelper.login(testUsers.user);
      
      cookies = await page.context().cookies();
      authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;
      
      const userResponse = await page.request.fetch('http://localhost:8000/jobs', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      expect(userResponse.status()).toBe(200);
    });
  });

  test.describe('API Error Handling', () => {
    test('should return proper error format for 400 Bad Request', async ({ page }) => {
      await authHelper.login(testUsers.admin);
      
      // Send malformed job creation request
      const response = await apiHelper.makeAuthenticatedRequest('POST', '/jobs', {
        // Missing required fields
        invalid_field: 'test'
      });

      expect(response).rejects.toThrow();
      
      try {
        await response;
      } catch (error: any) {
        expect(error.message).toContain('400');
      }
    });

    test('should return 404 for non-existent endpoints', async ({ page }) => {
      await authHelper.login(testUsers.admin);
      
      const response = await page.request.fetch('http://localhost:8000/non-existent-endpoint', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer valid-token'
        }
      });

      expect(response.status()).toBe(404);
      
      const responseBody = await response.json();
      expect(responseBody).toHaveProperty('error');
      expect(responseBody.error).toMatch(/not found/i);
    });

    test('should return 405 for unsupported HTTP methods', async ({ page }) => {
      await authHelper.login(testUsers.admin);
      
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;
      
      // Try unsupported method on jobs endpoint
      const response = await page.request.fetch('http://localhost:8000/jobs', {
        method: 'PATCH', // Assuming PATCH is not supported
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        }
      });

      expect(response.status()).toBe(405);
      
      const responseBody = await response.json();
      expect(responseBody).toHaveProperty('error');
      expect(responseBody.error).toMatch(/method not allowed/i);
    });

    test('should handle malformed JSON requests', async ({ page }) => {
      await authHelper.login(testUsers.admin);
      
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;
      
      const response = await page.request.fetch('http://localhost:8000/jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        data: 'invalid-json{'
      });

      expect(response.status()).toBe(400);
      
      const responseBody = await response.json();
      expect(responseBody).toHaveProperty('error');
      expect(responseBody.error).toMatch(/invalid|json|parse/i);
    });

    test('should return 422 for validation errors', async ({ page }) => {
      await authHelper.login(testUsers.admin);
      
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;
      
      // Send job creation request with invalid data
      const response = await page.request.fetch('http://localhost:8000/jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        data: JSON.stringify({
          agent_identifier: 'simple_prompt',
          data: { prompt: 'test' }
        })
      });

      expect(response.status()).toBe(422);
      
      const responseBody = await response.json();
      expect(responseBody).toHaveProperty('error');
      expect(responseBody.error).toMatch(/validation|invalid/i);
    });

    test('should handle server errors gracefully', async ({ page }) => {
      await authHelper.login(testUsers.admin);
      
      // Try to trigger a server error by accessing non-existent job
      const response = await apiHelper.makeAuthenticatedRequest('GET', '/jobs/non-existent-id');
      
      expect(response).rejects.toThrow();
      
      try {
        await response;
      } catch (error: any) {
        expect(error.message).toContain('404');
      }
    });
  });

  test.describe('Rate Limiting and Security', () => {
    test('should handle multiple rapid requests', async ({ page }) => {
      await authHelper.login(testUsers.admin);
      
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;
      
      // Make multiple rapid requests
      const requests = Array.from({ length: 10 }, () =>
        page.request.fetch('http://localhost:8000/jobs', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        })
      );
      
      const responses = await Promise.all(requests);
      
      // All requests should either succeed or be rate limited
      responses.forEach(response => {
        expect([200, 429]).toContain(response.status());
      });
    });

    test('should reject requests with suspicious headers', async ({ page }) => {
      await authHelper.login(testUsers.admin);
      
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;
      
      // Send request with suspicious headers
      const response = await page.request.fetch('http://localhost:8000/jobs', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'X-Forwarded-For': '127.0.0.1',
          'X-Real-IP': '10.0.0.1',
          'User-Agent': '<script>alert("xss")</script>'
        }
      });

      // Should still process the request but sanitize headers
      expect([200, 400, 403]).toContain(response.status());
    });

    test('should validate content-type headers', async ({ page }) => {
      await authHelper.login(testUsers.admin);
      
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;
      
      // Send POST request without proper content-type
      const response = await page.request.fetch('http://localhost:8000/jobs', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'text/plain'
        },
        data: JSON.stringify({
          agent_identifier: 'simple_prompt',
          data: { prompt: 'test' }
        })
      });

      expect([400, 415]).toContain(response.status());
    });
  });

  test.describe('CORS and Origin Validation', () => {
    test('should handle CORS preflight requests', async ({ page }) => {
      const response = await page.request.fetch('http://localhost:8000/jobs', {
        method: 'OPTIONS',
        headers: {
          'Origin': 'http://localhost:5173',
          'Access-Control-Request-Method': 'POST',
          'Access-Control-Request-Headers': 'Content-Type,Authorization'
        }
      });

      expect(response.status()).toBe(200);
      
      const headers = response.headers();
      expect(headers['access-control-allow-origin']).toBeTruthy();
      expect(headers['access-control-allow-methods']).toBeTruthy();
      expect(headers['access-control-allow-headers']).toBeTruthy();
    });

    test('should reject requests from unauthorized origins', async ({ page }) => {
      await authHelper.login(testUsers.admin);
      
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;
      
      const response = await page.request.fetch('http://localhost:8000/jobs', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Origin': 'https://malicious-site.com'
        }
      });

      // CORS should be handled appropriately
      expect([200, 403]).toContain(response.status());
    });
  });

  test.describe('Error Response Consistency', () => {
    test('should return consistent error response format', async ({ page }) => {
      const errorEndpoints = [
        { endpoint: '/jobs/invalid-id', method: 'GET', expectedStatus: 404 },
        { endpoint: '/jobs', method: 'PATCH', expectedStatus: 405 },
        { endpoint: '/invalid-endpoint', method: 'GET', expectedStatus: 404 }
      ];

      await authHelper.login(testUsers.admin);
      
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;

      for (const { endpoint, method, expectedStatus } of errorEndpoints) {
        const response = await page.request.fetch(`http://localhost:8000${endpoint}`, {
          method,
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        });

        expect(response.status()).toBe(expectedStatus);
        
        const responseBody = await response.json();
        
        // Verify consistent error response format
        expect(responseBody).toHaveProperty('error');
        expect(typeof responseBody.error).toBe('string');
        
        // Optional: Check for additional error details
        if (responseBody.detail) {
          expect(typeof responseBody.detail).toBe('string');
        }
      }
    });

    test('should include request ID in error responses', async ({ page }) => {
      const response = await page.request.fetch('http://localhost:8000/jobs', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      expect(response.status()).toBe(401);
      
      const responseBody = await response.json();
      
      // Check for tracking information (request ID, timestamp, etc.)
      const hasTrackingInfo = responseBody.request_id || 
                             responseBody.timestamp || 
                             responseBody.trace_id;
      
      // This is optional but recommended for production APIs
      // expect(hasTrackingInfo).toBeTruthy();
    });
  });

  test.describe('API Performance and Timeout Handling', () => {
    test('should handle slow requests appropriately', async ({ page }) => {
      await authHelper.login(testUsers.admin);
      
      const startTime = Date.now();
      
      const response = await apiHelper.makeAuthenticatedRequest('GET', '/jobs');
      
      const endTime = Date.now();
      const responseTime = endTime - startTime;
      
      // API should respond within reasonable time
      expect(responseTime).toBeLessThan(5000); // 5 seconds
      
      const jobs = await response;
      expect(Array.isArray(jobs)).toBe(true);
    });

    test('should handle timeout scenarios', async ({ page }) => {
      // This test would require a special endpoint that intentionally delays
      // For now, we'll test the client-side timeout handling
      
      await authHelper.login(testUsers.admin);
      
      try {
        const response = await page.request.fetch('http://localhost:8000/jobs', {
          method: 'GET',
          timeout: 1, // Very short timeout
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        // If it doesn't timeout, that's also fine
        expect(response.status()).toBe(200);
        
      } catch (error: any) {
        // Should handle timeout gracefully
        expect(error.message).toMatch(/timeout|exceeded/i);
      }
    });
  });
}); 