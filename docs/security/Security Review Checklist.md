# Security Review Checklist

Date: 2026-07-10

- [ ] No secrets committed
- [ ] No live trading code
- [ ] No exchange API keys
- [ ] No framework imports in domain
- [ ] No raw database URL in logs
- [ ] Dependency changes reviewed
- [ ] Migration changes reviewed
- [ ] Observability does not leak sensitive values
- [ ] New endpoints have tests
- [ ] New configuration values have safe defaults
