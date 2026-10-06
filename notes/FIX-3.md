# FIX-3 — A40 generation and online paired feature capture

## 2026-10-06T00:02:12-04:00 — codex-1 — Claim

Claimed new P0 FIX-3 before more B9 P1 work. Read MASTER §3.2/D-19: ICE unavailable until Oct8, A40 production generation/training authorized, online paired capture required to avoid multi-TB feature storage; historical default behavior unchanged under hard rule1. Existing B3 validation remains blocked; implement bank-adapter and base paths independent of mixtures, no failed B3 dependency used. B5 acceptance: decoded strings/assistant-only masks five samples per arm, feature agreement with fresh pass on three samples, exact scale-zero/base equality and nonzero real-adapter differences, matched token counts. B6 native loss/arm contracts read next.

Acceptance-first scope: explicit A40 production opt-in with pause protections and pinned config provenance; online frozen target pairs share one base weight copy, restore adapter state, no target gradients; CPU contracts then bounded A40 native-checkpoint smoke with decoded/mask audit, fresh-forward equality, scale-zero and real-child checks. Production response pipeline integration will be shared with B5; no large generation/training launched by builder. New code in followspec/ or atlas/, no historical defaults altered.
