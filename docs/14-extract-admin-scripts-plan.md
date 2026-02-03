# Extract Admin Scripts Plan

**Overall Progress:** `100%`

## TLDR
Move admin/backfill endpoints from `backend/main.py` into standalone scripts in `backend/scripts/`. This removes ~700 lines from main.py, eliminates security exposure of admin endpoints in production, and provides cleaner separation of one-time tools from production APIs.

## Critical Decisions
- **Standalone scripts over endpoints**: One-time operations, no remote execution needed, production exposure not acceptable
- **argparse over typer/click**: Simple scripts with 1-3 args each; no need for extra dependency
- **Direct script execution**: `cd backend && uv run scripts/backfill_chinese.py` instead of `python -m`
- **Shared common module**: `_common.py` for processor initialization to avoid code duplication

## Tasks

- [x] 🟩 **Step 1: Create scripts directory structure**
  - [x] 🟩 Create `backend/scripts/` directory
  - [x] 🟩 Create `backend/scripts/_common.py` with shared processor initialization

- [x] 🟩 **Step 2: Extract backfill_chinese script**
  - [x] 🟩 Create `backend/scripts/backfill_chinese.py` from `/backfill-chinese` endpoint (lines 303-464)
  - [x] 🟩 Add argparse CLI: `--n-segments`, `--strategy`

- [x] 🟩 **Step 3: Extract backfill_chinese_section script**
  - [x] 🟩 Create `backend/scripts/backfill_chinese_section.py` from `/backfill-chinese-section` endpoint (lines 467-647)
  - [x] 🟩 Add argparse CLI: `--section-name`, `--issue-id`

- [x] 🟩 **Step 4: Extract backfill_section_headers script**
  - [x] 🟩 Create `backend/scripts/backfill_section_headers.py` from `/backfill-section-headers` endpoint (lines 650-820)
  - [x] 🟩 Add argparse CLI: `--issue-id`

- [x] 🟩 **Step 5: Extract process_test script**
  - [x] 🟩 Create `backend/scripts/process_test.py` combining `/process-test` and `/process-test-groups` (lines 825-1024)
  - [x] 🟩 Add argparse CLI: `--url`, `--num-groups`, `--legacy` (for old 10-segment mode)

- [x] 🟩 **Step 6: Clean up main.py**
  - [x] 🟩 Remove all backfill endpoints (lines 303-820)
  - [x] 🟩 Remove dev-gated test endpoints (lines 823-1024)
  - [x] 🟩 Remove unused imports if any

## Testing

### Approach
Manual CLI testing - run each script with test arguments

### Test Scenarios
- [x] 🟩 Scenario 1: `cd backend && uv run scripts/backfill_chinese.py --help` → Shows usage with --n-segments and --strategy options
- [ ] 🟥 Scenario 2: `cd backend && uv run scripts/backfill_chinese.py --n-segments 1 --strategy shortest` → Processes 1 segment, outputs status (not run - requires DB data)
- [ ] 🟥 Scenario 3: `cd backend && uv run scripts/backfill_section_headers.py` → Runs against latest issue, outputs headers added count (not run - requires DB data)
- [x] 🟩 Scenario 4: Production server starts without admin endpoints → verified routes list excludes admin endpoints

### Acceptance Criteria
- [x] `backend/main.py` reduced from ~1046 lines to 321 lines
- [x] All 4 scripts run successfully with `cd backend && uv run scripts/<name>.py --help`
- [x] `/backfill-chinese`, `/backfill-chinese-section`, `/backfill-section-headers` not in routes
- [x] `/process-test` and `/process-test-groups` no longer exist (even in development)
