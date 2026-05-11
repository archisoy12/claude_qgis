CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 물류센터 마스터 (공급 + 공급예정 통합)
CREATE TABLE logistics_centers (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT '운영중'
                            CHECK (status IN ('운영중', '개발중', '공급예정', '철거')),
    address             TEXT NOT NULL UNIQUE,
    lat                 DOUBLE PRECISION,
    lng                 DOUBLE PRECISION,
    geom                GEOMETRY(Point, 4326),
    region              TEXT,
    total_area          DOUBLE PRECISION,
    net_leasable_area   DOUBLE PRECISION,
    floors_above        INTEGER,
    floors_below        INTEGER,
    dock_count          INTEGER,
    ceiling_height      DOUBLE PRECISION,
    completion_date     DATE,
    developer           TEXT,
    note                TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_centers_geom    ON logistics_centers USING GIST (geom);
CREATE INDEX idx_centers_address ON logistics_centers (address);
CREATE INDEX idx_centers_status  ON logistics_centers (status);

-- 임차사 정보
CREATE TABLE tenants (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name    TEXT NOT NULL,
    industry        TEXT,
    business_type   TEXT,
    contact_name    TEXT,
    contact_phone   TEXT,
    contact_email   TEXT,
    credit_grade    TEXT,
    note            TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tenants_company ON tenants (company_name);

-- 임대차 계약 (임대료 포함)
CREATE TABLE lease_contracts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    center_id       UUID NOT NULL REFERENCES logistics_centers(id) ON DELETE CASCADE,
    tenant_id       UUID REFERENCES tenants(id) ON DELETE SET NULL,
    floor           TEXT,
    unit_name       TEXT,
    lease_area      DOUBLE PRECISION,
    lease_start     DATE,
    lease_end       DATE,
    monthly_rent    BIGINT,
    rent_per_sqm    DOUBLE PRECISION,
    deposit         BIGINT,
    rent_free_months INTEGER DEFAULT 0,
    contract_status TEXT DEFAULT '계약중'
                        CHECK (contract_status IN ('계약중', '만료', '협의중', '해지')),
    note            TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_leases_center ON lease_contracts (center_id);
CREATE INDEX idx_leases_tenant ON lease_contracts (tenant_id);

-- 공실률 시계열
CREATE TABLE vacancy_records (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    center_id       UUID NOT NULL REFERENCES logistics_centers(id) ON DELETE CASCADE,
    record_year     INTEGER NOT NULL,
    record_month    INTEGER NOT NULL CHECK (record_month BETWEEN 1 AND 12),
    total_area      DOUBLE PRECISION,
    occupied_area   DOUBLE PRECISION,
    vacant_area     DOUBLE PRECISION,
    vacancy_rate    DOUBLE PRECISION,
    note            TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (center_id, record_year, record_month)
);

CREATE INDEX idx_vacancy_center ON vacancy_records (center_id);
CREATE INDEX idx_vacancy_period ON vacancy_records (record_year, record_month);

-- 거래 정보
CREATE TABLE transactions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    center_id       UUID NOT NULL REFERENCES logistics_centers(id) ON DELETE CASCADE,
    deal_date       DATE,
    deal_type       TEXT DEFAULT '매매'
                        CHECK (deal_type IN ('매매', '지분취득', '기타')),
    price           BIGINT,
    price_per_sqm   DOUBLE PRECISION,
    buyer           TEXT,
    seller          TEXT,
    cap_rate        DOUBLE PRECISION,
    noi             BIGINT,
    note            TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transactions_center ON transactions (center_id);
CREATE INDEX idx_transactions_date   ON transactions (deal_date);

-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_centers_updated_at
    BEFORE UPDATE ON logistics_centers
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_leases_updated_at
    BEFORE UPDATE ON lease_contracts
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
