---
name: Bug Report
about: Create a report to help us improve AI Agent Platform
title: '[BUG] '
labels: ['bug', 'needs-triage']
assignees: ''
---

## 🐛 Bug Description
A clear and concise description of what the bug is.

## 🔄 Steps to Reproduce
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## ✅ Expected Behavior
A clear and concise description of what you expected to happen.

## ❌ Actual Behavior
A clear and concise description of what actually happened.

## 📸 Screenshots
If applicable, add screenshots to help explain your problem.

## 🖥️ Environment Information
### Backend Environment
- **OS**: [e.g. Ubuntu 22.04, macOS Monterey, Windows 11]
- **Python Version**: [e.g. 3.8.10, 3.9.18, 3.11.5]
- **AI Agent Platform Version**: [e.g. v1.0.0, main branch commit hash]
- **Database**: [e.g. Supabase hosted, local PostgreSQL 14.9]

### Frontend Environment  
- **Browser**: [e.g. Chrome 120.0, Firefox 121.0, Safari 17.1]
- **Node.js Version**: [e.g. 18.18.0, 20.9.0]
- **Operating System**: [e.g. Windows 11, macOS Monterey, Ubuntu 22.04]

### Agent Configuration
- **AI Provider**: [e.g. Google AI (Gemini), OpenAI (GPT-4), Anthropic (Claude)]
- **Agent Type**: [e.g. Simple Prompt Agent, Web Scraping Agent, Custom Agent]
- **Authentication Method**: [e.g. API Key, OAuth, Service Account]

## 📋 Configuration Details
### Environment Variables (Remove sensitive values)
```bash
# Backend .env (replace sensitive values with "***")
SUPABASE_URL=***
AI_PROVIDER=google_ai
ENVIRONMENT=development

# Frontend .env.local (replace sensitive values with "***")  
NEXT_PUBLIC_SUPABASE_URL=***
NEXT_PUBLIC_ENVIRONMENT=development
```

### Relevant Configuration Files
If applicable, include relevant snippets from:
- `backend/config/settings.py` modifications
- Custom agent configurations
- Docker/deployment configurations

## 📝 Error Logs
### Backend Logs
```
Paste relevant backend error logs here
(Check backend/logs/ directory or console output)
```

### Frontend Console Errors
```
Paste browser console errors here
(Open Developer Tools → Console)
```

### Agent Execution Logs
```
Paste agent-specific error logs here
(Check job execution logs in the dashboard)
```

## 🔍 Additional Context
### Related Issues
- Link any related issues: #123, #456

### Attempted Solutions
Describe any solutions or workarounds you've already tried:
- [ ] Restarted services
- [ ] Cleared browser cache
- [ ] Checked environment variables
- [ ] Updated dependencies
- [ ] Other: ___________

### Impact Assessment
- **Severity**: [Low / Medium / High / Critical]
- **Frequency**: [Always / Often / Sometimes / Rarely]
- **User Impact**: [Single user / Multiple users / All users]
- **Workaround Available**: [Yes / No] - If yes, describe: ___________

## 🧪 Testing Information
### Test Cases
If you've written test cases to reproduce the bug:
```python
# Example test case
def test_bug_reproduction():
    # Your test code here
    pass
```

### Test Environment
- **Fresh Installation**: [Yes / No]
- **Development Mode**: [Yes / No]  
- **Production Environment**: [Yes / No]
- **Docker Deployment**: [Yes / No]

## 🏷️ Labels Checklist
Please help us categorize this issue by checking relevant labels:

### Component
- [ ] **Backend** - Python/FastAPI backend issues
- [ ] **Frontend** - React/TypeScript frontend issues  
- [ ] **Agent Framework** - Agent execution or framework issues
- [ ] **Database** - Supabase/PostgreSQL issues
- [ ] **Authentication** - Auth/security issues
- [ ] **API** - REST API endpoint issues
- [ ] **UI/UX** - User interface or experience issues
- [ ] **Documentation** - Documentation problems
- [ ] **Deployment** - Installation/deployment issues
- [ ] **Dependencies** - Third-party package issues

### Priority
- [ ] **Critical** - System down, data loss, security vulnerability
- [ ] **High** - Major feature broken, significant user impact
- [ ] **Medium** - Feature partially working, moderate user impact  
- [ ] **Low** - Minor issue, cosmetic problem, low user impact

### Type
- [ ] **Regression** - Something that used to work is now broken
- [ ] **New Bug** - Bug in existing functionality
- [ ] **Edge Case** - Unusual scenario or configuration
- [ ] **Performance** - Slow response times or resource usage
- [ ] **Memory Leak** - Memory usage grows over time
- [ ] **Race Condition** - Timing-dependent bug

---

**Note**: Please provide as much detail as possible. The more information you provide, the faster we can identify and fix the issue. Thank you for helping improve AI Agent Platform! 🛠️ 