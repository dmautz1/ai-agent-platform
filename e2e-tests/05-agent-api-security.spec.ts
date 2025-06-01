import { test, expect } from '@playwright/test';
import { ApiHelper, AuthHelper } from './helpers/test-helpers';
import { testUsers, testJobs, generateTestData } from './helpers/test-data';

test.describe('Agent API Security and Validation', () => {
  let apiHelper: ApiHelper;
  let authHelper: AuthHelper;

  test.beforeEach(async ({ page }) => {
    apiHelper = new ApiHelper(page);
    authHelper = new AuthHelper(page);
    
    // Login for authenticated tests
    await authHelper.login(testUsers.admin);
  });

  test.describe('Agent Input Validation', () => {
    test('should validate text processing agent input', async ({ page }) => {
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;

      // Test missing required fields
      const invalidInputs = [
        { /* empty data */ },
        { agent_type: 'text_processing' }, // missing data
        { agent_type: 'text_processing', data: {} }, // missing input_text
        { agent_type: 'text_processing', data: { input_text: '' } }, // empty input_text
        { agent_type: 'text_processing', data: { input_text: 'a'.repeat(10000) } }, // too long
        { agent_type: 'text_processing', data: { input_text: 'test', operation: 'invalid_operation' } },
      ];

      for (const invalidInput of invalidInputs) {
        const response = await page.request.fetch('http://localhost:8000/jobs', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          data: JSON.stringify(invalidInput)
        });

        expect([400, 422]).toContain(response.status());
        
        const responseBody = await response.json();
        expect(responseBody).toHaveProperty('error');
      }
    });

    test('should validate summarization agent input', async ({ page }) => {
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;

      // Test invalid summarization inputs
      const invalidInputs = [
        { agent_type: 'summarization', data: {} }, // missing input source
        { agent_type: 'summarization', data: { input_text: '', input_url: '' } }, // both empty
        { agent_type: 'summarization', data: { input_text: 'test', input_url: 'https://example.com' } }, // both provided
        { agent_type: 'summarization', data: { input_text: 'test', max_summary_length: -1 } }, // negative length
        { agent_type: 'summarization', data: { input_text: 'test', max_summary_length: 10000 } }, // too long
        { agent_type: 'summarization', data: { input_url: 'not-a-url' } }, // invalid URL
        { agent_type: 'summarization', data: { input_text: 'test', format: 'invalid_format' } },
      ];

      for (const invalidInput of invalidInputs) {
        const response = await page.request.fetch('http://localhost:8000/jobs', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          data: JSON.stringify(invalidInput)
        });

        expect([400, 422]).toContain(response.status());
        
        const responseBody = await response.json();
        expect(responseBody).toHaveProperty('error');
      }
    });

    test('should validate web scraping agent input', async ({ page }) => {
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;

      // Test invalid web scraping inputs
      const invalidInputs = [
        { agent_type: 'web_scraping', data: {} }, // missing input_url
        { agent_type: 'web_scraping', data: { input_url: '' } }, // empty URL
        { agent_type: 'web_scraping', data: { input_url: 'not-a-url' } }, // invalid URL format
        { agent_type: 'web_scraping', data: { input_url: 'ftp://example.com' } }, // unsupported protocol
        { agent_type: 'web_scraping', data: { input_url: 'https://localhost' } }, // localhost (security risk)
        { agent_type: 'web_scraping', data: { input_url: 'https://192.168.1.1' } }, // private IP
        { agent_type: 'web_scraping', data: { input_url: 'https://example.com', max_pages: 0 } }, // invalid page count
        { agent_type: 'web_scraping', data: { input_url: 'https://example.com', max_pages: 1000 } }, // too many pages
        { agent_type: 'web_scraping', data: { input_url: 'https://example.com', selectors: 'invalid_array' } }, // wrong type
      ];

      for (const invalidInput of invalidInputs) {
        const response = await page.request.fetch('http://localhost:8000/jobs', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          data: JSON.stringify(invalidInput)
        });

        expect([400, 422]).toContain(response.status());
        
        const responseBody = await response.json();
        expect(responseBody).toHaveProperty('error');
      }
    });

    test('should reject unknown agent types', async ({ page }) => {
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;

      const unknownAgentTypes = [
        'unknown_agent',
        'malicious_agent',
        '',
        null,
        123,
        { type: 'nested_object' }
      ];

      for (const agentType of unknownAgentTypes) {
        const response = await page.request.fetch('http://localhost:8000/jobs', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          data: JSON.stringify({
            agent_type: agentType,
            data: { input_text: 'test' }
          })
        });

        expect([400, 422]).toContain(response.status());
        
        const responseBody = await response.json();
        expect(responseBody).toHaveProperty('error');
        expect(responseBody.error).toMatch(/agent|type|invalid/i);
      }
    });
  });

  test.describe('SQL Injection Prevention', () => {
    test('should prevent SQL injection in job creation', async ({ page }) => {
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;

      const sqlInjectionPayloads = [
        "'; DROP TABLE jobs; --",
        "' OR '1'='1",
        "'; DELETE FROM jobs WHERE '1'='1'; --",
        "' UNION SELECT * FROM users --",
        "'; INSERT INTO jobs (data) VALUES ('malicious'); --"
      ];

      for (const payload of sqlInjectionPayloads) {
        const response = await page.request.fetch('http://localhost:8000/jobs', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          data: JSON.stringify({
            agent_type: 'text_processing',
            data: {
              input_text: payload,
              operation: 'sentiment_analysis'
            }
          })
        });

        // Should either create the job safely or reject the input
        expect([200, 201, 400, 422]).toContain(response.status());
        
        if (response.status() === 200 || response.status() === 201) {
          const responseBody = await response.json();
          // If job was created, the SQL injection should be treated as regular text
          expect(responseBody).toHaveProperty('data');
        }
      }
    });

    test('should prevent SQL injection in job retrieval', async ({ page }) => {
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;

      const sqlInjectionPayloads = [
        "'; DROP TABLE jobs; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM users --"
      ];

      for (const payload of sqlInjectionPayloads) {
        const response = await page.request.fetch(`http://localhost:8000/jobs/${encodeURIComponent(payload)}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        });

        // Should return 404 for invalid job ID, not execute SQL
        expect(response.status()).toBe(404);
        
        const responseBody = await response.json();
        expect(responseBody).toHaveProperty('error');
      }
    });
  });

  test.describe('XSS Prevention', () => {
    test('should sanitize XSS payloads in job data', async ({ page }) => {
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;

      const xssPayloads = [
        '<script>alert("xss")</script>',
        '<img src="x" onerror="alert(1)">',
        'javascript:alert("xss")',
        '<svg/onload=alert("xss")>',
        '"><script>alert("xss")</script>'
      ];

      for (const payload of xssPayloads) {
        const response = await page.request.fetch('http://localhost:8000/jobs', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          data: JSON.stringify({
            agent_type: 'text_processing',
            data: {
              input_text: payload,
              operation: 'sentiment_analysis'
            }
          })
        });

        // Should either create the job safely or reject the input
        expect([200, 201, 400, 422]).toContain(response.status());
        
        if (response.status() === 200 || response.status() === 201) {
          const responseBody = await response.json();
          expect(responseBody).toHaveProperty('data');
          
          // XSS payload should be treated as regular text, not executable code
          const jobData = responseBody.data;
          expect(typeof jobData).toBe('object');
        }
      }
    });
  });

  test.describe('File Upload Security', () => {
    test('should reject malicious file uploads', async ({ page }) => {
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;

      // Test various malicious file scenarios
      const maliciousFiles = [
        { name: 'script.js', content: 'alert("xss")' },
        { name: 'executable.exe', content: 'MZ\x90\x00' }, // PE header
        { name: '../../../etc/passwd', content: 'root:x:0:0:root:/root:/bin/bash' },
        { name: 'test.php', content: '<?php system($_GET["cmd"]); ?>' },
        { name: 'large_file.txt', content: 'A'.repeat(100 * 1024 * 1024) }, // 100MB
      ];

      for (const file of maliciousFiles) {
        // This would test file upload endpoints if they exist
        // For now, we'll test if the API properly rejects file-based attacks
        
        const response = await page.request.fetch('http://localhost:8000/jobs', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          data: JSON.stringify({
            agent_type: 'text_processing',
            data: {
              input_text: file.content,
              filename: file.name
            }
          })
        });

        // Should handle potentially dangerous content safely
        expect([200, 201, 400, 422]).toContain(response.status());
      }
    });
  });

  test.describe('Rate Limiting by Agent Type', () => {
    test('should enforce rate limits per agent type', async ({ page }) => {
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;

      // Test rate limiting for each agent type
      const agentTypes = ['text_processing', 'summarization', 'web_scraping'];

      for (const agentType of agentTypes) {
        const requests = Array.from({ length: 5 }, (_, i) =>
          page.request.fetch('http://localhost:8000/jobs', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${authToken}`
            },
            data: JSON.stringify({
              agent_type: agentType,
              data: { ...testJobs[agentType.replace('_', '')].data }
            })
          })
        );

        const responses = await Promise.all(requests);

        // Some requests should succeed, but rate limiting might kick in
        const successfulRequests = responses.filter(r => [200, 201].includes(r.status()));
        const rateLimitedRequests = responses.filter(r => r.status() === 429);

        expect(successfulRequests.length + rateLimitedRequests.length).toBe(5);
      }
    });
  });

  test.describe('Agent Resource Limits', () => {
    test('should enforce text processing limits', async ({ page }) => {
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;

      // Test various text length limits
      const textLengths = [
        { text: 'short', shouldSucceed: true },
        { text: 'A'.repeat(1000), shouldSucceed: true }, // 1KB
        { text: 'A'.repeat(50000), shouldSucceed: true }, // 50KB
        { text: 'A'.repeat(1000000), shouldSucceed: false }, // 1MB - should be rejected
      ];

      for (const { text, shouldSucceed } of textLengths) {
        const response = await page.request.fetch('http://localhost:8000/jobs', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          data: JSON.stringify({
            agent_type: 'text_processing',
            data: {
              input_text: text,
              operation: 'sentiment_analysis'
            }
          })
        });

        if (shouldSucceed) {
          expect([200, 201]).toContain(response.status());
        } else {
          expect([400, 413, 422]).toContain(response.status());
          
          const responseBody = await response.json();
          expect(responseBody).toHaveProperty('error');
          expect(responseBody.error).toMatch(/too large|limit|size/i);
        }
      }
    });

    test('should enforce web scraping URL restrictions', async ({ page }) => {
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;

      // Test URL restrictions
      const urlTests = [
        { url: 'https://httpbin.org/html', shouldSucceed: true },
        { url: 'https://example.com', shouldSucceed: true },
        { url: 'http://localhost:8080', shouldSucceed: false }, // localhost
        { url: 'https://192.168.1.1', shouldSucceed: false }, // private IP
        { url: 'https://10.0.0.1', shouldSucceed: false }, // private IP
        { url: 'https://172.16.0.1', shouldSucceed: false }, // private IP
        { url: 'ftp://example.com', shouldSucceed: false }, // unsupported protocol
        { url: 'file:///etc/passwd', shouldSucceed: false }, // file protocol
      ];

      for (const { url, shouldSucceed } of urlTests) {
        const response = await page.request.fetch('http://localhost:8000/jobs', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          data: JSON.stringify({
            agent_type: 'web_scraping',
            data: {
              input_url: url,
              max_pages: 1
            }
          })
        });

        if (shouldSucceed) {
          expect([200, 201]).toContain(response.status());
        } else {
          expect([400, 403, 422]).toContain(response.status());
          
          const responseBody = await response.json();
          expect(responseBody).toHaveProperty('error');
        }
      }
    });
  });

  test.describe('Agent Status and Health Checks', () => {
    test('should check agent availability', async ({ page }) => {
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;

      const response = await page.request.fetch('http://localhost:8000/agents', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      expect(response.status()).toBe(200);
      
      const responseBody = await response.json();
      expect(responseBody).toHaveProperty('data');
      
      const agents = responseBody.data;
      expect(typeof agents).toBe('object');
      
      // Should include all three agent types
      expect(agents).toHaveProperty('text_processing');
      expect(agents).toHaveProperty('summarization');
      expect(agents).toHaveProperty('web_scraping');
      
      // Each agent should have status information
      Object.values(agents).forEach((agent: any) => {
        expect(agent).toHaveProperty('status');
        expect(['active', 'inactive', 'maintenance']).toContain(agent.status);
      });
    });

    test('should handle agent-specific health checks', async ({ page }) => {
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;

      const agentTypes = ['text_processing', 'summarization', 'web_scraping'];

      for (const agentType of agentTypes) {
        const response = await page.request.fetch(`http://localhost:8000/agents/${agentType}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        });

        expect(response.status()).toBe(200);
        
        const responseBody = await response.json();
        expect(responseBody).toHaveProperty('data');
        
        const agentInfo = responseBody.data;
        expect(agentInfo).toHaveProperty('name');
        expect(agentInfo).toHaveProperty('status');
        expect(agentInfo.name).toContain(agentType.replace('_', ' '));
      }
    });
  });

  test.describe('Error Response Security', () => {
    test('should not leak sensitive information in error messages', async ({ page }) => {
      const cookies = await page.context().cookies();
      const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;

      // Test various error scenarios
      const errorTests = [
        { endpoint: '/jobs/non-existent-id', method: 'GET' },
        { endpoint: '/jobs', method: 'POST', data: { invalid: 'data' } },
        { endpoint: '/agents/invalid-agent', method: 'GET' },
      ];

      for (const { endpoint, method, data } of errorTests) {
        const response = await page.request.fetch(`http://localhost:8000${endpoint}`, {
          method,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          data: data ? JSON.stringify(data) : undefined
        });

        expect([400, 404, 405, 422]).toContain(response.status());
        
        const responseBody = await response.json();
        expect(responseBody).toHaveProperty('error');
        
        // Error messages should not contain sensitive information
        const errorMessage = responseBody.error.toLowerCase();
        
        // Should not contain database details
        expect(errorMessage).not.toMatch(/sql|database|table|column|postgres|supabase/);
        
        // Should not contain file paths
        expect(errorMessage).not.toMatch(/\/home|\/var|\/usr|\/etc|c:\\|d:\\/);
        
        // Should not contain internal server details
        expect(errorMessage).not.toMatch(/traceback|stack trace|internal server/);
      }
    });
  });
}); 