# BALLY TRADES BOT Security Policy

## Supported Versions

Security fixes are applied to the actively developed version of BALLY TRADES BOT.

## Reporting a Security Vulnerability

Please do not publicly disclose security vulnerabilities.

Report suspected vulnerabilities privately to the project owner through GitHub's private security reporting mechanism.

Include:

- A clear description of the vulnerability
- Steps to reproduce it
- Potential impact
- Relevant logs or screenshots
- Suggested mitigation, if known

Never include passwords, broker credentials, API keys, private keys, or other secrets in a vulnerability report.

## Security Principles

BALLY TRADES BOT follows these principles:

1. Broker credentials must never be committed to Git.
2. Secrets must be supplied through protected environment/configuration mechanisms.
3. Live trading must remain disabled by default during development.
4. Trading execution must pass the existing risk and execution gates.
5. Mobile clients must never directly control MT5 execution.
6. Production trading credentials must remain outside source control.
7. Changes to stable production code must be reviewed and tested.
8. Security controls must not be bypassed merely to execute a trade.

## Trading Safety

Security and trading safety are separate layers.

Authentication, authorization, API security, risk management, market validation, execution validation, and broker connectivity must all be enforced independently.

A valid authenticated user must not automatically receive permission to execute unrestricted trades.

## Secret Handling

The following must never be committed:

- MT5 passwords
- API keys
- access tokens
- private keys
- certificates containing private credentials
- production environment files
- database credentials
- cloud credentials

Use .env.example only for non-secret configuration templates.

## Development Safety

Development and testing should use:

- DRY_RUN where appropriate
- disabled live execution by default
- automated tests
- security checks
- controlled deployment

Production live trading must require explicit authorization and independent execution safeguards.
