// ── 인증 가드 ──────────────────────────────────────────────────────────────────
const token = localStorage.getItem("token");
const role  = localStorage.getItem("role");
if (!token) window.location.href = "/login.html";

function logout() {
  localStorage.clear();
  window.location.href = "/login.html";
}

const isAdmin = role === "admin";

// ── API 헬퍼 ───────────────────────────────────────────────────────────────────
async function api(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    ...options,
    headers: { Authorization: `Bearer ${token}`, ...options.headers },
  });
  if (res.status === 401) { logout(); return; }
  if (!res.ok) throw await res.json();
  if (res.status === 204) return null;
  return res.json();
}

// ── 초기화 ─────────────────────────────────────────────────────────────────────
let map, markersLayer, allCenters = [], selectedCenterId = null;

document.addEventListener("DOMContentLoaded", async () => {
  // 역할 UI
  document.getElementById("role-badge").textContent = isAdmin ? "관리자" : "조회";
  if (isAdmin) {
    document.getElementById("btn-upload").classList.remove("d-none");
  }

  initMap();
  await loadCenters();
  initFilters();
  renderUploadForm();
});

// ── 지도 ───────────────────────────────────────────────────────────────────────
function initMap() {
  map = L.map("map").setView([36.5, 127.8], 7);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
    maxZoom: 18,
  }).addTo(map);
  markersLayer = L.layerGroup().addTo(map);
}

const STATUS_COLOR = {
  "운영중":   "#16a34a",
  "개발중":   "#ca8a04",
  "공급예정": "#2563eb",
  "철거":     "#9ca3af",
};

function makeMarkerIcon(status) {
  const color = STATUS_COLOR[status] || "#6b7280";
  return L.divIcon({
    className: "",
    html: `<div style="width:14px;height:14px;border-radius:50%;background:${color};
              border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.3);"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

async function loadCenters() {
  const geojson = await api("/centers/geojson");
  allCenters    = await api("/centers");
  renderMarkers(geojson.features);
  renderList(allCenters);
}

function renderMarkers(features) {
  markersLayer.clearLayers();
  features.forEach((f) => {
    const [lng, lat] = f.geometry.coordinates;
    const m = L.marker([lat, lng], { icon: makeMarkerIcon(f.properties.status) })
      .bindTooltip(f.properties.name, { direction: "top", offset: [0, -8] })
      .on("click", () => selectCenter(f.properties.id));
    markersLayer.addLayer(m);
  });
}

// ── 센터 목록 ──────────────────────────────────────────────────────────────────
function renderList(centers) {
  const el = document.getElementById("panel-list");
  if (!centers.length) {
    el.innerHTML = `<div class="p-4 text-center text-muted" style="font-size:.85rem;">조건에 맞는 센터가 없습니다.</div>`;
    return;
  }
  el.innerHTML = centers.map((c) => `
    <div class="center-item ${c.id === selectedCenterId ? "active" : ""}" onclick="selectCenter('${c.id}')">
      <div class="d-flex align-items-center gap-2">
        <span class="center-name">${c.name}</span>
        <span class="badge-status badge-${c.status}">${c.status}</span>
      </div>
      <div class="center-meta">${c.address}</div>
      <div class="center-meta">${c.total_area ? (c.total_area / 3.305785).toFixed(0) + "평" : ""} ${c.completion_date ? "· " + c.completion_date : ""}</div>
    </div>
  `).join("");
}

// ── 필터 ───────────────────────────────────────────────────────────────────────
function initFilters() {
  const regions = [...new Set(allCenters.map((c) => c.region).filter(Boolean))];
  const sel = document.getElementById("filter-region");
  regions.forEach((r) => sel.innerHTML += `<option value="${r}">${r}</option>`);

  ["filter-status", "filter-region", "search-input"].forEach((id) => {
    document.getElementById(id).addEventListener("input", applyFilters);
  });
}

function applyFilters() {
  const status  = document.getElementById("filter-status").value;
  const region  = document.getElementById("filter-region").value;
  const keyword = document.getElementById("search-input").value.toLowerCase();

  const filtered = allCenters.filter((c) =>
    (!status  || c.status  === status) &&
    (!region  || c.region  === region) &&
    (!keyword || c.name.toLowerCase().includes(keyword) || c.address.toLowerCase().includes(keyword))
  );

  renderList(filtered);

  // 지도 마커도 필터
  const ids = new Set(filtered.map((c) => c.id));
  markersLayer.eachLayer((m) => {
    const tooltip = m.getTooltip();
    // 필터된 센터만 표시 (간단히 opacity로 처리)
    m.setOpacity(ids.size === allCenters.length ? 1 : 0.2);
  });
}

// ── 센터 선택 ──────────────────────────────────────────────────────────────────
async function selectCenter(id) {
  selectedCenterId = id;
  const center = allCenters.find((c) => c.id === id);
  if (!center) return;

  document.getElementById("sidebar-title").textContent = center.name;
  document.getElementById("btn-close-sidebar").classList.remove("d-none");
  document.getElementById("tab-nav").classList.remove("d-none");
  document.getElementById("panel-list").classList.add("d-none");
  if (isAdmin) document.getElementById("admin-actions").classList.remove("d-none");

  showTab("info");

  // 지도 이동
  if (center.lat && center.lng) {
    map.setView([center.lat, center.lng], 13);
  }
}

function closeSidebar() {
  selectedCenterId = null;
  document.getElementById("sidebar-title").textContent = "센터를 선택하세요";
  document.getElementById("btn-close-sidebar").classList.add("d-none");
  document.getElementById("tab-nav").classList.add("d-none");
  document.getElementById("panel-list").classList.remove("d-none");
  document.getElementById("admin-actions").classList.add("d-none");
  ["panel-info", "panel-lease", "panel-vacancy", "panel-transaction"].forEach((id) => {
    document.getElementById(id).classList.add("d-none");
  });
}

// ── 탭 ────────────────────────────────────────────────────────────────────────
const TAB_RENDERERS = {
  info:        renderInfoTab,
  lease:       renderLeaseTab,
  vacancy:     renderVacancyTab,
  transaction: renderTransactionTab,
};

function showTab(name) {
  document.querySelectorAll(".tab-btn").forEach((b, i) => {
    const tabs = ["info", "lease", "vacancy", "transaction"];
    b.classList.toggle("active", tabs[i] === name);
  });
  ["panel-info", "panel-lease", "panel-vacancy", "panel-transaction"].forEach((id) => {
    document.getElementById(id).classList.add("d-none");
  });
  document.getElementById(`panel-${name}`).classList.remove("d-none");
  TAB_RENDERERS[name]();
}

async function renderInfoTab() {
  const center = allCenters.find((c) => c.id === selectedCenterId);
  const el = document.getElementById("panel-info");

  const rows = [
    ["주소",       center.address],
    ["상태",       `<span class="badge-status badge-${center.status}">${center.status}</span>`],
    ["지역",       center.region],
    ["연면적",     center.total_area ? `${center.total_area.toLocaleString()} ㎡ (${(center.total_area / 3.305785).toFixed(0)}평)` : null],
    ["임대가능면적", center.net_leasable_area ? `${center.net_leasable_area.toLocaleString()} ㎡` : null],
    ["지상층수",   center.floors_above ? `${center.floors_above}층` : null],
    ["도크 수",    center.dock_count ? `${center.dock_count}개` : null],
    ["층고",       center.ceiling_height ? `${center.ceiling_height}m` : null],
    ["준공일",     center.completion_date],
    ["개발사",     center.developer],
  ].filter(([, v]) => v);

  el.innerHTML = `<div class="info-section">` +
    rows.map(([label, val]) => `
      <div class="mb-3">
        <div class="info-label">${label}</div>
        <div class="info-value">${val}</div>
      </div>
    `).join("") +
    `</div>`;
}

async function renderLeaseTab() {
  const leases = await api(`/leases?center_id=${selectedCenterId}`);
  const el = document.getElementById("panel-lease");

  if (!leases.length) {
    el.innerHTML = `<div class="p-4 text-center text-muted" style="font-size:.85rem;">임대차 정보가 없습니다.</div>`;
    return;
  }

  el.innerHTML = `<div style="overflow-x:auto;">
    <table class="data-table">
      <thead>
        <tr>
          <th>임차사</th><th>층/호실</th><th>면적</th><th>월임대료</th><th>계약기간</th><th>상태</th>
        </tr>
      </thead>
      <tbody>
        ${leases.map((l) => `
          <tr>
            <td>${l.tenant_id ? "등록됨" : "-"}</td>
            <td>${[l.floor, l.unit_name].filter(Boolean).join("/") || "-"}</td>
            <td>${l.lease_area ? l.lease_area.toLocaleString() + "㎡" : "-"}</td>
            <td>${l.monthly_rent ? (l.monthly_rent / 10000).toLocaleString() + "만원" : "-"}</td>
            <td style="font-size:.72rem;">${l.lease_start || ""} ~ ${l.lease_end || ""}</td>
            <td><span class="badge-status badge-${l.contract_status === "계약중" ? "운영중" : "철거"}">${l.contract_status}</span></td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  </div>`;
}

async function renderVacancyTab() {
  const records = await api(`/vacancy?center_id=${selectedCenterId}`);
  const el = document.getElementById("panel-vacancy");

  if (!records.length) {
    el.innerHTML = `<div class="p-4 text-center text-muted" style="font-size:.85rem;">공실률 데이터가 없습니다.</div>`;
    return;
  }

  // 최근 12개월
  const recent = records.slice(-12);
  const maxRate = Math.max(...recent.map((r) => r.vacancy_rate || 0));

  el.innerHTML = `
    <div class="info-section">
      <div class="mb-2 fw-semibold" style="font-size:.85rem;">공실률 추이 (최근 ${recent.length}개월)</div>
      ${recent.map((r) => {
        const pct = maxRate > 0 ? (r.vacancy_rate / maxRate * 100) : 0;
        return `
          <div class="d-flex align-items-center gap-2 mb-1" style="font-size:.78rem;">
            <span style="width:52px;color:#6b7280;">${r.record_year}-${String(r.record_month).padStart(2,"0")}</span>
            <div style="flex:1;background:#f3f4f6;border-radius:4px;height:10px;">
              <div style="width:${pct}%;background:#2563eb;height:100%;border-radius:4px;"></div>
            </div>
            <span style="width:36px;text-align:right;font-weight:600;">${r.vacancy_rate != null ? r.vacancy_rate.toFixed(1) + "%" : "-"}</span>
          </div>
        `;
      }).join("")}
    </div>
    <div style="overflow-x:auto;">
      <table class="data-table">
        <thead><tr><th>기준월</th><th>전체면적</th><th>공실면적</th><th>공실률</th></tr></thead>
        <tbody>
          ${records.map((r) => `
            <tr>
              <td>${r.record_year}-${String(r.record_month).padStart(2,"0")}</td>
              <td>${r.total_area ? r.total_area.toLocaleString() + "㎡" : "-"}</td>
              <td>${r.vacant_area ? r.vacant_area.toLocaleString() + "㎡" : "-"}</td>
              <td>${r.vacancy_rate != null ? r.vacancy_rate.toFixed(1) + "%" : "-"}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>`;
}

async function renderTransactionTab() {
  const txs = await api(`/transactions?center_id=${selectedCenterId}`);
  const el  = document.getElementById("panel-transaction");

  if (!txs.length) {
    el.innerHTML = `<div class="p-4 text-center text-muted" style="font-size:.85rem;">거래 정보가 없습니다.</div>`;
    return;
  }

  el.innerHTML = `<div style="overflow-x:auto;">
    <table class="data-table">
      <thead><tr><th>거래일</th><th>유형</th><th>금액</th><th>단가</th><th>Cap Rate</th><th>매수인</th></tr></thead>
      <tbody>
        ${txs.map((t) => `
          <tr>
            <td>${t.deal_date || "-"}</td>
            <td>${t.deal_type}</td>
            <td>${t.price ? (t.price / 100000000).toFixed(0) + "억" : "-"}</td>
            <td>${t.price_per_sqm ? t.price_per_sqm.toLocaleString() + "원/㎡" : "-"}</td>
            <td>${t.cap_rate != null ? t.cap_rate.toFixed(2) + "%" : "-"}</td>
            <td>${t.buyer || "-"}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  </div>`;
}

// ── 삭제 ───────────────────────────────────────────────────────────────────────
async function deleteCenter() {
  if (!confirm("정말 삭제하시겠습니까? 관련 임대차·거래 데이터도 모두 삭제됩니다.")) return;
  await api(`/centers/${selectedCenterId}`, { method: "DELETE" });
  closeSidebar();
  await loadCenters();
}

// ── 업로드 패널 ────────────────────────────────────────────────────────────────
function openUpload()  { document.getElementById("upload-panel").classList.add("open"); }
function closeUpload() { document.getElementById("upload-panel").classList.remove("open"); }

// 업로드 타입별 기본 컬럼 매핑 정의
const UPLOAD_CONFIGS = {
  centers: {
    label: "물류센터",
    endpoint: "/upload/centers",
    fields: [
      { key: "col_address",    label: "대지위치",    required: true  },
      { key: "col_name",       label: "센터명",      required: true  },
      { key: "col_region",     label: "지역"                        },
      { key: "col_total_area", label: "연면적(㎡)"                  },
      { key: "col_net_area",   label: "임대가능면적"                },
      { key: "col_floors",     label: "지상층수"                    },
      { key: "col_dock",       label: "도크수"                      },
      { key: "col_ceiling",    label: "층고"                        },
      { key: "col_completion", label: "준공일"                      },
      { key: "col_developer",  label: "개발사"                      },
    ],
    extra: [
      { key: "status", label: "상태", type: "select",
        options: ["운영중","개발중","공급예정","철거"] },
    ],
  },
  tenants: {
    label: "임차사",
    endpoint: "/upload/tenants",
    fields: [
      { key: "col_company",   label: "임차사명",  required: true },
      { key: "col_industry",  label: "업종"                     },
      { key: "col_business",  label: "사업유형"                 },
      { key: "col_contact",   label: "담당자"                   },
      { key: "col_phone",     label: "연락처"                   },
      { key: "col_email",     label: "이메일"                   },
      { key: "col_grade",     label: "신용등급"                 },
    ],
  },
  leases: {
    label: "임대료",
    endpoint: "/upload/leases",
    fields: [
      { key: "col_address",  label: "대지위치",  required: true },
      { key: "col_tenant",   label: "임차사명"                 },
      { key: "col_floor",    label: "층"                       },
      { key: "col_unit",     label: "호실"                     },
      { key: "col_area",     label: "임대면적"                 },
      { key: "col_start",    label: "임대시작일"               },
      { key: "col_end",      label: "임대종료일"               },
      { key: "col_rent",     label: "월임대료"                 },
      { key: "col_rent_sqm", label: "임대료/㎡"               },
      { key: "col_deposit",  label: "보증금"                   },
      { key: "col_status",   label: "계약상태"                 },
    ],
  },
  vacancy: {
    label: "공실률",
    endpoint: "/upload/vacancy",
    fields: [
      { key: "col_address",  label: "대지위치",  required: true },
      { key: "col_year",     label: "연도",      required: true },
      { key: "col_month",    label: "월",        required: true },
      { key: "col_total",    label: "전체면적"                 },
      { key: "col_occupied", label: "임대면적"                 },
      { key: "col_vacant",   label: "공실면적"                 },
      { key: "col_rate",     label: "공실률(%)"               },
    ],
  },
  transactions: {
    label: "거래",
    endpoint: "/upload/transactions",
    fields: [
      { key: "col_address",   label: "대지위치",  required: true },
      { key: "col_date",      label: "거래일"                   },
      { key: "col_type",      label: "거래유형"                 },
      { key: "col_price",     label: "거래금액"                 },
      { key: "col_price_sqm", label: "단가/㎡"                 },
      { key: "col_buyer",     label: "매수인"                   },
      { key: "col_seller",    label: "매도인"                   },
      { key: "col_cap",       label: "Cap Rate"                },
      { key: "col_noi",       label: "NOI"                     },
    ],
  },
};

let uploadedColumns = [];
let uploadedFile    = null;

function renderUploadForm() {
  const type   = document.getElementById("upload-type").value;
  const config = UPLOAD_CONFIGS[type];
  const area   = document.getElementById("upload-form-area");
  uploadedFile    = null;
  uploadedColumns = [];

  area.innerHTML = `
    <!-- 드롭존 -->
    <div class="dropzone" id="dropzone" onclick="document.getElementById('file-input').click()">
      <div class="icon">📂</div>
      <p><strong>엑셀 파일을 드래그하거나 클릭하세요</strong></p>
      <p>.xlsx / .xls 형식</p>
    </div>
    <input type="file" id="file-input" accept=".xlsx,.xls" class="d-none" onchange="onFileSelected(event)" />

    <!-- 컬럼 매핑 (파일 선택 후 표시) -->
    <div id="mapping-area" class="d-none mt-3">
      <div class="fw-semibold mb-2" style="font-size:.85rem;">컬럼 매핑</div>
      <table class="mapping-table">
        <thead><tr><th>시스템 필드</th><th>내 엑셀 컬럼</th></tr></thead>
        <tbody id="mapping-tbody"></tbody>
      </table>
      ${config.extra ? config.extra.map((e) => `
        <div class="mt-2">
          <label class="form-label" style="font-size:.82rem;">${e.label}</label>
          <select name="${e.key}" class="form-select form-select-sm">
            ${e.options.map((o) => `<option value="${o}">${o}</option>`).join("")}
          </select>
        </div>
      `).join("") : ""}
      <button class="btn btn-primary w-100 mt-3" onclick="submitUpload()">업로드 실행</button>
    </div>

    <!-- 결과 -->
    <div id="upload-result" class="upload-result d-none"></div>
  `;

  // 드래그앤드롭
  const dz = document.getElementById("dropzone");
  dz.addEventListener("dragover",  (e) => { e.preventDefault(); dz.classList.add("dragover"); });
  dz.addEventListener("dragleave", ()  => dz.classList.remove("dragover"));
  dz.addEventListener("drop",      (e) => { e.preventDefault(); dz.classList.remove("dragover"); handleFile(e.dataTransfer.files[0]); });
}

async function onFileSelected(e) { handleFile(e.target.files[0]); }

async function handleFile(file) {
  if (!file) return;
  uploadedFile = file;

  // 엑셀 헤더 읽기 (서버로 보내 파싱)
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res = await fetch("/api/upload/preview-columns", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    });
    if (res.ok) {
      uploadedColumns = await res.json();
    }
  } catch {
    // 미리보기 실패 시 빈 배열로 진행
    uploadedColumns = [];
  }

  renderMappingTable();
}

function renderMappingTable() {
  const type   = document.getElementById("upload-type").value;
  const config = UPLOAD_CONFIGS[type];
  const tbody  = document.getElementById("mapping-tbody");

  const colOptions = ["(매핑 안 함)", ...uploadedColumns]
    .map((c) => `<option value="${c}">${c}</option>`)
    .join("");

  tbody.innerHTML = config.fields.map((f) => {
    const matched = uploadedColumns.find((c) => c.trim() === f.label) || "";
    const opts = uploadedColumns.map((c) =>
      `<option value="${c}" ${c === matched ? "selected" : ""}>${c}</option>`
    ).join("");
    return `
      <tr>
        <td>${f.label}${f.required ? ' <span style="color:red">*</span>' : ""}</td>
        <td>
          <select name="${f.key}">
            <option value="">(매핑 안 함)</option>
            ${opts}
          </select>
        </td>
      </tr>
    `;
  }).join("");

  document.getElementById("mapping-area").classList.remove("d-none");
  document.getElementById("dropzone").querySelector("p").textContent = `✅ ${uploadedFile.name}`;
}

async function submitUpload() {
  if (!uploadedFile) return;
  const type   = document.getElementById("upload-type").value;
  const config = UPLOAD_CONFIGS[type];
  const fd     = new FormData();
  fd.append("file", uploadedFile);

  // 매핑 값 수집
  const tbody = document.getElementById("mapping-tbody");
  tbody.querySelectorAll("select").forEach((sel) => {
    if (sel.name && sel.value) fd.append(sel.name, sel.value);
  });

  // extra 필드 (status 등)
  document.querySelectorAll("#mapping-area select[name]").forEach((sel) => {
    if (sel.closest("#mapping-tbody")) return;
    fd.append(sel.name, sel.value);
  });

  const resultEl = document.getElementById("upload-result");
  resultEl.innerHTML = `<div class="text-muted">업로드 중...</div>`;
  resultEl.classList.remove("d-none");

  try {
    const data = await api(config.endpoint, { method: "POST", body: fd });
    resultEl.innerHTML = `
      <div class="success fw-semibold">✅ 성공: ${data.success}건</div>
      ${data.failed ? `<div class="failed">❌ 실패: ${data.failed}건</div>` : ""}
      ${data.errors.length ? `<div class="error-list">${data.errors.join("<br>")}</div>` : ""}
    `;
    if (data.success > 0) await loadCenters();
  } catch (e) {
    resultEl.innerHTML = `<div class="failed">오류: ${e.detail || JSON.stringify(e)}</div>`;
  }
}
