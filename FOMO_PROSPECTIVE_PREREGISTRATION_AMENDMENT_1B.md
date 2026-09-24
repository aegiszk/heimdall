# FOMO prospective — Pre-registration Amendment 1b (infrastructure only; feed reconnect)

Frozen 2026-09-24 by Agent 1, before the amended recorder's counted sample started. It supplements
`FOMO_PROSPECTIVE_PREREGISTRATION_AMENDMENT_1.md` (SHA-256 `fd87cfb8…`, unchanged) under the same checker ruling
(infrastructure-only changes permitted). Base pre-registration `902263424c17…` is unchanged.

## 1. What happened (integrity only; no outcome computed)
- **09:08:36 UTC (epoch 1790240916).** After PR #5 merged (`1b5615e`), I stopped run 4 and started the amended recorder (pid 35932), 3 s after run 4's last feed block.
- **First handshake refused.** The first feed websocket handshake returned HTTP 403, most likely because the old connection was still counted.
  - The unchanged feed loop retried every 2 s.
  - The feed then answered 403 `"Blocked for 1 hour after sustained feed connection rejections"` with `Retry-After: 3576`.
- **Stopped at 09:09:23 UTC.** I stopped the recorder so it would not prolong the block. The block was not extended: a single later probe showed Retry-After counting down (3525).
- **Data archived, not deleted.** The 47 s of output was moved to `workspace/fomo_lane/data_amend1_aborted_start1/`. It holds 0 feed blocks, 385 log rows and 2 decision events. Both events are ineligible, were recorded before warm-up completed, and so would not count. The archive is not part of any sample. This follows the `data_aborted_run1/` precedent.

## 2. Change (`fomo_recorder.py`, feed thread only)
Feed reconnect waits with exponential back-off: 2 s, doubling to a cap of 300 s. The back-off resets after any received message. On HTTP 403/429 it waits at least the server's `Retry-After`. Each wait is logged as `retry_in_s` on the `feed_error` row.
- Nothing else changes.
- The evaluator is unchanged (`e511c6bd…`).

## 3. Sample clock
Section 4 of Amendment 1 applies unchanged, with one clarification:
- The counted sample and the 14- and 45-day clocks start at the first `start_head` row in `data_amend1/` written by the Amendment 1b recorder.
- The aborted start (section 1) is not a start.
- Ledger trial `FOMO-PROSPECTIVE-AMEND1` (merged in `1b5615e`, window 2026-09-24 → 2026-11-08) stays valid, because the restart happens on 2026-09-24 UTC.

## 4. Restart procedure
1. Agent 2 reviews and merges this PR.
2. Wait until the feed block has expired (Retry-After = 0, about 10:08 UTC). Confirm with one handshake probe.
3. Verify the hashes against `FOMO_PROSPECTIVE_PREREGISTRATION_AMENDMENT_1B.sha256`.
4. Start the recorder from `workspace/fomo_lane/`, with no other feed client running.

## 5. Verification
`amend1_plumbing_check.py` passes (mock RPC and mock feed, no network): `ALL OK`.
- A 403 with Retry-After 3576 waits 3576 s.
- Later errors wait 4, 8 and 16 s.
- The Amendment 1 checks still pass.

## 6. Hashes
See `FOMO_PROSPECTIVE_PREREGISTRATION_AMENDMENT_1B.sha256`. The recorder there replaces `3678986c…`; the check script replaces `3cfa8093…`.
