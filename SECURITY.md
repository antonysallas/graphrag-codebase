# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in
GraphRAG Codebase, please report it responsibly.

### How to Report

1. **Do NOT open a public issue** for security vulnerabilities.
2. Email the maintainers directly at the email address listed in the repository.
3. Include the following information:
   * Description of the vulnerability
   * Steps to reproduce
   * Potential impact
   * Any suggested fixes (optional)

### What to Expect

* **Acknowledgment**: We will acknowledge receipt of your report within 48
  hours.
* **Assessment**: We will assess the vulnerability and determine its severity.
* **Fix Timeline**: Critical vulnerabilities will be addressed as quickly as
  possible. We aim to release a fix within 7-14 days for critical issues.
* **Disclosure**: We will coordinate with you on public disclosure timing.

## Security Best Practices for Users

### Neo4j Database

1. **Use Strong Passwords**: Never use default Neo4j passwords in production.

   ```bash
   # Change default password
   NEO4J_PASSWORD="your-secure-password"
   ```

2. **Network Isolation**: Run Neo4j on a private network, not exposed to the
   internet.

3. **Enable Authentication**: Always run Neo4j with authentication enabled.

### LLM API Keys

1. **Use Environment Variables**: Never hardcode API keys in configuration
   files.

   ```bash
   export LLM_API_KEY="your-api-key"
   ```

2. **Protect Configuration Files**: Ensure `.env` has restrictive permissions.

   ```bash
   chmod 600 .env
   ```

3. **Use Local Models When Possible**: vLLM and Ollama provide local inference
   without sending data to external services.

### Cypher Injection Prevention

The GraphRAG pipeline includes built-in protections against Cypher injection:

1. **Schema Validation**: Queries are validated against the graph schema.
2. **Query Sanitization**: User inputs are sanitized before query construction.
3. **Parameterized Queries**: All queries use Neo4j parameterized queries.

### Codebase Data

When indexing codebases, be aware that:

* Source code content may be stored in Neo4j
* Graph traversals can reveal code structure
* MCP tools expose query capabilities to connected agents

Ensure appropriate access controls are in place for sensitive codebases.

## Known Security Considerations

### MCP Server

The MCP server exposes query tools to connected LLM agents:

* Run the MCP server on localhost only by default
* Enable authentication (`MCP_REQUIRE_AUTH=true`) for network deployments
* Use rate limiting (`MCP_RATE_LIMIT_PER_MINUTE`) to prevent abuse

### Logging

1. **Log Level**: Use WARNING or higher in production to minimize data exposure.
2. **Log Access**: Restrict access to log files containing query patterns.

## Security Updates

Security updates will be released as patch versions. Watch the repository
releases to receive notifications of security updates.
