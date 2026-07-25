# Patient Display — Pending Issues

- [ ] Debug overlay text (id, now, peak, trigger) is drawn inside the ROI and interferes with the measurement. Should be just a small current value number placed above the ROI border, green if inactive, red if active — nothing inside the ROI

- [ ] "Sample Baselines" button name is confusing now that detection uses absolute threshold, not delta — rename to something clearer like "Measure Idle Values"
- [ ] No way to reset peak values in debug overlay without stopping and restarting monitoring
- [ ] Threshold spinbox in setup tool goes up to 200 — max should probably match the 0–255 pixel range
- [ ] ROI coordinate accuracy on the hospital computer has not been verified end-to-end
- [ ] `monitor_index` is hardcoded to 1 in config default — no UI to change which monitor to watch
