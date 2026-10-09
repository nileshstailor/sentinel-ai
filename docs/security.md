# Security notes

- API bearer token (hackathon). Prefer Cognito for production.
- Tenant isolation by `user_id` on all queries.
- Secrets via AWS Secrets Manager / untracked `.env` — never commit.
- LLM outputs cannot execute bank freezes; `SecurityPolicyEngine` must approve.
- Face ID gates freeze / unfreeze / keep-frozen and fraud-hotline escalation; Face ID alone is not bank authorization.
- Stolen phone location is not reliable proof of owner presence.
- GPS deletion is user-initiated (`DELETE /v1/gps`); not tied to AWS suspend deadline.
- All financial/auth events labeled SIMULATED.
