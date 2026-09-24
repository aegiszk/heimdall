-- SCHEMA_TRUTH.sql — Canonical state/attribution schema (truth file)
-- Neon Postgres. Every fill traces to a signal and a verifier verdict (I6 attribution completeness).
-- Validate Prisma/ORM against THIS file, never the reverse.

CREATE TABLE strategies (
    id              TEXT PRIMARY KEY,          -- e.g. 'carry_btc', 'oi_extreme', 'vol_momo'
    family          TEXT NOT NULL,             -- carry | oi_reversion | vol_momentum | alpha101 | llm_agent
    kind            TEXT NOT NULL,             -- quant | llm
    live_enabled    BOOLEAN NOT NULL DEFAULT FALSE,   -- I7: never true until LIVE_GATE
    capital_slice   NUMERIC NOT NULL DEFAULT 0,       -- I5 cap
    rung            TEXT NOT NULL DEFAULT 'paper',     -- paper|tiny|50k|150k|500k
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE signals (
    id              BIGSERIAL PRIMARY KEY,
    strategy_id     TEXT NOT NULL REFERENCES strategies(id),
    asset           TEXT NOT NULL,             -- BTC | ETH
    ts              TIMESTAMPTZ NOT NULL,       -- point-in-time of the view
    conviction      NUMERIC NOT NULL CHECK (conviction BETWEEN -1 AND 1),
    reasoning       TEXT,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE verdicts (
    id              BIGSERIAL PRIMARY KEY,
    signal_id       BIGINT NOT NULL REFERENCES signals(id),
    passed          BOOLEAN NOT NULL,
    dsr_prob        NUMERIC,
    pbo             NUMERIC,
    mc_perm_p       NUMERIC,
    boot_sharpe_lo  NUMERIC,
    nw_tstat        NUMERIC,
    max_dd          NUMERIC,
    n_trades        INTEGER,
    n_params        INTEGER,
    report          JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE fills (
    id              BIGSERIAL PRIMARY KEY,
    signal_id       BIGINT NOT NULL REFERENCES signals(id),   -- I6: no orphan fills
    verdict_id      BIGINT NOT NULL REFERENCES verdicts(id),
    venue           TEXT NOT NULL,             -- okx | hyperliquid
    leg             TEXT NOT NULL,             -- spot | perp
    side            TEXT NOT NULL,             -- buy | sell
    qty             NUMERIC NOT NULL,
    price           NUMERIC NOT NULL,
    fee             NUMERIC NOT NULL DEFAULT 0,
    funding_pnl     NUMERIC NOT NULL DEFAULT 0,
    is_paper        BOOLEAN NOT NULL DEFAULT TRUE,
    ts              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE position_ledger (            -- reconciled vs exchange each cycle (I6)
    id              BIGSERIAL PRIMARY KEY,
    strategy_id     TEXT NOT NULL REFERENCES strategies(id),
    venue           TEXT NOT NULL,
    asset           TEXT NOT NULL,
    leg             TEXT NOT NULL,
    net_qty         NUMERIC NOT NULL,
    net_delta_usd   NUMERIC NOT NULL,         -- I1 monitored
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE incidents (                  -- invariant breaches, kill-switch fires, funnel firewall hits
    id              BIGSERIAL PRIMARY KEY,
    kind            TEXT NOT NULL,           -- delta_breach|margin|funding_flip|dd_kill|reconcile|firewall
    strategy_id     TEXT REFERENCES strategies(id),
    detail          JSONB NOT NULL,
    ts              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_signals_strategy_ts ON signals(strategy_id, ts);
CREATE INDEX idx_fills_signal ON fills(signal_id);
CREATE INDEX idx_ledger_strategy ON position_ledger(strategy_id, venue, asset);
