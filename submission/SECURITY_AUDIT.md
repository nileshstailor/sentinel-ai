# Security audit notes — pre-GitHub publish

**Date:** 2026-10-09  
**Scope:** Working tree prior to first git publish (repo was not previously a git repository).

## Findings

| Finding | Severity | Remediation |
|---------|----------|-------------|
| API bearer token was embedded in `ios/.../Info.plist` and `project.yml` | High (if published) | Replaced with placeholders; load via Demo Lab / `Config.local.plist` (gitignored) / UserDefaults after Save & Sync |
| Local `.env` with sponsor credentials | Expected | Listed in `.gitignore`; never commit |
| `Config.local.plist` generated for local builds | Expected | Gitignored |
| No Apple certs/profiles found in tree | OK | — |
| No personal GPS export dumps found for commit | OK | Recordings path gitignored |

## Actions taken

- Strengthened `.gitignore`  
- Sanitized committed iOS token fields  
- Added `Config.local.plist.example` and refreshed `.env.example`  
- Documented that **credential rotation** is recommended if this token was ever shared or screenshotted  

## Explicitly NOT done (need your approval)

- Git history rewrite (N/A — no prior git history)  
- AWS/Secrets Manager token rotation  
- Making any GitHub repository public  
- Force-push  

## Publish gate

Do not make the repo public until you confirm:  
1) `git grep` / GitHub secret scanning shows no live tokens  
2) Demo Lab still authenticates after local config  
3) You approve the remote visibility (private vs public)
