# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| Latest | ✅ |
| < 1.0.0 | ❌ (pre-release) |

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Report security issues to: **security@your-org.com** (or via GitHub's private vulnerability reporting).

Include:
1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (optional)

We'll acknowledge within 48 hours and aim to release a patch within 7 days.

## Security Considerations

- **API Keys**: Never commit API keys. Use `.env` files (excluded from git)
- **Self-hosted**: Ensure your `config.yaml` is not publicly accessible
- **CORS**: Configure `cors_origins` in `config.yaml` to restrict frontend origins
- **Rate limiting**: Built-in rate limiting is basic — add a reverse proxy (nginx/Caddy) for production
