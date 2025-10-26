// Cinema Analytics Dashboard (Unified + Robust)

// ----- Data paths (try several) -----
const DATA_PATHS = [
  "../data/data/cinema_insights.json", // main
  "../data/cinema_insights.json", // fallback
  "data/data/cinema_insights.json", // root
  "data/cinema_insights.json", // root
  "cinema_insights.json", // same dir
  "./cinema_insights.json", // same dir
];

// ----- Colors -----
const CHART_COLORS = {
  primary: "#8B5CF6",
  secondary: "#EC4899",
  accent: "#10B981",
  gradient: [
    "#8B5CF6",
    "#9333EA",
    "#A855F7",
    "#B794F4",
    "#C4B5FD",
    "#DDD6FE",
    "#EC4899",
    "#F472B6",
  ],
};

function numFormat(n) {
  if (n == null) return "0";
  const x = Number(n);
  return isFinite(x) ? x.toLocaleString() : "0";
}
function animateCount(el, end, dur = 900) {
  const start = 0,
    diff = end - start,
    startTs = performance.now();
  function tick(t) {
    const p = Math.min(1, (t - startTs) / dur);
    el.textContent = Math.round(start + diff * p).toLocaleString();
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
function initials(name = "") {
  const parts = name.split(/\s+/).filter(Boolean);
  const i1 = parts[0]?.[0] || "";
  const i2 = parts[parts.length - 1]?.[0] || "";
  return (i1 + i2).toUpperCase();
}

const charts = {};

// ----- Tabs -----
document.addEventListener("click", e => {
  const btn = e.target.closest(".tab-btn");
  if (!btn) return;
  const tabId = btn.dataset.tab;
  document
    .querySelectorAll(".tab-btn")
    .forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  document
    .querySelectorAll(".tab-content")
    .forEach(c => c.classList.remove("active"));
  document.getElementById(tabId)?.classList.add("active");
});

// ----- Fetch with fallbacks -----
async function loadData() {
  for (const path of DATA_PATHS) {
    try {
      const res = await fetch(path, { cache: "no-cache" });
      if (res.ok) {
        console.log(`✅ Loaded data from: ${path}`);
        return await res.json();
      }
    } catch (err) {
      console.log(`⚠️ Failed to load from: ${path}`);
    }
  }
  throw new Error("Could not load cinema_insights.json from any path");
}

// ----- Bootstrap -----
document.addEventListener("DOMContentLoaded", initDashboard);

async function initDashboard() {
  try {
    const data = await loadData();
    console.log("📊 Cinema data:", data);

    // Show content
    document.getElementById("loading").style.display = "none";
    document.getElementById("content").style.display = "block";

    // Render sections
    renderStats(data);
    createGenreChart(data.genres || {});
    createDecadeChart(data.decades || {});
    renderDirectors(data.directors || {});
    renderRuntimeChart(data.graph_data?.runtime_histogram);

    if (data.ml_insights) renderMLInsights(data.ml_insights);
    if (data.actors) renderActors(data.actors);
  } catch (error) {
    console.error("❌ Error:", error);
    showError(error.message);
  }
}

// ----- UI helpers -----
function showError(message) {
  document.getElementById("loading").style.display = "none";
  document.getElementById("error").innerHTML = `
    <div class="error-message">
      <i class="fas fa-exclamation-triangle"></i>
      <h2>Oops! Something went wrong</h2>
      <p>${message}</p>
      <p>Tried these paths:</p>
      <ul>${DATA_PATHS.map(p => `<li><code>${p}</code></li>`).join("")}</ul>
      <p><strong>Tip:</strong> (re)generate with <code>python scripts/analyze_data.py --output data/data/cinema_insights.json</code></p>
    </div>`;
  document.getElementById("error").style.display = "block";
}

// ----- Renderers -----
function renderStats(data) {
  const s = data.basic_stats || {};
  const total = s.total_movies ?? 0;
  const hours = s.total_runtime_hours ?? 0;
  const span = (s.year_range && s.year_range.span) || 0;

  const genresBlock = data.genres || {};
  const totalGenres =
    genresBlock.total_unique_genres ??
    (genresBlock.top_10_genres &&
      Object.keys(genresBlock.top_10_genres).length) ??
    (genresBlock.genre_distribution &&
      Object.keys(genresBlock.genre_distribution).length) ??
    (genresBlock.distribution &&
      Object.keys(genresBlock.distribution).length) ??
    0;

  const html = `
    <div class="kpi">
      <div class="kpi-icon"><i class="fas fa-film"></i></div>
      <div class="kpi-label">Total Movies</div>
      <div class="kpi-value" id="kpi-total">0</div>
    </div>
    <div class="kpi">
      <div class="kpi-icon"><i class="fas fa-clock"></i></div>
      <div class="kpi-label">Hours Watched</div>
      <div class="kpi-value" id="kpi-hours">0</div>
    </div>
    <div class="kpi">
      <div class="kpi-icon"><i class="fas fa-calendar"></i></div>
      <div class="kpi-label">Year Span</div>
      <div class="kpi-value">${span ? numFormat(span) : "N/A"}</div>
    </div>
    <div class="kpi">
      <div class="kpi-icon"><i class="fas fa-theater-masks"></i></div>
      <div class="kpi-label">Genres</div>
      <div class="kpi-value">${numFormat(totalGenres)}</div>
    </div>
  `;
  const box = document.getElementById("stats-container");
  box.innerHTML = html;

  // animated counters
  animateCount(document.getElementById("kpi-total"), Number(total) || 0);
  animateCount(
    document.getElementById("kpi-hours"),
    Math.round(Number(hours) || 0)
  );
}

function createGenreChart(genreData) {
  const ctx = document.getElementById("genreChart")?.getContext("2d");
  if (!ctx) return;

  // Accept several shapes
  const top10 = cloneObj(
    genreData.top_10_genres ||
      pickTop(genreData.genre_distribution) ||
      pickTop(genreData.distribution) ||
      {}
  );

  const labels = Object.keys(top10);
  const values = Object.values(top10);

  if (!labels.length) return;

  charts.genre?.destroy?.();
  charts.genre = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Number of Movies",
          data: values,
          backgroundColor: CHART_COLORS.gradient.slice(0, labels.length),
          borderColor: CHART_COLORS.primary,
          borderWidth: 1.5,
          borderRadius: 8,
        },
      ],
    },
    options: chartAxesOptions(),
  });
}
const chips = labels
  .slice(0, 6)
  .map(
    (g, i) => `
  <div class="genre-chip">
    <span class="name">${g}</span>
    <span class="count">${values[i]} movies</span>
    <span class="bar" style="width:${(values[i] / values[0]) * 100}%"></span>
  </div>
`
  )
  .join("");
document.getElementById("genre-stats").innerHTML = chips;

function createDecadeChart(decades) {
  const ctx = document.getElementById("decadeChart")?.getContext("2d");
  if (!ctx || !decades) return;

  // Accept { "1990": {count:12} } or { "1990": 12 }
  const entries = Object.entries(decades)
    .map(([k, v]) => [Number(k), (v && v.count) ?? v])
    .filter(([, v]) => isFinite(v));
  entries.sort((a, b) => a[0] - b[0]);

  if (!entries.length) return;

  const labels = entries.map(([d]) => `${d}s`);
  const values = entries.map(([, c]) => c);

  charts.decade?.destroy?.();
  charts.decade = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Movies Watched",
          data: values,
          borderColor: CHART_COLORS.secondary,
          backgroundColor: "rgba(236, 72, 153, 0.1)",
          tension: 0.4,
          fill: true,
        },
      ],
    },
    options: chartAxesOptions({ legend: false }),
  });
}

function renderDirectors(directorsData = {}) {
  const container = document.getElementById("directors-container");
  if (!container) return;

  let rows = Object.entries(directorsData).map(([name, v]) => {
    if (typeof v === "number") return { name, movie_count: v };
    return {
      name,
      movie_count: v.movie_count ?? 0,
      total_runtime_hours: v.total_runtime_hours,
    };
  });
  rows = rows.filter(d => d.name && d.movie_count > 0);
  rows.sort((a, b) => (b.movie_count || 0) - (a.movie_count || 0));
  rows = rows.slice(0, 12);

  if (!rows.length) {
    container.innerHTML = `<p class="loading">No director data available.</p>`;
    return;
  }

  container.innerHTML = `
    <div class="directors-grid">
      ${rows
        .map(
          d => `
        <div class="person-card">
          <div class="person-avatar">${initials(d.name)}</div>
          <div class="person-meta">
            <h3>${d.name}</h3>
            <p><i class="fas fa-film"></i> ${numFormat(d.movie_count)} movies
              ${
                d.total_runtime_hours
                  ? ` · <i class="fas fa-clock"></i> ${Number(
                      d.total_runtime_hours
                    ).toFixed(1)}h`
                  : ""
              }</p>
          </div>
        </div>
      `
        )
        .join("")}
    </div>
  `;
}

function renderActors(actorsData = {}) {
  const wrap = document.getElementById("actors-container");
  if (!wrap) return;

  let list = [];
  if (Array.isArray(actorsData.top_actors)) {
    list = actorsData.top_actors.map(a => ({
      name: a.name || a[0],
      appearances: a.movie_count ?? a.appearances ?? a[1],
      birth_year: a.birth_year ?? null,
    }));
  } else if (
    actorsData.top_actors &&
    typeof actorsData.top_actors === "object"
  ) {
    list = Object.entries(actorsData.top_actors).map(([name, v]) => ({
      name,
      appearances: v.appearances ?? v.movie_count ?? 0,
      birth_year: v.birth_year ?? null,
    }));
  }

  // hide “Unknown” & zeroes
  list = list.filter(
    a =>
      a &&
      a.name &&
      a.name.toLowerCase() !== "unknown" &&
      (a.appearances || 0) > 0
  );
  if (!list.length) {
    wrap.innerHTML = `
      <section class="panel">
        <h2 class="panel-title"><i class="fas fa-users"></i> Top Actors</h2>
        <p class="loading">No actor data yet. Run <span class="mono">enrich_people.py</span> and regenerate insights.</p>
      </section>`;
    return;
  }

  list.sort((a, b) => (b.appearances || 0) - (a.appearances || 0));
  const top = list.slice(0, 12);

  wrap.innerHTML = `
    <section class="panel">
      <h2 class="panel-title"><i class="fas fa-users"></i> Top Actors</h2>
      <div class="actors-grid">
        ${top
          .map(
            a => `
          <div class="person-card">
            <div class="person-avatar">${initials(a.name)}</div>
            <div class="person-meta">
              <h3>${a.name}</h3>
              <p><i class="fas fa-film"></i> ${numFormat(
                a.appearances
              )} in collection
                 ${
                   a.birth_year
                     ? ` · <i class="fas fa-calendar"></i> ${a.birth_year}`
                     : ""
                 }</p>
            </div>
          </div>
        `
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderMLInsights(ml = {}) {
  const container = document.getElementById("ml-insights-container");
  if (!container) return;

  // Python currently produces "taste_clusters"
  const clusters = ml.taste_clusters || ml.genre_clusters || {};
  const entries = Object.entries(clusters);

  container.innerHTML = `
    <div class="chart-container">
      <h2 class="chart-title"><i class="fas fa-brain"></i> ML Insights</h2>
      ${
        entries.length
          ? `<div class="highlights-grid">
            ${entries
              .slice(0, 6)
              .map(
                ([label, info]) => `
              <div class="highlight-card">
                <i class="fas fa-project-diagram"></i>
                <h4>${escapeHTML(label)}</h4>
                <p>${toNumber(info.size)} movies (${toNumber(
                  info.percentage
                )}%)</p>
              </div>`
              )
              .join("")}
          </div>`
          : `<p class="loading-text">Not enough text/keyword data for clustering yet.</p>`
      }
    </div>`;
}

function renderRuntimeChart(hist) {
  const ctx = document.getElementById("runtimeChart")?.getContext("2d");
  if (!ctx || !hist || !hist.bins || !hist.counts) return;

  charts.runtime?.destroy?.();
  charts.runtime = new Chart(ctx, {
    type: "bar",
    data: {
      labels: hist.bins,
      datasets: [
        {
          label: "Number of Movies",
          data: hist.counts,
          backgroundColor: CHART_COLORS.accent,
          borderColor: CHART_COLORS.accent,
          borderWidth: 1.5,
          borderRadius: 8,
        },
      ],
    },
    options: chartAxesOptions({ legend: false }),
  });
}

// ----- Utils -----
function chartAxesOptions({ legend = false } = {}) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: legend },
      tooltip: {
        backgroundColor: "rgba(15, 23, 42, 0.95)",
        titleColor: "#F8FAFC",
        bodyColor: "#CBD5E1",
        borderColor: CHART_COLORS.primary,
        borderWidth: 1,
        padding: 12,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { color: "#94A3B8" },
        grid: { color: "rgba(148,163,184,0.1)" },
      },
      x: {
        ticks: { color: "#94A3B8" },
        grid: { display: false },
      },
    },
  };
}

function pickTop(obj, n = 10) {
  if (!obj || typeof obj !== "object") return null;
  return Object.fromEntries(
    Object.entries(obj)
      .sort((a, b) => b[1] - a[1])
      .slice(0, n)
  );
}
function countKeys(obj) {
  return obj && typeof obj === "object" ? Object.keys(obj).length : 0;
}
function toNumber(v) {
  return v == null || Number.isNaN(+v) ? 0 : Number(v).toLocaleString();
}
function cloneObj(o) {
  return JSON.parse(JSON.stringify(o || {}));
}
function firstDefined(...vals) {
  for (const v of vals) if (v != null) return v;
  return undefined;
}
function escapeHTML(s = "") {
  return s.replace(
    /[&<>"']/g,
    m =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[
        m
      ])
  );
}
