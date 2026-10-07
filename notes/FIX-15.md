# FIX-15 — Automatic reduced-pilot evaluation

## 2026-10-07T01:29:13.305461-04:00 — codex-1 — Claim

D-38 pilot needs a four-job training-plan handoff, reuse of matching seed-0 Frozen references across stages, unique trained evaluation names (existing B7 names omit checkpoint identity), and optional evaluation of a fully trained sealed checkpoint while native validation continues. Preserve default behavior and all config/budget/pin/held-out checks. Tests first; expose pending validation explicitly. Add optional queue job reload and a controller that appends only preflighted K4 jobs, keeping the sole canonical method-M1 owner-locked dispatcher. No gate certification or repeated seeds.
