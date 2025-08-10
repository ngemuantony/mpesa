# Contributing to M-Pesa STK Push Integration

Thank you for your interest in contributing to this project! We welcome contributions from the community and are grateful for your help in making this M-Pesa integration better.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Security Guidelines](#security-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Community](#community)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code:

- **Be respectful**: Treat everyone with respect and kindness
- **Be inclusive**: Welcome newcomers and help them feel included
- **Be constructive**: Focus on what is best for the community
- **Be patient**: Understand that everyone has different skill levels
- **Be collaborative**: Work together towards common goals

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.8 or higher
- Git version control
- Django knowledge (basic to intermediate)
- Understanding of M-Pesa API concepts
- Experience with REST APIs

### Setup Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/mpesa.git
   cd mpesa
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your test credentials
   ```

5. **Run initial setup**
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   python manage.py test
   ```

## Development Process

### Branching Strategy

We use a simplified Git Flow:

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Feature development branches
- `hotfix/*`: Critical bug fixes
- `release/*`: Release preparation branches

### Feature Development Workflow

1. **Create feature branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Develop your feature**
   - Write code following our standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   python manage.py test
   python test_security.py
   python test_integration.py
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Coding Standards

### Python Code Style

We follow PEP 8 with some project-specific additions:

```python
# Good: Clear, descriptive names
def validate_mpesa_callback(request_data):
    """Validate M-Pesa callback request data."""
    pass

# Bad: Unclear abbreviations
def val_cb(data):
    pass
```

### Django Conventions

- Use Django's built-in features when possible
- Follow Django's model, view, template patterns
- Use Django forms for validation
- Implement proper error handling

### Documentation Standards

- All functions must have docstrings
- Use Google-style docstrings
- Update README.md for new features
- Add inline comments for complex logic

```python
def process_payment(phone_number, amount, reference):
    """Process M-Pesa STK Push payment.
    
    Args:
        phone_number (str): Customer phone number in format 254XXXXXXXXX
        amount (int): Payment amount in KES
        reference (str): Unique payment reference
        
    Returns:
        dict: Payment response with status and transaction details
        
    Raises:
        ValidationError: If input parameters are invalid
        PaymentError: If payment processing fails
    """
    pass
```

### Security Standards

- Never log sensitive data (passwords, tokens, PINs)
- Sanitize all user inputs
- Use parameterized queries
- Validate all callback requests
- Implement proper error handling without information disclosure

## Testing Guidelines

### Test Coverage Requirements

- Minimum 80% code coverage
- All new features must include tests
- Critical security functions require comprehensive tests

### Test Types

1. **Unit Tests**: Test individual functions and methods
   ```python
   class TestPhoneValidation(TestCase):
       def test_valid_phone_formats(self):
           self.assertEqual(validate_phone("0712345678"), "254712345678")
   ```

2. **Integration Tests**: Test API endpoints
   ```python
   class TestPaymentAPI(APITestCase):
       def test_stk_push_success(self):
           response = self.client.post('/payments/checkout/', data)
           self.assertEqual(response.status_code, 200)
   ```

3. **Security Tests**: Test security features
   ```python
   class TestCallbackSecurity(TestCase):
       def test_invalid_ip_rejected(self):
           # Test IP whitelisting
           pass
   ```

### Running Tests

```bash
# All tests
python manage.py test

# Specific test file
python manage.py test mpesa.tests.test_payments

# With coverage
coverage run --source='.' manage.py test
coverage report -m
```

## Security Guidelines

### Secure Development Practices

1. **Input Validation**
   - Validate all user inputs
   - Sanitize data before database storage
   - Use Django forms for validation

2. **Authentication & Authorization**
   - Implement proper access controls
   - Use Django's authentication framework
   - Validate all API requests

3. **Data Protection**
   - Hash sensitive data
   - Use HTTPS in production
   - Implement proper logging without exposing secrets

4. **Error Handling**
   - Don't expose internal errors to users
   - Log errors securely
   - Provide helpful but safe error messages

### Security Testing

```bash
# Run security tests
python test_security.py

# Check for common vulnerabilities
bandit -r .

# Dependency security scan
safety check
```

## Pull Request Process

### Before Submitting

1. **Self-review checklist**
   - [ ] Code follows project style guidelines
   - [ ] Tests are added for new functionality
   - [ ] All tests pass locally
   - [ ] Documentation is updated
   - [ ] No sensitive information is committed
   - [ ] Commit messages follow conventions

2. **Pre-commit hooks**
   ```bash
   # Install pre-commit hooks
   pre-commit install
   
   # Run hooks manually
   pre-commit run --all-files
   ```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Security Considerations
- [ ] No sensitive data exposed
- [ ] Input validation implemented
- [ ] Security tests updated

## Documentation
- [ ] README updated
- [ ] Code comments added
- [ ] API documentation updated
```

### Review Process

1. **Automated Checks**
   - Code style validation
   - Test execution
   - Security scans
   - Coverage reports

2. **Manual Review**
   - Code quality assessment
   - Security review
   - Documentation review
   - Functionality testing

3. **Approval Process**
   - At least one maintainer approval required
   - All automated checks must pass
   - Security review for sensitive changes

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Bug Description**
Clear description of the issue

**Steps to Reproduce**
1. Step one
2. Step two
3. Expected vs actual result

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.9]
- Django version: [e.g., 5.2.4]

**Additional Context**
Any additional information
```

### Feature Requests

Use the feature request template:

```markdown
**Feature Description**
Clear description of the proposed feature

**Use Case**
Why this feature would be valuable

**Implementation Ideas**
Any thoughts on implementation

**Additional Context**
Any additional information
```

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community discussions
- **Pull Requests**: Code contributions and reviews

### Getting Help

1. **Documentation**: Check README.md and code comments
2. **Existing Issues**: Search for similar problems
3. **Create Issue**: If you can't find a solution
4. **Community**: Engage with other contributors

### Recognition

Contributors will be:
- Listed in the AUTHORS section of README.md
- Mentioned in release notes for significant contributions
- Invited to join the maintainers team for exceptional contributions

## Development Tips

### Debugging

```bash
# Enable debug mode for development
export DEBUG=True

# Use Django shell for testing
python manage.py shell

# Check logs
tail -f logs/django.log
```

### Common Issues

1. **Database migrations**: Always create and test migrations
2. **Static files**: Run `collectstatic` after changes
3. **Dependencies**: Keep requirements.txt updated
4. **Environment variables**: Use .env for local development

### Best Practices

- Write self-documenting code
- Use meaningful variable names
- Keep functions focused and small
- Follow DRY (Don't Repeat Yourself) principle
- Test edge cases and error conditions

## Questions?

If you have questions about contributing:
1. Check this document first
2. Search existing issues and discussions
3. Create a new issue with the "question" label
4. Engage with the community

Thank you for contributing to making M-Pesa integration better for everyone! 🚀
