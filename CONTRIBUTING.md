# Contributing to AI Agent Platform

Thank you for your interest in contributing to AI Agent Platform! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/ai-agent-platform.git
   cd ai-agent-platform
   ```
3. **Set up the development environment** following the [README.md](README.md)
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
5. **Make your changes** and test them
6. **Submit a pull request**

## 🎯 Ways to Contribute

### 🐛 Bug Reports
- Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md)
- Include steps to reproduce, expected behavior, and actual behavior
- Provide system information (OS, Node.js/Python versions, etc.)

### ✨ Feature Requests
- Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md)
- Describe the use case and proposed solution
- Consider starting a discussion before implementing large features

### 🤖 Agent Development
- Create custom agents in the `backend/agents/` directory
- Follow the self-contained agent framework patterns
- Include proper documentation and examples

### 📚 Documentation
- Improve existing documentation
- Add examples and tutorials
- Fix typos and unclear instructions

### 🧪 Testing
- Add test coverage for new features
- Fix failing tests
- Improve test infrastructure

## 🛠️ Development Setup

### Prerequisites
- **Node.js 18+**
- **Python 3.8+**
- **Git**

### Environment Setup
1. **Install dependencies**:
   ```bash
   # Root dependencies
   npm install
   
   # Frontend dependencies
   cd frontend && npm install && cd ..
   
   # Backend dependencies
   cd backend && python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt && cd ..
   ```

2. **Configure environment variables**:
   ```bash
   cp backend/env.example backend/.env
   cp frontend/env.local.example frontend/.env.local
   # Edit files with your credentials
   ```

3. **Set up database** (follow [Environment Setup Guide](docs/getting-started/environment-setup.md))

4. **Start development servers**:
   ```bash
   # Terminal 1: Backend
   cd backend && source venv/bin/activate && python main.py
   
   # Terminal 2: Frontend  
   cd frontend && npm run dev
   ```

## 🧪 Testing

### Running Tests
```bash
# All tests
npm test

# Backend tests only
npm run test:backend

# Frontend tests only
npm run test:frontend

# E2E tests
npm run test:e2e
```

### Test Standards
- **Backend**: Maintain >95% test coverage
- **Frontend**: Maintain >90% test coverage
- **Integration**: Test critical user workflows
- **New features**: Include comprehensive tests

### Test Structure
```
backend/tests/
├── unit/          # Unit tests for individual modules
├── integration/   # Integration tests for API endpoints
└── agents/        # Tests for custom agents

frontend/src/test/
├── components/    # Component tests
├── hooks/         # Custom hook tests
└── utils/         # Utility function tests
```

## 📋 Coding Standards

### Backend (Python)
- **Style**: Follow PEP 8
- **Type hints**: Use type annotations
- **Docstrings**: Use Google-style docstrings
- **Testing**: Use pytest with async support
- **Linting**: Code must pass flake8 and black formatting

```python
async def example_function(param: str) -> Dict[str, Any]:
    """
    Example function demonstrating proper style.
    
    Args:
        param: Description of parameter
        
    Returns:
        Dictionary with result data
    """
    return {"result": param}
```

### Frontend (TypeScript/React)
- **Style**: Follow project ESLint configuration
- **Components**: Use functional components with hooks
- **Props**: Define proper TypeScript interfaces
- **Testing**: Use React Testing Library patterns
- **Accessibility**: Include ARIA attributes where needed

```typescript
interface ExampleProps {
  title: string;
  onAction: (data: string) => void;
}

export const ExampleComponent: React.FC<ExampleProps> = ({ title, onAction }) => {
  return (
    <div>
      <h1>{title}</h1>
      <button onClick={() => onAction('example')}>
        Action
      </button>
    </div>
  );
};
```

### Agent Development
- **Framework**: Use SelfContainedAgent base class
- **Models**: Define Pydantic models for job data
- **Endpoints**: Use framework decorators
- **Error handling**: Include proper exception handling
- **Documentation**: Document agent capabilities and usage

```python
from agent_framework import SelfContainedAgent, endpoint, job_model
from pydantic import BaseModel, Field

@job_model
class MyJobData(BaseModel):
    text: str = Field(..., description="Text to process")

class MyAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(
            description="My custom agent",
            **kwargs
        )
    
    @endpoint("/my-agent/process", methods=["POST"], auth_required=True)
    async def process(self, request_data: dict, user: dict):
        # Implementation here
        pass
```

## 🔄 Pull Request Process

### Before Submitting
1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Run the full test suite** and ensure it passes
4. **Update CHANGELOG.md** if applicable
5. **Rebase** your branch on the latest main

### PR Guidelines
- **Title**: Use clear, descriptive titles
- **Description**: Explain what, why, and how
- **Scope**: Keep PRs focused and reasonably sized
- **Testing**: Include test results and coverage information
- **Breaking changes**: Clearly document any breaking changes

### PR Template
```markdown
## What
Brief description of changes

## Why
Explanation of the problem being solved

## How
Technical approach and implementation details

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Documentation updated
- [ ] Tests added for new functionality
- [ ] No breaking changes (or clearly documented)
- [ ] Code follows project standards
```

## 🎨 Code Review Process

### For Contributors
- **Be responsive** to feedback
- **Ask questions** if feedback is unclear
- **Make requested changes** promptly
- **Test thoroughly** after making changes

### For Reviewers
- **Be constructive** and specific in feedback
- **Focus on** code quality, design, and maintainability
- **Consider** performance and security implications
- **Approve** when code meets project standards

## 📊 Performance Guidelines

### Backend Performance
- **API response times**: Target <200ms for most endpoints
- **Memory usage**: Monitor and optimize memory consumption
- **Database queries**: Use efficient queries and indexing
- **Caching**: Implement appropriate caching strategies

### Frontend Performance
- **Bundle size**: Keep main bundle <500KB gzipped
- **Load times**: Target <3s initial load
- **Rendering**: Optimize re-renders and component updates
- **Accessibility**: Maintain >90% Lighthouse accessibility score

## 🔒 Security Guidelines

### General Security
- **Never commit** sensitive data (API keys, passwords, etc.)
- **Validate** all user inputs
- **Sanitize** outputs to prevent XSS
- **Use HTTPS** in production environments

### Backend Security
- **Authentication**: Implement proper JWT validation
- **Authorization**: Check permissions for all protected endpoints
- **Rate limiting**: Implement appropriate rate limits
- **SQL injection**: Use parameterized queries

### Frontend Security
- **XSS prevention**: Sanitize user inputs and outputs
- **CSRF protection**: Use appropriate tokens and headers
- **Content Security Policy**: Follow CSP guidelines
- **Dependency security**: Regularly update dependencies

## 📝 Documentation Standards

### Code Documentation
- **Functions**: Document purpose, parameters, and return values
- **Classes**: Explain responsibilities and usage patterns
- **Modules**: Provide overview and key concepts
- **APIs**: Use OpenAPI/Swagger documentation

### User Documentation
- **Clear instructions**: Step-by-step guides
- **Examples**: Include working code examples
- **Troubleshooting**: Address common issues
- **Screenshots**: Use visuals where helpful

## 🌟 Recognition

Contributors who make significant improvements will be:
- **Listed** in CONTRIBUTORS.md
- **Mentioned** in release notes
- **Credited** in documentation
- **Invited** to join the maintainer team (for regular contributors)

## ❓ Getting Help

### Communication Channels
- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check existing docs first

### Contact
- **Maintainers**: See MAINTAINERS.md
- **Security issues**: See SECURITY.md
- **General questions**: Open a GitHub discussion

## 📜 Code of Conduct

This project follows our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code. Please report unacceptable behavior to the project maintainers.

---

Thank you for contributing to AI Agent Platform! 🎉 