// Chart.js Configuration for reports and dashboard analytics
document.addEventListener('DOMContentLoaded', () => {
    const trendChartCtx = document.getElementById('trendChart');
    const deptChartCtx = document.getElementById('deptChart');

    if (!trendChartCtx || !deptChartCtx) return; // Only run on reports/analytics page

    // Fetch theme configuration from document
    const isDarkMode = () => document.documentElement.getAttribute('data-theme') === 'dark';

    // Chart.js default font settings
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.color = isDarkMode() ? '#94a3b8' : '#64748b';

    let trendChart = null;
    let deptChart = null;

    function renderCharts(data) {
        // Colors configured based on current theme
        const primaryColor = isDarkMode() ? '#818cf8' : '#6366f1';
        const accentColor = isDarkMode() ? '#22d3ee' : '#06b6d4';
        const gridColor = isDarkMode() ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';
        
        const deptColors = [
            '#6366f1', // Indigo
            '#06b6d4', // Cyan
            '#10b981', // Emerald Green
            '#f59e0b', // Amber
            '#ef4444', // Rose Red
            '#8b5cf6', // Violet
        ];

        // 1. Line Chart: 7-Day Attendance Trend
        trendChart = new Chart(trendChartCtx, {
            type: 'line',
            data: {
                labels: data.trend.labels,
                datasets: [{
                    label: 'Attendance count',
                    data: data.trend.data,
                    borderColor: primaryColor,
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.3,
                    borderWidth: 3,
                    pointBackgroundColor: primaryColor,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        padding: 12,
                        backgroundColor: isDarkMode() ? '#1e293b' : '#ffffff',
                        titleColor: isDarkMode() ? '#f8fafc' : '#1e293b',
                        bodyColor: isDarkMode() ? '#94a3b8' : '#64748b',
                        borderColor: isDarkMode() ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)',
                        borderWidth: 1,
                        displayColors: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: isDarkMode() ? '#94a3b8' : '#64748b'
                        }
                    },
                    y: {
                        grid: {
                            color: gridColor
                        },
                        ticks: {
                            stepSize: 1,
                            precision: 0,
                            color: isDarkMode() ? '#94a3b8' : '#64748b'
                        }
                    }
                }
            }
        });

        // 2. Doughnut Chart: Department-wise present today
        deptChart = new Chart(deptChartCtx, {
            type: 'doughnut',
            data: {
                labels: data.departments.labels,
                datasets: [{
                    data: data.departments.data,
                    backgroundColor: deptColors.slice(0, data.departments.labels.length),
                    borderWidth: isDarkMode() ? 2 : 1,
                    borderColor: isDarkMode() ? '#1e293b' : '#ffffff',
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            color: isDarkMode() ? '#94a3b8' : '#64748b',
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        padding: 12,
                        backgroundColor: isDarkMode() ? '#1e293b' : '#ffffff',
                        titleColor: isDarkMode() ? '#f8fafc' : '#1e293b',
                        bodyColor: isDarkMode() ? '#94a3b8' : '#64748b',
                        borderColor: isDarkMode() ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)',
                        borderWidth: 1
                    }
                },
                cutout: '70%'
            }
        });
    }

    // Load Data from API
    fetch('/reports/api/analytics')
        .then(response => response.json())
        .then(data => {
            renderCharts(data);
        })
        .catch(err => {
            console.error("Failed to load analytics data: ", err);
        });

    // Handle theme toggle update without reloading the page
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === "attributes" && mutation.attributeName === "data-theme") {
                if (trendChart && deptChart) {
                    // Re-color fonts and lines based on theme
                    const labelColor = isDarkMode() ? '#94a3b8' : '#64748b';
                    const gridColor = isDarkMode() ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';
                    const primaryColor = isDarkMode() ? '#818cf8' : '#6366f1';
                    
                    // Update Trend Chart
                    trendChart.options.scales.x.ticks.color = labelColor;
                    trendChart.options.scales.y.ticks.color = labelColor;
                    trendChart.options.scales.y.grid.color = gridColor;
                    trendChart.data.datasets[0].borderColor = primaryColor;
                    trendChart.data.datasets[0].pointBackgroundColor = primaryColor;
                    trendChart.options.plugins.tooltip.backgroundColor = isDarkMode() ? '#1e293b' : '#ffffff';
                    trendChart.options.plugins.tooltip.titleColor = isDarkMode() ? '#f8fafc' : '#1e293b';
                    trendChart.options.plugins.tooltip.bodyColor = isDarkMode() ? '#94a3b8' : '#64748b';
                    trendChart.options.plugins.tooltip.borderColor = isDarkMode() ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)';
                    trendChart.update();

                    // Update Department Chart
                    deptChart.options.plugins.legend.labels.color = labelColor;
                    deptChart.data.datasets[0].borderColor = isDarkMode() ? '#1e293b' : '#ffffff';
                    deptChart.data.datasets[0].borderWidth = isDarkMode() ? 2 : 1;
                    deptChart.options.plugins.tooltip.backgroundColor = isDarkMode() ? '#1e293b' : '#ffffff';
                    deptChart.options.plugins.tooltip.titleColor = isDarkMode() ? '#f8fafc' : '#1e293b';
                    deptChart.options.plugins.tooltip.bodyColor = isDarkMode() ? '#94a3b8' : '#64748b';
                    deptChart.options.plugins.tooltip.borderColor = isDarkMode() ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)';
                    deptChart.update();
                }
            }
        });
    });

    observer.observe(document.documentElement, { attributes: true });
});
