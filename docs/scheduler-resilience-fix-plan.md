# Scheduler Resilience Fix Plan

**Overall Progress:** `0%`

## TLDR
Fix two issues with the Cloud Scheduler newsletter processing: (1) Cloud Scheduler timeout mismatch causing process to be killed mid-processing, and (2) batch database insertion that loses all data if process fails halfway. Also increase memory for large newsletters.

## Critical Decisions
- **Scheduler timeout**: Increase from 180s to 3600s to match Cloud Run timeout
- **Batch size**: Insert segments in batches of 50 (balances durability vs performance)
- **Memory**: Increase from 1Gi to 2Gi for 798-segment newsletters
- **Architecture**: Keep HTTP endpoint approach (simpler than Cloud Run Jobs for this use case)

## Tasks:

- [x] 🟩 **Step 1: Update Cloud Scheduler Timeout**
  - [x] 🟩 Update `attemptDeadline` from 180s to 1800s (max allowed) via gcloud CLI

- [x] 🟩 **Step 2: Increase Cloud Run Memory**
  - [x] 🟩 Update `.github/workflows/deploy-backend.yml` to use `--memory 2Gi`

- [x] 🟩 **Step 3: Implement Batch Segment Insertion**
  - [x] 🟩 Modify `processor.py` to insert segments in batches of 50 during processing
  - [x] 🟩 Add progress logging for each batch inserted

- [ ] 🔶 **Step 4: Deploy and Verify**
  - [ ] 🟥 Commit and push changes to trigger deployment
  - [ ] 🟥 Manually trigger scheduler job to test with real newsletter
  - [ ] 🟥 Verify segments are inserted incrementally in logs

## Output Location

This plan is saved to `docs/scheduler-resilience-fix-plan.md`.
