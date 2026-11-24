# Owner-authorized GPU preemption, November24,2026

Priority: free sbhansali8 GPU jobs for the ReFit rebuttal. No other users' processes were terminated. The ReFit canonical queue was preserved.

- Initial cancellations: heck-srv3 GPU2, PID2580315; heck-srv5 GPU4, PID1721673 (`amazidea` continual training; verified exited).
- Follow-up cancellations: heck-srv1 GPU0 PID2411447 and GPU2 PID2411916 (`amazidea` probes), plus their shell wrappers.
- Six `amazidea` dispatcher workers on heck-srv2 were stopped to prevent relaunch:2541223,2541227,2541228,2556284,2562549,2562551. Their queue-slot wrappers/SSH/sleep descendants were also stopped.
- Actions checked account ownership and project cwd. Supervisors were temporarily stopped before descendants were terminated, then terminated and continued so termination could complete. All process outputs remain on disk.
- `before.json`: verified jobs/ownership on all five nodes. `terminated.json`: exact signalled processes and commands. `after.json`: no remaining competing workers or owned non-ReFit GPU workloads.

To resume old work later, inspect the original amazidea queue and run logs first, then explicitly restart only unfinished jobs; cancellation does not authorize automatic resumption. No old configuration or result file was modified.
