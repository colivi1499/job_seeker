-- Canonical Job record (POC Sec. 4.3).
-- Missing fields are NULL / empty JSON array — never omit keys in API responses.

CREATE TABLE IF NOT EXISTS jobs (
  id            TEXT PRIMARY KEY,          -- e.g. "muse-12345"
  title         TEXT NOT NULL,
  company       TEXT,
  location      TEXT,
  description   TEXT,
  url           TEXT,
  source        TEXT NOT NULL,             -- "themuse", "remotive", ...
  salary_min    REAL,
  salary_max    REAL,
  posted_date   TEXT,                      -- ISO-8601
  skills_json   TEXT NOT NULL DEFAULT '[]' -- JSON array of strings
);

CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_posted_date ON jobs(posted_date);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
