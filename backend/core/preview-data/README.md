# Preview Data

Seed data used by the Coral Companion preview environment workflows.

## Structure

| Path | Purpose |
|---|---|
| `r2-seed/` | Sample images uploaded to each preview R2 bucket on creation. Directory structure is preserved (e.g. `sites/Olohuita/original/demo-coral.png` → R2 key `sites/Olohuita/original/demo-coral.png`). |

## How it works

When you create a preview environment via the manual gate
(`.github/workflows/preview-dispatch.yml`):

1. A Supabase branch `preview-<slug>` is created, seeded with production data
2. An R2 bucket `coral-companion-preview-<slug>` is created, populated with `r2-seed/*`
3. A Modal environment `preview-<slug>` is created, running the segmentation worker
4. A Cloudflare Worker `coral-companion-router-preview-<slug>` is deployed, serving the frontend + backend core

When the branch is deleted (or you run the manual teardown), all four resources are cleaned up.