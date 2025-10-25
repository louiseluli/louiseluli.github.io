// Cinema Analytics Dashboard - COMPLETE WITH ACTORS & ML
// Fixed paths and added comprehensive visualizations

// Configuration - TRY MULTIPLE PATHS
const DATA_PATHS = [
  "../data/data/cinema_insights.json", // From pages/cinema.html
  "data/data/cinema_insights.json", // From root
  "../cinema_insights.json", // Fallback
];

const CHART_COLORS = {
  primary: "#8B5CF6",
  secondary: "#EC4899",
  accent: "#10B981",
  warning: "#F59E0B",
  info: "#3B82F6",
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

const charts = {};

// Load data with fallback paths
async function loadData() {
  for (const path of DATA_PATHS) {
    try {
      const response = await fetch(path);
      if (response.ok) {
        console.log(`✅ Loaded data from: ${path}`);
        return await response.json();
      }
    } catch (error) {
      console.log(`⚠️  Failed to load from: ${path}`);
    }
  }
  throw new Error("Could not load cinema_insights.json from any path");
}

// Initialize dashboard
async function initDashboard() {
  try {
    const data = await loadData();
    console.log("📊 Cinema data loaded:", data);

    updateStats(data.basic_stats);
    createGenreChart(data.genres);
    createDecadeChart(data.decades);
    updateDirectors(data.directors);

    // NEW: Actor section
    if (data.actors && data.actors.top_actors) {
      updateActors(data.actors);
    }

    // NEW: ML insights
    if (data.ml_insights) {
      updateMLInsights(data.ml_insights);
    }

    // NEW: Advanced graphs
    if (data.graph_data) {
      createTimelineChart(data.graph_data.timeline);
      createRuntimeHistogram(data.graph_data.runtime_histogram);
    }
  } catch (error) {
    console.error("❌ Error loading dashboard:", error);
    showError(
      "Failed to load cinema analytics data. Please run: python scripts/analyze_data.py"
    );
  }
}

// Update stats
function updateStats(stats) {
  document.getElementById("total-count").textContent =
    stats.total_movies.toLocaleString();
  document.getElementById("stat-total").textContent =
    stats.total_movies.toLocaleString();
  document.getElementById("stat-hours").textContent =
    stats.total_runtime_hours.toLocaleString();

  const yearRange = stats.year_range;
  document.getElementById("stat-span").textContent = yearRange.span || "N/A";
  document.getElementById("stat-days").textContent =
    stats.total_runtime_days.toLocaleString();
}

// Genre Chart
function createGenreChart(genresData) {
  const ctx = document.getElementById("genreChart");
  if (!ctx) return;

  const top10 = genresData.top_10_genres;
  const labels = Object.keys(top10);
  const values = Object.values(top10);

  document.getElementById("stat-genres").textContent =
    genresData.total_unique_genres;

  charts.genre = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Number of Movies",
          data: values,
          backgroundColor: CHART_COLORS.gradient.slice(0, 10),
          borderColor: CHART_COLORS.primary,
          borderWidth: 2,
          borderRadius: 8,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(15, 23, 42, 0.95)",
          titleColor: "#F8FAFC",
          bodyColor: "#CBD5E1",
          borderColor: CHART_COLORS.primary,
          borderWidth: 1,
          padding: 12,
          displayColors: false,
          callbacks: {
            label: function (context) {
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = ((context.parsed.y / total) * 100).toFixed(1);
              return `${context.parsed.y} movies (${percentage}%)`;
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: "rgba(148, 163, 184, 0.1)" },
          ticks: { color: "#94A3B8" },
        },
        x: {
          grid: { display: false },
          ticks: { color: "#94A3B8" },
        },
      },
    },
  });

  const statsHtml = `
    <div class="stats-grid">
      ${labels
        .slice(0, 5)
        .map(
          (genre, i) => `
        <div class="stat-item">
          <span class="stat-genre">${genre}</span>
          <span class="stat-count">${values[i]} movies</span>
          <div class="stat-bar" style="width: ${
            (values[i] / values[0]) * 100
          }%; background: ${CHART_COLORS.gradient[i]}"></div>
        </div>
      `
        )
        .join("")}
    </div>
  `;
  document.getElementById("genre-stats").innerHTML = statsHtml;
}

// Decade Chart
function createDecadeChart(decadesData) {
  const ctx = document.getElementById("decadeChart");
  if (!ctx) return;

  const decades = Object.keys(decadesData).sort();
  const counts = decades.map(d => decadesData[d].count);

  charts.decade = new Chart(ctx, {
    type: "line",
    data: {
      labels: decades.map(d => `${d}s`),
      datasets: [
        {
          label: "Movies Watched",
          data: counts,
          backgroundColor: "rgba(139, 92, 246, 0.2)",
          borderColor: CHART_COLORS.primary,
          borderWidth: 3,
          fill: true,
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          labels: { color: "#CBD5E1", font: { size: 12 } },
        },
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
          title: { display: true, text: "Number of Movies", color: "#94A3B8" },
          grid: { color: "rgba(148, 163, 184, 0.1)" },
          ticks: { color: "#94A3B8" },
        },
        x: {
          grid: { color: "rgba(148, 163, 184, 0.1)" },
          ticks: { color: "#94A3B8" },
        },
      },
    },
  });

  const mostActive = decades.reduce((max, d) =>
    decadesData[d].count > decadesData[max].count ? d : max
  );

  const highlightsHtml = `
    <div class="highlights-grid">
      <div class="highlight-card">
        <i class="fas fa-fire"></i>
        <h4>Most Active Decade</h4>
        <p><strong>${mostActive}s</strong> with ${decadesData[mostActive].count} movies</p>
      </div>
      <div class="highlight-card">
        <i class="fas fa-calendar"></i>
        <h4>Era Coverage</h4>
        <p><strong>${decades.length}</strong> decades represented</p>
      </div>
    </div>
  `;
  document.getElementById("decade-highlights").innerHTML = highlightsHtml;
}

// Directors
function updateDirectors(directorsData) {
  const container = document.getElementById("directors-list");
  if (!container || !directorsData) return;

  const directors = Object.entries(directorsData).slice(0, 12);
  document.getElementById("stat-directors").textContent =
    Object.keys(directorsData).length;

  const html = directors
    .map(
      ([name, data], index) => `
    <div class="director-card">
      <div class="director-rank">#${index + 1}</div>
      <div class="director-info">
        <h3>${name}</h3>
        <div class="director-stats">
          <span><i class="fas fa-film"></i> ${data.movie_count} movies</span>
          <span><i class="fas fa-clock"></i> ${data.total_runtime_hours.toFixed(
            1
          )}h</span>
        </div>
      </div>
    </div>
  `
    )
    .join("");

  container.innerHTML = html;
}

// NEW: Update Actors
function updateActors(actorsData) {
  const container = document.getElementById("actors-list");
  if (!container) return;

  const actors = Object.entries(actorsData.top_actors || {}).slice(0, 20);

  if (actors.length === 0) {
    container.innerHTML =
      '<p class="loading-text">No actor data available. Run enrich_people.py to generate.</p>';
    return;
  }

  const html = actors
    .map(
      ([name, data], index) => `
    <div class="actor-card">
      <div class="actor-rank">#${index + 1}</div>
      <div class="actor-info">
        <h3>${name}</h3>
        <div class="actor-stats">
          <span><i class="fas fa-film"></i> ${
            data.appearances
          } in collection</span>
          ${
            data.birth_year
              ? `<span><i class="fas fa-calendar"></i> ${data.birth_year}</span>`
              : ""
          }
        </div>
      </div>
    </div>
  `
    )
    .join("");

  container.innerHTML = html;
}

// NEW: ML Insights
function updateMLInsights(mlData) {
  const container = document.getElementById("ml-insights");
  if (!container) return;

  let html = '<h3><i class="fas fa-robot"></i> Machine Learning Insights</h3>';

  // Genre clustering
  if (
    mlData.genre_clustering &&
    Object.keys(mlData.genre_clustering).length > 0
  ) {
    html +=
      '<div class="ml-section"><h4>Genre Clusters</h4><div class="cluster-grid">';
    for (const [cluster, info] of Object.entries(mlData.genre_clustering).slice(
      0,
      6
    )) {
      html += `
        <div class="cluster-card">
          <div class="cluster-name">${cluster}</div>
          <div class="cluster-stat">${info.size} movies (${info.percentage}%)</div>
        </div>
      `;
    }
    html += "</div></div>";
  }

  // Trends
  if (mlData.trends) {
    html += `
      <div class="ml-section">
        <h4>Trends Detected</h4>
        <div class="trend-info">
          <p><strong>Decade Trend:</strong> ${mlData.trends.decade_trend}</p>
          ${
            mlData.trends.peak_decade
              ? `<p><strong>Peak:</strong> ${mlData.trends.peak_decade}s (${mlData.trends.peak_count} movies)</p>`
              : ""
          }
        </div>
      </div>
    `;
  }

  container.innerHTML = html;
}

// NEW: Timeline Chart
function createTimelineChart(timelineData) {
  const ctx = document.getElementById("timelineChart");
  if (!ctx || !timelineData) return;

  charts.timeline = new Chart(ctx, {
    type: "line",
    data: {
      labels: timelineData.years,
      datasets: [
        {
          label: "Movies per Year",
          data: timelineData.counts,
          backgroundColor: "rgba(236, 72, 153, 0.2)",
          borderColor: CHART_COLORS.secondary,
          borderWidth: 2,
          fill: true,
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(15, 23, 42, 0.95)",
          titleColor: "#F8FAFC",
          bodyColor: "#CBD5E1",
          padding: 12,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: "rgba(148, 163, 184, 0.1)" },
          ticks: { color: "#94A3B8" },
        },
        x: {
          grid: { display: false },
          ticks: {
            color: "#94A3B8",
            maxTicksLimit: 20, // Show fewer year labels
          },
        },
      },
    },
  });
}

// NEW: Runtime Histogram
function createRuntimeHistogram(runtimeData) {
  const ctx = document.getElementById("runtimeChart");
  if (!ctx || !runtimeData) return;

  charts.runtime = new Chart(ctx, {
    type: "bar",
    data: {
      labels: runtimeData.bins,
      datasets: [
        {
          label: "Number of Movies",
          data: runtimeData.counts,
          backgroundColor: CHART_COLORS.accent,
          borderColor: CHART_COLORS.accent,
          borderWidth: 2,
          borderRadius: 8,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(15, 23, 42, 0.95)",
          titleColor: "#F8FAFC",
          bodyColor: "#CBD5E1",
          padding: 12,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: "rgba(148, 163, 184, 0.1)" },
          ticks: { color: "#94A3B8" },
        },
        x: {
          grid: { display: false },
          ticks: { color: "#94A3B8" },
        },
      },
    },
  });
}

// Error display
function showError(message) {
  const container = document.querySelector(".dashboard");
  const errorHtml = `
    <div class="error-message">
      <i class="fas fa-exclamation-triangle"></i>
      <h2>Oops! Something went wrong</h2>
      <p>${message}</p>
      <p>Tried these paths:</p>
      <ul>${DATA_PATHS.map(p => `<li><code>${p}</code></li>`).join("")}</ul>
      <p><strong>Solution:</strong> Run <code>python scripts/analyze_data.py</code> from your project root</p>
    </div>
  `;
  container.innerHTML = errorHtml;
}

// Initialize on load
document.addEventListener("DOMContentLoaded", initDashboard);
