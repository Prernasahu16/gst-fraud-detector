-- ==============================================================
-- GST FRAUD DETECTOR — INDIA
-- File:   gst_fraud_queries.sql
-- DB:     MySQL 8.0+
-- Run:    mysql -u root -p gst_fraud < gst_fraud_queries.sql
-- ==============================================================

CREATE DATABASE IF NOT EXISTS gst_fraud;
USE gst_fraud;

-- ── DROP + CREATE TABLE ───────────────────────────────────────
DROP TABLE IF EXISTS gst_returns;

CREATE TABLE gst_returns (
    record_id               INT            NOT NULL,
    month_year              VARCHAR(10)    NOT NULL,
    fiscal_year             VARCHAR(8)     NOT NULL,
    state                   VARCHAR(40)    NOT NULL,
    zone                    VARCHAR(12)    NOT NULL,
    sector                  VARCHAR(40)    NOT NULL,
    fraud_prone_sector      TINYINT(1)     DEFAULT 0,
    gstr1_declared_sales    BIGINT         NOT NULL,
    gstr3b_tax_paid         BIGINT         NOT NULL,
    itc_claimed             BIGINT         NOT NULL,
    itc_rate_pct            DECIMAL(7,2),
    mismatch_pct            DECIMAL(8,2),
    fraud_flag              ENUM('CRITICAL','HIGH_RISK','MEDIUM_RISK','NORMAL'),
    fraud_score             TINYINT,
    is_fraud                TINYINT(1)     DEFAULT 0,
    fraud_type              VARCHAR(30)    DEFAULT 'NONE',
    PRIMARY KEY (record_id),
    INDEX idx_state    (state),
    INDEX idx_flag     (fraud_flag),
    INDEX idx_sector   (sector),
    INDEX idx_fy       (fiscal_year),
    INDEX idx_score    (fraud_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── LOAD CSV ──────────────────────────────────────────────────
-- Run this after creating the table:
-- LOAD DATA LOCAL INFILE '/full/path/to/data/gst_clean.csv'
-- INTO TABLE gst_returns
-- FIELDS TERMINATED BY ','
-- OPTIONALLY ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 ROWS
-- (record_id, month_year, fiscal_year, state, zone, sector,
--  fraud_prone_sector, gstr1_declared_sales, gstr3b_tax_paid,
--  itc_claimed, itc_rate_pct, mismatch_pct, fraud_flag,
--  fraud_score, is_fraud, fraud_type);


-- ==============================================================
-- QUERY 1: FLAGSHIP MISMATCH DETECTION
-- The core rule: ITC/Sales ratio classifies fraud risk
-- ==============================================================
SELECT
    state,
    sector,
    month_year,
    fiscal_year,
    FORMAT(gstr1_declared_sales, 0)          AS sales_declared_inr,
    FORMAT(itc_claimed, 0)                   AS itc_claimed_inr,
    itc_rate_pct,
    CASE
        WHEN itc_claimed > gstr1_declared_sales
            THEN 'CRITICAL — ITC exceeds sales (mathematically impossible)'
        WHEN itc_rate_pct > 85
            THEN 'HIGH RISK — ITC > 85% of declared sales'
        WHEN itc_rate_pct > 65
            THEN 'MEDIUM RISK — elevated ITC rate'
        ELSE 'NORMAL'
    END                                       AS mismatch_verdict,
    fraud_score
FROM gst_returns
WHERE fraud_flag IN ('CRITICAL', 'HIGH_RISK')
ORDER BY fraud_score DESC, itc_rate_pct DESC
LIMIT 50;


-- ==============================================================
-- QUERY 2: STATE RISK DASHBOARD
-- State-level aggregation for investigation priority
-- ==============================================================
SELECT
    state,
    zone,
    COUNT(*)                                                      AS total_filings,
    SUM(CASE WHEN fraud_flag = 'CRITICAL'   THEN 1 ELSE 0 END)  AS critical_count,
    SUM(CASE WHEN fraud_flag = 'HIGH_RISK'  THEN 1 ELSE 0 END)  AS high_risk_count,
    ROUND(AVG(itc_rate_pct), 2)                                  AS avg_itc_rate_pct,
    ROUND(AVG(fraud_score),  1)                                  AS avg_fraud_score,
    ROUND(
        SUM(CASE WHEN fraud_flag != 'NORMAL' THEN 1 ELSE 0 END)
        / COUNT(*) * 100, 1
    )                                                             AS pct_flagged,
    CASE
        WHEN AVG(fraud_score) > 35 THEN '🔴 HIGH RISK STATE'
        WHEN AVG(fraud_score) > 20 THEN '🟡 MEDIUM RISK STATE'
        ELSE                             '🟢 LOW RISK STATE'
    END                                                           AS state_risk_tier,
    FORMAT(SUM(itc_claimed), 0)                                  AS total_itc_claimed_inr
FROM gst_returns
GROUP BY state, zone
ORDER BY avg_fraud_score DESC;


-- ==============================================================
-- QUERY 3: SECTOR VULNERABILITY MATRIX
-- Which sectors are most fraud-prone?
-- ==============================================================
SELECT
    sector,
    fraud_prone_sector,
    COUNT(*)                                                      AS total_records,
    ROUND(AVG(itc_rate_pct), 2)                                  AS avg_itc_rate,
    MAX(itc_rate_pct)                                            AS max_itc_rate,
    SUM(CASE WHEN fraud_flag = 'CRITICAL'  THEN 1 ELSE 0 END)   AS critical_flags,
    SUM(CASE WHEN fraud_flag = 'HIGH_RISK' THEN 1 ELSE 0 END)   AS high_risk_flags,
    ROUND(
        SUM(CASE WHEN fraud_flag IN ('CRITICAL','HIGH_RISK') THEN 1 ELSE 0 END)
        / COUNT(*) * 100, 2
    )                                                             AS fraud_rate_pct,
    ROUND(AVG(fraud_score), 1)                                   AS avg_fraud_score
FROM gst_returns
GROUP BY sector, fraud_prone_sector
ORDER BY fraud_rate_pct DESC;


-- ==============================================================
-- QUERY 4: MONTHLY TREND (YEAR-ON-YEAR)
-- FY comparison to detect escalation
-- ==============================================================
SELECT
    fiscal_year,
    month_year,
    COUNT(*)                                                      AS total_filings,
    SUM(CASE WHEN fraud_flag = 'CRITICAL'  THEN 1 ELSE 0 END)   AS critical,
    SUM(CASE WHEN fraud_flag = 'HIGH_RISK' THEN 1 ELSE 0 END)   AS high_risk,
    ROUND(AVG(fraud_score), 1)                                   AS avg_score,
    ROUND(SUM(itc_claimed) / 1e7, 2)                             AS total_itc_crore
FROM gst_returns
GROUP BY fiscal_year, month_year
ORDER BY fiscal_year, month_year;


-- ==============================================================
-- QUERY 5: TRIPLE INTERSECTION — HIGHEST PRIORITY QUEUE
-- Critical flag + fraud-prone sector + high-risk state
-- Near-zero false positive rate
-- ==============================================================
SELECT
    gr.state,
    gr.sector,
    gr.month_year,
    gr.fiscal_year,
    gr.itc_rate_pct,
    gr.fraud_score,
    gr.fraud_type,
    ROUND(gr.itc_claimed / 1e7, 2)            AS itc_crore,
    ROUND(gr.gstr1_declared_sales / 1e7, 2)  AS sales_crore,
    'IMMEDIATE INVESTIGATION'                  AS action_required
FROM gst_returns gr
WHERE gr.fraud_flag = 'CRITICAL'
  AND gr.fraud_prone_sector = 1
  AND gr.state IN (
        SELECT state
        FROM gst_returns
        GROUP BY state
        HAVING AVG(fraud_score) > (
            SELECT AVG(fraud_score) * 1.25 FROM gst_returns
        )
  )
ORDER BY gr.fraud_score DESC, gr.itc_rate_pct DESC;


-- ==============================================================
-- QUERY 6: YEAR-ON-YEAR FRAUD ESCALATION
-- Detect states/sectors with rising fraud risk over time
-- ==============================================================
SELECT
    state,
    sector,
    ROUND(AVG(CASE WHEN fiscal_year LIKE 'FY2022%' THEN fraud_score END), 1) AS score_fy22,
    ROUND(AVG(CASE WHEN fiscal_year LIKE 'FY2023%' THEN fraud_score END), 1) AS score_fy23,
    ROUND(AVG(CASE WHEN fiscal_year LIKE 'FY2024%' THEN fraud_score END), 1) AS score_fy24,
    ROUND(
        AVG(CASE WHEN fiscal_year LIKE 'FY2024%' THEN fraud_score END)
      - AVG(CASE WHEN fiscal_year LIKE 'FY2022%' THEN fraud_score END)
    , 1)                                                                      AS two_yr_change,
    CASE
        WHEN (AVG(CASE WHEN fiscal_year LIKE 'FY2024%' THEN fraud_score END)
            - AVG(CASE WHEN fiscal_year LIKE 'FY2022%' THEN fraud_score END)) > 10
            THEN '⬆ ESCALATING'
        WHEN (AVG(CASE WHEN fiscal_year LIKE 'FY2024%' THEN fraud_score END)
            - AVG(CASE WHEN fiscal_year LIKE 'FY2022%' THEN fraud_score END)) < -5
            THEN '⬇ IMPROVING'
        ELSE '→ STABLE'
    END                                                                       AS trend
FROM gst_returns
GROUP BY state, sector
HAVING score_fy22 IS NOT NULL
   AND score_fy24 IS NOT NULL
ORDER BY two_yr_change DESC
LIMIT 25;


-- ==============================================================
-- QUERY 7: CIRCULAR TRADING DETECTION
-- Volume spike + normal ITC rate = shell company loop
-- ==============================================================
WITH state_sector_avg AS (
    SELECT
        state,
        sector,
        AVG(gstr1_declared_sales)    AS mean_sales,
        STDDEV(gstr1_declared_sales) AS std_sales
    FROM gst_returns
    GROUP BY state, sector
)
SELECT
    g.state,
    g.sector,
    g.month_year,
    g.fiscal_year,
    ROUND(g.gstr1_declared_sales / s.mean_sales, 2) AS volume_ratio,
    g.itc_rate_pct,
    g.fraud_flag,
    g.fraud_score,
    CASE
        WHEN g.gstr1_declared_sales > s.mean_sales + 2.5 * s.std_sales
         AND g.itc_rate_pct BETWEEN 50 AND 85
        THEN '⚠ SUSPECTED CIRCULAR TRADING'
        ELSE 'Normal volume'
    END                                              AS volume_alert
FROM gst_returns g
JOIN state_sector_avg s
  ON g.state = s.state AND g.sector = s.sector
WHERE g.gstr1_declared_sales > s.mean_sales + 2.5 * s.std_sales
ORDER BY volume_ratio DESC
LIMIT 30;


-- ==============================================================
-- QUERY 8: ENFORCEMENT IMPACT BY ZONE
-- Which zones have low fraud despite high economic activity?
-- ==============================================================
SELECT
    zone,
    COUNT(DISTINCT state)                                                 AS states_in_zone,
    COUNT(*)                                                              AS total_records,
    ROUND(AVG(itc_rate_pct), 2)                                          AS avg_itc_rate,
    ROUND(AVG(fraud_score),  1)                                          AS avg_fraud_score,
    ROUND(SUM(CASE WHEN fraud_flag = 'CRITICAL' THEN 1 ELSE 0 END)
          / COUNT(*) * 100, 2)                                           AS critical_rate_pct,
    ROUND(AVG(gstr3b_tax_paid) / AVG(gstr1_declared_sales) * 100, 1)   AS effective_tax_rate_pct,
    SUM(CASE WHEN fraud_flag = 'CRITICAL' THEN 1 ELSE 0 END)            AS total_critical
FROM gst_returns
GROUP BY zone
ORDER BY avg_fraud_score DESC;
