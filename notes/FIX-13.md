# FIX-13 — Single-seed feasibility handoff

## 2026-10-07T01:02:29.808985-04:00 — codex-1 — Claim

D-37 makes seed0 the exploratory priority. Existing evaluation_jobs insists all12runs complete and would reject intentionallyinterrupted seeds1/2, making accepted single-seed evaluation unavailable. Add explicit training_seeds selection, defaultall3 unchanged. Validate selectedtraining as before; reportexcludedruns, keep12jobplanidentityvalidation; reuse Frozen seed0 frompreviousfullstage without relaunching replicas. Tests first: single-seed fourarm coverage, unselectedinterruption tolerated, selectedfailures rejected, priorFrozenreuse, invalidseedselection rejected, defaults unchanged.
