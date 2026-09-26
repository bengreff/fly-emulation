# Session 7 log

Start: Sat 26 Sep 2026 13:14 CDT. Mode: unattended, 5 h max (stop new work at 17:54, wrap by 18:14).

Pre-session Q&A with Ben (attended, 13:10):
- Run the Session 7 prompt as written, **with authority to act as a creative researcher and make judgement calls**; adaptability over rigid adherence. Guardrails (labels, pre-registration, sealed data) still apply.
- Both Azevedo spare zips are in ~/Downloads.
- backhouse may be used freely for the whole session.

## Timeline
- 13:25 Unpacked both spare cells (sizes verified exact), MANIFEST entries added; only Acquisition metadata read (both R35C09). Sealed. Tests 55 pass (4m51). No leftover processes. backhouse up (sleep-infinity keepalive attached).
- 13:28 AL pre-reg written (DECISIONS s7). Measured: uEPSP 6.19 mV (KW2008), Nagel 2015 depression f=0.78/893 ms. Scale 10.9 derived. Runs P/M seeds 0 (Mac), 1-2 (backhouse). sync_backhouse.sh now includes data/params,derived,measurements.
- 13:37 AL P/M fail (3 seeds). Repair 1 (PN rest -57.8) running. VNC operating-point pre-reg; grid d=2..6 on backhouse, d=0 control on Mac.
- 13:38 AL repair 1 fails (3 seeds). Post-hoc budget AL: 1/2 used.
- 13:40 VNC operating point: stop rule (MN 0 Hz at all d). 13Ba=IN13B013 candidate; tuning layer check launched on backhouse.
- 13:43 13Ba check fails; transfer config T pre-registered; 13Ba check (backhouse) + dev reflex (Mac) launched
- 13:49 T fails (13Ba + dev H1 0.70). Tp (no depression) launched: 13Ba on backhouse, dev on Mac.
- 13:50 Regression (default model, backhouse): sugar 26.3/87.3 Hz; closed loop seeds 0-2: 0 non-tonic spikes, brain excl ORN 0.39/0.37/0.27 Hz. PASS.
- 13:56 Protocol flaw: leg beats soft probe (T, Tp). score_reflex clamp gate added (cell unopened if >1.5 deg); kp=100. Re-scoring T, Tp on dev (Mac, sequential).
- 14:02 Standing 1 seed: default zmin .54; T .75 (zmean .98, best yet); Tp .64; Tp silenced .68. Tp stability FAIL (70 spikes/ms after silencing). T dev (kp100) H1 .6 fail. Launched T stability + standing seeds.
- 14:08 CX ring = sustained cells in T/Tp. Exploratory E1 (global 1.8 mV + depression) and E2 (EPG kick) on backhouse.
- 14:10 E1 unstable (optic lobe loops); E2 default ring does not persist after kick. Hypothesis (ring sets efficacy ceiling) not supported.
- 14:14 Diagnostic: IN21A006 (Glu) cancels extension excitation under Tp. Exploratory glu+ runs (Tp, T) on Mac.
- 14:15 Found DNg33<->5-HT fast-excitation loop; pre-reg M0 (monoamine fast sign 0); 10 runs on backhouse
- 14:18 M0 fails (stability 2/3 seeds default). T+M0 standing seed 2 = 0.92 (first height pass; unstable config). Rest-potential lit added to targets.
- 14:25 glu+ exploratory: Tp ext +3.4 Hz (5x short), H1 .7. Not sufficient.
- 14:42 Command direction (seeds 1-4): T DNg100 forward PASS (+0.65, 4/4); MDN fails both; default fails both.
