# Implementation Plan (Two-Stage)

This file is the canonical execution order.

## Stage Order (Non-Negotiable)

1. Stage 1: Local 10x MVP
2. Stage 2: Productization Without Bloat

Do not execute Stage 2 work before Stage 1 exit criteria pass.

## Stage 1

Use: `STAGE_1_LOCAL_MVP.md`

Focus:

1. Four-screen workflow product
2. OpenAlex-only ingestion
3. Real BYOK scoring
4. Manual pipeline board
5. Single-workspace local development

## Stage 2

Use: `STAGE_2_PRODUCTIZATION.md`

Focus:

1. UX hardening
2. Auth/roles + tenancy + RLS
3. Selective automation/search depth
4. Extensibility and enterprise admin

## Legacy Phase Files

`PHASE_01_*` to `PHASE_08_*` are legacy drafts and not the current source of truth.

If there is a conflict, stage documents always win.

## Global Acceptance Rule

MVP is complete only when all Stage 1 acceptance tests pass and local performance targets are met.
