/**
 * charts.js - Shared chart helpers and workload chart renderer.
 * Used by the dashboard page.
 */

/**
 * Render a horizontal bar chart of employee workload data.
 * @param {Array} data - [{name, shift_count, role}, ...]
 * @param {string} canvasId - target canvas element id
 * @returns {Chart}
 */
function createWorkloadBarChart(data, canvasId = 'workloadChart') {
  const ctx = document.getElementById(canvasId)?.getContext('2d');
  if (!ctx) return null;
  const palette = [
    '#3b82f6','#10b981','#f59e0b','#8b5cf6','#ef4444',
    '#06b6d4','#84cc16','#f97316','#ec4899','#14b8a6',
  ];
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.name.split(' ').slice(-1)[0]),
      datasets: [{
        label: 'Shifts',
        data: data.map(d => d.shift_count),
        backgroundColor: data.map((_, i) => palette[i % palette.length]),
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: items => data[items[0].dataIndex]?.name || items[0].label,
            label: item => ` ${item.raw} shifts`,
          },
        },
      },
      scales: {
        x: { beginAtZero: true, ticks: { stepSize: 1 } },
        y: { ticks: { font: { size: 11 } } },
      },
    },
  });
}

/**
 * Render a doughnut chart of shift type distribution.
 * @param {Object} counts - {shift_key: count}
 * @param {Array} shifts - shift definition objects
 * @param {string} canvasId
 * @returns {Chart}
 */
function createShiftDoughnut(counts, shifts, canvasId = 'shiftDistChart') {
  const ctx = document.getElementById(canvasId)?.getContext('2d');
  if (!ctx) return null;
  const shiftMap = {};
  shifts.forEach(s => (shiftMap[s.shift_key] = s));
  const keys = Object.keys(counts);
  if (!keys.length) return null;
  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: keys.map(k => shiftMap[k]?.name || k),
      datasets: [{
        data: keys.map(k => counts[k]),
        backgroundColor: keys.map(k => shiftMap[k]?.color_hex || '#3b82f6'),
        borderWidth: 2,
        borderColor: '#fff',
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { font: { size: 11 }, padding: 12 } },
      },
      cutout: '60%',
    },
  });
}

/**
 * Render a line chart showing schedules per day.
 * @param {Array} schedules - schedule rows with date field
 * @param {string} canvasId
 */
function createScheduleTimelineChart(schedules, canvasId = 'timelineChart') {
  const ctx = document.getElementById(canvasId)?.getContext('2d');
  if (!ctx) return null;
  const counts = {};
  schedules.forEach(s => { counts[s.date] = (counts[s.date] || 0) + 1; });
  const sortedDates = Object.keys(counts).sort();
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: sortedDates.map(d => formatDate(d)),
      datasets: [{
        label: 'Assignments',
        data: sortedDates.map(d => counts[d]),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59,130,246,0.08)',
        fill: true,
        tension: 0.4,
        pointRadius: 3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
    },
  });
}
