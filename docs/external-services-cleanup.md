# External services cleanup (opt-in only)

Suspension of AWS workloads does **not** delete or pause these automatically:

1. **ClickHouse Cloud** — preserve GPS history; pause/scale only with user approval.
2. **MongoDB Atlas** — preserve incidents/settings; pause cluster only with approval.
3. **OpenAI** — disable key / set spend limits in OpenAI dashboard.
4. **ElevenLabs** — disable key if provisioned.

Never delete user GPS as part of the Sunday deadline.
