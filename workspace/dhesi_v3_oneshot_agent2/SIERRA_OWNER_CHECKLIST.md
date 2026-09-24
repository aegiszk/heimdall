# Sierra harvest — owner checklist (Dhesi NQ, one time)

**Do not scroll, zoom or look at the chart.** Minimise Sierra while it downloads.
Menu names were checked against the Sierra Chart docs on 2026-09-24.

1. Start Sierra Chart. Select **File >> Connect to Data Feed**.
2. Open **Global Settings >> Data/Trade Service Settings**.
   - Write down the current **Intraday Data Storage Time Unit**.
   - Set it to **1 Minute**, then press **OK**.
3. Open **Global Settings >> Symbol Settings**. Untick **Use Custom Symbol Settings Values**, then press **OK**.
4. Select **File >> New Chart >> Intraday Chart**.
5. Open **Chart >> Chart Settings** and set:

   | Tab | Setting | Value |
   |---|---|---|
   | Symbol | Symbol | `NQZ24-CME` |
   | Symbol | Continuous Contract | **Continuous Futures Contract - Volume Based Rollover** (NOT "…Back Adjusted") |
   | Bar Period | Bar period | **1 Min** |
   | Bar Period | Gap Fill | **None** |
   | Session Times | Time Zone | **UTC** |
   | Session Times | Intraday Session Times | Start **00:00:00**, End **23:59:59** |
   | Session Times | Use Evening Session | **unticked** |
   | Session Times | Load Weekend Data | **ticked** |
   | Data Limiting | Load Data Limiting Method | **Date Range**, From **2011-09-01**, To **2024-10-31** (protocol V1 §2.3 excludes earlier data) |

   Press **OK**, then minimise Sierra. Wait until downloading stops; about 15–40 min is expected.
6. Create the folder `C:\Users\Xerxus\Documents\heimdall_validation_sealed\`. It is OUTSIDE the git repo, so no agent can commit it.
7. Select **Edit >> Export Bar Data to Text File**. Save the file as `C:\Users\Xerxus\Documents\heimdall_validation_sealed\NQ_continuous_1m_raw.txt`.
8. Close that chart. If Sierra asks to save, answer **No**.
9. Open **Global Settings >> Data/Trade Service Settings** and set the Intraday Data Storage Time Unit back to the value you wrote down in step 2.
10. Tell Agent 2: **"harvest done"**.

Agent 2 then runs everything else, blind:
- the `.dly` hazard re-check;
- the frozen converter;
- the integrity gates, which report metadata only.

You are needed once more at the end, to write the authorization file.

## If a computer-use session does this for the owner
- The owner approves steps 2–3. They are required:
  - step 2 avoids downloading 13 years of TICK data;
  - step 3 is Sierra's mandatory step for continuous charts;
  - step 9 restores step 2.
- After pressing OK in step 5, minimise the chart window at once. Judge download progress from the Message Log, not the chart. Never zoom, scroll, describe or deliberately screenshot the chart area.
- Report back ONLY: "harvest done", the export path and the file size. Never describe prices, levels or chart shapes.
- Why the range ends 2024-10-31, not 2024-06:
  - Integrity gate 3 (protocol V1 §2.4) needs Jul–Sep 2024, which is already-used development data.
  - The validator deletes every row at or after 2024-06-29 00:00 ET before any computation (protocol §2.3).
  - The blind set is therefore 2011-09 → 2024-06-28, as registered in the trials ledger (`NQ-dhesi-inversion-v3-untouched`).
