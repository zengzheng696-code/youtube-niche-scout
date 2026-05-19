const fallbackReport = {
  meta: {
    generated_at: "未生成",
    week_id: "none",
    market: "UK",
    summary: "还没有生成周报。请运行 python scripts/generate_weekly_report.py。",
  },
  source_status: {
    youtube: { status: "missing_report", records: 0 },
  },
  products: [],
};

const report = window.__PET_SCOUT_REPORT__ || fallbackReport;

const cardsEl = document.querySelector("#cards");
const resultTitle = document.querySelector("#resultTitle");
const reportMeta = document.querySelector("#reportMeta");
const weeklySummary = document.querySelector("#weeklySummary");
const sourceStatus = document.querySelector("#sourceStatus");
const searchInput = document.querySelector("#searchInput");
const petFilter = document.querySelector("#petFilter");
const categoryFilter = document.querySelector("#categoryFilter");
const confidenceFilter = document.querySelector("#confidenceFilter");
const riskFilter = document.querySelector("#riskFilter");
const sourceFilter = document.querySelector("#sourceFilter");
const minScore = document.querySelector("#minScore");
const minScoreLabel = document.querySelector("#minScoreLabel");
const sortBy = document.querySelector("#sortBy");
const detailDialog = document.querySelector("#detailDialog");
const detailContent = document.querySelector("#detailContent");
const closeDialog = document.querySelector("#closeDialog");
const exportBtn = document.querySelector("#exportBtn");

function safeText(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => {
    const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
    return map[char];
  });
}

function clampScore(value) {
  const number = Number(value);
  if (Number.isNaN(number)) return 0;
  return Math.max(0, Math.min(100, number));
}

function confidenceLabel(confidence) {
  if (confidence === "high") return { text: "high", className: "good" };
  if (confidence === "medium") return { text: "medium", className: "watch" };
  return { text: confidence || "low", className: "risk" };
}

function hydrateSelect(select, values) {
  const active = select.value;
  select.innerHTML = '<option value="all">全部</option>';
  [...new Set(values.filter(Boolean))].sort().forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.append(option);
  });
  select.value = [...select.options].some((option) => option.value === active) ? active : "all";
}

function hydrateChrome() {
  const meta = report.meta || {};
  reportMeta.textContent = `${meta.market || "UK"} · ${meta.week_id || "unknown week"} · ${meta.generated_at || "not generated"}`;
  weeklySummary.textContent = meta.summary || "暂无摘要。";

  const statuses = report.source_status || {};
  sourceStatus.innerHTML = Object.entries(statuses)
    .map(([source, value]) => {
      const status = value.status || "unknown";
      const records = value.records || 0;
      const note = value.note || "";
      return `
        <article>
          <span>${safeText(source.toUpperCase())}</span>
          <strong>${safeText(status)}</strong>
          <small>${records} records${note ? ` · ${safeText(note)}` : ""}</small>
        </article>
      `;
    })
    .join("");

  hydrateSelect(petFilter, report.products.map((product) => product.pet));
  hydrateSelect(categoryFilter, report.products.map((product) => product.category));
}

function productSources(product) {
  return Object.entries(product.signals || {})
    .filter(([, value]) => value && value.enabled)
    .map(([source]) => source);
}

function getFilteredProducts() {
  const query = searchInput.value.trim().toLowerCase();
  const min = Number(minScore.value);

  return [...(report.products || [])]
    .filter((product) => {
      const sources = productSources(product);
      const haystack = [
        product.name,
        product.pet,
        product.category,
        product.problem,
        product.landing_page_angle,
        ...(product.evidence || []).map((item) => `${item.source} ${item.title} ${item.summary}`),
      ]
        .join(" ")
        .toLowerCase();

      return (
        (!query || haystack.includes(query)) &&
        (petFilter.value === "all" || product.pet === petFilter.value) &&
        (categoryFilter.value === "all" || product.category === categoryFilter.value) &&
        (confidenceFilter.value === "all" || product.confidence === confidenceFilter.value) &&
        (riskFilter.value === "all" || product.risk === riskFilter.value) &&
        (sourceFilter.value === "all" || sources.includes(sourceFilter.value)) &&
        product.score >= min
      );
    })
    .sort((a, b) => {
      if (sortBy.value !== "score") {
        return (b.scores?.[sortBy.value] || 0) - (a.scores?.[sortBy.value] || 0);
      }
      return b.score - a.score;
    });
}

function renderBars(product) {
  const rows = [
    ["搜索覆盖", product.scores?.youtube_search || 0],
    ["观看速度", product.scores?.youtube_velocity || 0],
    ["互动强度", product.scores?.youtube_engagement || 0],
    ["评论痛点", product.scores?.youtube_comments || 0],
  ];

  return rows
    .map(
      ([label, value]) => `
        <div class="bar-row">
          <span>${safeText(label)}</span>
          <div class="bar"><span style="width:${clampScore(value)}%"></span></div>
          <b>${clampScore(value)}</b>
        </div>
      `,
    )
    .join("");
}

function renderCards() {
  minScoreLabel.textContent = minScore.value;
  const filtered = getFilteredProducts();
  resultTitle.textContent = `候选品 (${filtered.length})`;

  if (!filtered.length) {
    cardsEl.innerHTML = '<p class="why">当前没有候选品。若数据源未启用，请配置 .env.local 后运行周报脚本；也可以用 --fixture 生成演示报告。</p>';
    return;
  }

  cardsEl.innerHTML = filtered
    .map((product, index) => {
      const confidence = confidenceLabel(product.confidence);
      const scoreClass = confidence.className === "watch" ? "medium-score" : confidence.className === "risk" ? "low-score" : "";
      const sources = productSources(product);

      return `
        <article class="card">
          <div class="card-top">
            <div>
              <h3>${safeText(product.name)}</h3>
              <div class="meta">
                <span class="pill">${safeText(product.pet)}</span>
                <span class="pill">${safeText(product.category)}</span>
                <span class="pill">Risk: ${safeText(product.risk)}</span>
                <span class="pill">Confidence: ${safeText(product.confidence)}</span>
              </div>
            </div>
            <div class="score ${scoreClass}">${product.score}</div>
          </div>
          <p class="why">${safeText(product.problem)}</p>
          <div class="bars">${renderBars(product)}</div>
          <div class="source-list">${sources.map((source) => `<span>${safeText(source)}</span>`).join("") || "no enabled source"}</div>
          <div class="card-actions">
            <button class="ghost-btn" data-detail="${index}">查看证据与打法</button>
          </div>
        </article>
      `;
    })
    .join("");

  document.querySelectorAll("[data-detail]").forEach((button) => {
    button.addEventListener("click", () => openDetail(filtered[Number(button.dataset.detail)]));
  });
}

function listItems(items) {
  return (items || []).map((item) => `<li>${safeText(item)}</li>`).join("");
}

function signalLine(product, source) {
  const signal = product.signals?.[source];
  if (!signal || !signal.enabled) return `<li>${source}: 未启用或无数据</li>`;
  return `<li>${source}: ${safeText(signal.summary)} (${signal.score || 0}/100)</li>`;
}

function evidenceItems(product) {
  return (product.evidence || [])
    .map((item) => {
      const title = safeText(item.title || item.source);
      const summary = safeText(item.summary || "");
      const url = item.url ? `<a href="${safeText(item.url)}" target="_blank">${title}</a>` : title;
      return `<li><b>${safeText(item.source)}</b>: ${url} · ${summary}</li>`;
    })
    .join("");
}

function openDetail(product) {
  detailContent.innerHTML = `
    <p class="eyebrow">${safeText(product.pet)} · ${safeText(product.category)}</p>
    <h2>${safeText(product.name)}</h2>
    <p class="why">${safeText(product.problem)}</p>
    <div class="meta">
      <span class="pill">Score: ${product.score}</span>
      <span class="pill">Confidence: ${safeText(product.confidence)}</span>
      <span class="pill">Risk: ${safeText(product.risk)}</span>
      <span class="pill">Price: ${safeText(product.suggested_price || "TBD")}</span>
      <span class="pill">Supply: ${safeText(product.supply_price || "TBD")} / MOQ ${safeText(product.moq || "TBD")}</span>
    </div>
    <div class="detail-grid">
      <section class="detail-box">
        <h3>平台信号</h3>
        <ul>
          ${signalLine(product, "youtube_search")}
          ${signalLine(product, "youtube_velocity")}
          ${signalLine(product, "youtube_engagement")}
          ${signalLine(product, "youtube_comments")}
          ${signalLine(product, "creator_diversity")}
        </ul>
      </section>
      <section class="detail-box">
        <h3>证据</h3>
        <ul>${evidenceItems(product) || "<li>暂无证据链接</li>"}</ul>
      </section>
      <section class="detail-box">
        <h3>7 天测试打法</h3>
        <ul>${listItems(product.test_plan)}</ul>
      </section>
      <section class="detail-box">
        <h3>风险与素材角度</h3>
        <ul>
          ${listItems(product.risks)}
          ${listItems(product.creative_angles)}
        </ul>
      </section>
    </div>
  `;
  detailDialog.showModal();
}

function exportCsv() {
  const header = ["rank", "name", "pet", "category", "score", "confidence", "risk", "suggested_price", "supply_price", "moq", "problem"];
  const rows = (report.products || []).map((product, index) =>
    header
      .map((key) => {
        const value = key === "rank" ? index + 1 : product[key];
        return `"${String(value ?? "").replaceAll('"', '""')}"`;
      })
      .join(","),
  );

  const blob = new Blob([[header.join(","), ...rows].join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `uk-pet-scout-${report.meta?.week_id || "latest"}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

[searchInput, petFilter, categoryFilter, confidenceFilter, riskFilter, sourceFilter, minScore, sortBy].forEach((element) => {
  element.addEventListener("input", renderCards);
});

closeDialog.addEventListener("click", () => detailDialog.close());
exportBtn.addEventListener("click", exportCsv);

hydrateChrome();
renderCards();
