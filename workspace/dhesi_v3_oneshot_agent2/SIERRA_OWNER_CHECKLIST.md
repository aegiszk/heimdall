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
   | Data Limiting | Load Data Limiting Method | **Date Range**, From **2008-06-01**, To **2024-10-31** |

   Press **OK**, then minimise Sierra. Wait until downloading stops; about 15–40 min is expected.
6. Create the folder `C:\Users\Xerxus\Documents\Heimdall\validation_data\SEALED\`.
7. Select **Edit >> Export Bar Data to Text File**. Save the file as `C:\Users\Xerxus\Documents\Heimdall\validation_data\SEALED\NQ_continuous_1m_raw.txt`.
8. Close that chart. If Sierra asks to save, answer **No**.
9. Open **Global Settings >> Data/Trade Service Settings** and set the Intraday Data Storage Time Unit back to the value you wrote down in step 2.
10. Tell Agent 2: **"harvest done"**.

Agent 2 then runs everything else, blind:
- the `.dly` hazard re-check;
- the frozen converter;
- the integrity gates, which report metadata only.

You are needed once more at the end, to write the authorization file.
