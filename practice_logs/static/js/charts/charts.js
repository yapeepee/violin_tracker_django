import { chartColors, commonChartOptions } from './config.js';
import { formatDate, handleError } from '../utils.js';

// 存儲所有圖表實例
export const charts = {};

// 載入每週練習數據
export async function loadWeeklyData(studentName) {
    try {
        const params = new URLSearchParams(window.location.search);
        params.set('student_name', studentName);
        const response = await fetch(`/api/weekly-practice/?${params}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();

        charts.weeklyChart = new Chart(document.getElementById('weeklyChart'), {
            type: 'line',
            data: {
                labels: data.map(d => formatDate(d.date)),
                datasets: [{
                    label: '練習時間（分鐘）',
                    data: data.map(d => d.total_minutes),
                    borderColor: chartColors.primary,
                    backgroundColor: `${chartColors.primary}15`,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y',
                    borderWidth: 2
                }, {
                    label: '平均評分',
                    data: data.map(d => d.avg_rating),
                    borderColor: chartColors.secondary,
                    backgroundColor: `${chartColors.secondary}15`,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y1',
                    borderWidth: 2
                }]
            },
            options: {
                ...commonChartOptions,
                scales: createDualAxisScales('分鐘', '評分', true)
            }
        });
    } catch (error) {
        handleError('weeklyChart', error);
    }
}

// 載入樂曲練習數據
export async function loadPieceData(studentName) {
    try {
        const params = new URLSearchParams(window.location.search);
        params.set('student_name', studentName);
        const response = await fetch(`/api/piece-practice/?${params}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();

        charts.pieceChart = new Chart(document.getElementById('pieceChart'), {
            type: 'bar',
            data: {
                labels: data.map(d => d.piece),
                datasets: [{
                    label: '總練習時間（分鐘）',
                    data: data.map(d => d.total_minutes),
                    backgroundColor: `${chartColors.primary}80`,
                    borderColor: chartColors.primary,
                    borderWidth: 2,
                    yAxisID: 'y'
                }, {
                    label: '平均評分',
                    data: data.map(d => d.avg_rating),
                    backgroundColor: `${chartColors.secondary}80`,
                    borderColor: chartColors.secondary,
                    borderWidth: 2,
                    yAxisID: 'y1'
                }]
            },
            options: {
                ...commonChartOptions,
                scales: createDualAxisScales('分鐘', '評分', true)
            }
        });
    } catch (error) {
        handleError('pieceChart', error);
    }
}

// 載入最近練習趨勢
export async function loadRecentTrendData(studentName) {
    try {
        const params = new URLSearchParams(window.location.search);
        params.set('student_name', studentName);
        const response = await fetch(`/api/recent-trend/?${params}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();

        charts.recentTrendChart = new Chart(document.getElementById('recentTrendChart'), {
            type: 'line',
            data: {
                labels: data.map(d => formatDate(d.date)),
                datasets: createRecentTrendDatasets(data)
            },
            options: {
                ...commonChartOptions,
                scales: createTripleAxisScales()
            }
        });
    } catch (error) {
        handleError('recentTrendChart', error);
    }
}

// 載入練習重點分析
export async function loadFocusStats(studentName) {
    try {
        const params = new URLSearchParams(window.location.search);
        params.set('student_name', studentName);
        const response = await fetch(`/api/focus-stats/?${params}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();

        const { normalizedData, maxMinutes, maxSessions } = normalizeData(data);
        createFocusChart(normalizedData, data);
        updateFocusStats(data);
    } catch (error) {
        handleError('focusChart', error);
    }
}

// 載入休息日統計
export async function loadRestDayStats(studentName) {
    try {
        const params = new URLSearchParams(window.location.search);
        params.set('student_name', studentName);
        const response = await fetch(`/api/rest-days/?${params}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();

        updateRestDayStats(data);
        createRestDayChart(data);
    } catch (error) {
        handleError('restDayChart', error);
    }
}

// 載入樂曲切換頻率
export async function loadSwitchingData(studentName) {
    try {
        const params = new URLSearchParams(window.location.search);
        params.set('student_name', studentName);
        const response = await fetch(`/api/piece-switching/?${params}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();

        charts.switchingChart = new Chart(document.getElementById('switchingChart'), {
            type: 'bar',
            data: {
                labels: data.map(d => formatDate(d.date)),
                datasets: createSwitchingDatasets(data)
            },
            options: {
                ...commonChartOptions,
                scales: createTripleAxisScales('曲目數', '練習次數', '評分')
            }
        });
    } catch (error) {
        handleError('switchingChart', error);
    }
}

// 輔助函數
function createDualAxisScales(yLabel, y1Label, hasRating = false) {
    return {
        x: {
            grid: {
                color: 'rgba(139, 69, 19, 0.1)',
                borderColor: chartColors.primary
            }
        },
        y: {
            type: 'linear',
            display: true,
            position: 'left',
            title: {
                display: true,
                text: yLabel,
                color: chartColors.primary,
                font: {
                    family: '"Baskerville", "Times New Roman", serif',
                    size: 14
                }
            },
            grid: {
                color: 'rgba(139, 69, 19, 0.1)',
                borderColor: chartColors.primary
            }
        },
        y1: {
            type: 'linear',
            display: true,
            position: 'right',
            title: {
                display: true,
                text: y1Label,
                color: chartColors.secondary,
                font: {
                    family: '"Baskerville", "Times New Roman", serif',
                    size: 14
                }
            },
            ...(hasRating ? { min: 1, max: 5 } : {}),
            grid: {
                drawOnChartArea: false,
                borderColor: chartColors.secondary
            }
        }
    };
}

function createTripleAxisScales(yLabel = '分鐘', y1Label = '曲目數', y2Label = '評分') {
    const scales = createDualAxisScales(yLabel, y1Label);
    scales.y2 = {
        type: 'linear',
        display: true,
        position: 'right',
        title: {
            display: true,
            text: y2Label,
            color: chartColors.secondary,
            font: {
                family: '"Baskerville", "Times New Roman", serif',
                size: 14
            }
        },
        min: 1,
        max: 5,
        grid: {
            drawOnChartArea: false,
            borderColor: chartColors.secondary
        }
    };
    return scales;
}

function createRecentTrendDatasets(data) {
    return [{
        label: '練習時間（分鐘）',
        data: data.map(d => d.total_minutes),
        borderColor: chartColors.primary,
        backgroundColor: `${chartColors.primary}15`,
        fill: true,
        tension: 0.4,
        yAxisID: 'y',
        borderWidth: 2
    }, {
        label: '練習曲目數',
        data: data.map(d => d.pieces_practiced),
        borderColor: chartColors.success,
        backgroundColor: `${chartColors.success}15`,
        fill: true,
        tension: 0.4,
        yAxisID: 'y1',
        borderWidth: 2
    }, {
        label: '平均評分',
        data: data.map(d => d.avg_rating),
        borderColor: chartColors.secondary,
        backgroundColor: `${chartColors.secondary}15`,
        fill: true,
        tension: 0.4,
        yAxisID: 'y2',
        borderWidth: 2
    }];
}

function createSwitchingDatasets(data) {
    return [{
        label: '練習曲目數',
        data: data.map(d => d.pieces_count),
        backgroundColor: `${chartColors.primary}80`,
        borderColor: chartColors.primary,
        borderWidth: 2,
        yAxisID: 'y'
    }, {
        label: '練習次數',
        data: data.map(d => d.total_sessions),
        backgroundColor: `${chartColors.success}80`,
        borderColor: chartColors.success,
        borderWidth: 2,
        yAxisID: 'y1'
    }, {
        label: '平均評分',
        data: data.map(d => d.avg_rating),
        backgroundColor: `${chartColors.secondary}80`,
        borderColor: chartColors.secondary,
        borderWidth: 2,
        yAxisID: 'y2'
    }];
}

function normalizeData(data) {
    const maxMinutes = Math.max(...data.map(d => d.total_minutes));
    const maxSessions = Math.max(...data.map(d => d.session_count));

    const normalizedData = data.map(d => ({
        ...d,
        normalized_minutes: (d.total_minutes / maxMinutes) * 100,
        normalized_sessions: (d.session_count / maxSessions) * 100
    }));

    return { normalizedData, maxMinutes, maxSessions };
}

function createFocusChart(normalizedData, originalData) {
    charts.focusChart = new Chart(document.getElementById('focusChart'), {
        type: 'radar',
        data: {
            labels: normalizedData.map(d => d.focus_display),
            datasets: [{
                label: '練習時間',
                data: normalizedData.map(d => d.normalized_minutes),
                backgroundColor: `${chartColors.primary}33`,
                borderColor: chartColors.primary,
                pointBackgroundColor: chartColors.primary,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: chartColors.primary,
                borderWidth: 2
            }, {
                label: '練習次數',
                data: normalizedData.map(d => d.normalized_sessions),
                backgroundColor: `${chartColors.secondary}33`,
                borderColor: chartColors.secondary,
                pointBackgroundColor: chartColors.secondary,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: chartColors.secondary,
                borderWidth: 2
            }]
        },
        options: createFocusChartOptions(originalData)
    });
}

function createFocusChartOptions(data) {
    return {
        ...commonChartOptions,
        scales: {
            r: {
                min: 0,
                max: 100,
                beginAtZero: true,
                grid: {
                    color: 'rgba(139, 69, 19, 0.1)',
                    lineWidth: 1
                },
                angleLines: {
                    color: 'rgba(139, 69, 19, 0.1)',
                    lineWidth: 1
                },
                pointLabels: {
                    font: {
                        family: '"Baskerville", "Times New Roman", serif',
                        size: 14,
                        weight: 'bold'
                    },
                    color: chartColors.dark
                },
                ticks: {
                    display: false
                }
            }
        },
        plugins: {
            ...commonChartOptions.plugins,
            tooltip: {
                callbacks: {
                    label: function (context) {
                        const label = context.dataset.label || '';
                        const focusData = data[context.dataIndex];
                        if (label === '練習時間') {
                            return [
                                `${label}: ${focusData.total_minutes}分鐘`,
                                `平均評分: ${focusData.avg_rating.toFixed(1)}`
                            ];
                        }
                        return `${label}: ${focusData.session_count}次`;
                    }
                }
            }
        }
    };
}

function updateFocusStats(data) {
    const statsContainer = document.createElement('div');
    statsContainer.className = 'mt-4';
    statsContainer.innerHTML = `
        <div class="row text-center">
            <div class="col-4">
                <small class="d-block text-muted" style="font-family: var(--font-serif);">總練習時間</small>
                <strong style="color: var(--primary-color); font-family: var(--font-serif);">${data.reduce((sum, d) => sum + d.total_minutes, 0)}分鐘</strong>
            </div>
            <div class="col-4">
                <small class="d-block text-muted" style="font-family: var(--font-serif);">總練習次數</small>
                <strong style="color: var(--primary-color); font-family: var(--font-serif);">${data.reduce((sum, d) => sum + d.session_count, 0)}次</strong>
            </div>
            <div class="col-4">
                <small class="d-block text-muted" style="font-family: var(--font-serif);">平均評分</small>
                <strong style="color: var(--primary-color); font-family: var(--font-serif);">${(data.reduce((sum, d) => sum + (d.avg_rating || 0), 0) / data.length).toFixed(1)}</strong>
            </div>
        </div>
    `;

    const chartContainer = document.getElementById('focusChart').parentElement;
    const existingStats = chartContainer.querySelector('.mt-4');
    if (existingStats) {
        existingStats.remove();
    }
    chartContainer.appendChild(statsContainer);
}

function updateRestDayStats(data) {
    document.getElementById('totalDays').textContent = data.total_days;
    document.getElementById('practiceDays').textContent = data.practice_days;
    document.getElementById('restDays').textContent = data.rest_days;

    const ratio = data.practice_ratio * 100;
    const progressBar = document.getElementById('practiceRatio');
    progressBar.style.width = `${ratio}%`;
    progressBar.setAttribute('aria-valuenow', ratio);
    progressBar.textContent = `${ratio.toFixed(1)}%`;
}

function createRestDayChart(data) {
    const centerText = {
        id: 'centerText',
        afterDraw(chart, args, options) {
            const { ctx, chartArea: { left, top, right, bottom, width, height } } = chart;
            ctx.save();

            const ratio = data.practice_ratio * 100;

            // 練習比例文字
            ctx.font = `bold 24px "Baskerville", "Times New Roman", serif`;
            ctx.fillStyle = chartColors.primary;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(
                `${ratio.toFixed(1)}%`,
                width / 2 + left,
                height / 2 + top
            );

            // "練習率" 文字
            ctx.font = `14px "Baskerville", "Times New Roman", serif`;
            ctx.fillStyle = chartColors.dark;
            ctx.fillText(
                '練習率',
                width / 2 + left,
                height / 2 + top + 25
            );

            ctx.restore();
        }
    };

    charts.restDayChart = new Chart(document.getElementById('restDayChart'), {
        type: 'doughnut',
        data: {
            labels: ['練習天數', '休息天數'],
            datasets: [{
                data: [data.practice_days, data.rest_days],
                backgroundColor: [
                    `${chartColors.primary}CC`,
                    `${chartColors.secondary}CC`
                ],
                borderColor: [
                    chartColors.primary,
                    chartColors.secondary
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: {
                            family: '"Baskerville", "Times New Roman", serif',
                            size: 14
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const value = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${context.label}: ${value}天 (${percentage}%)`;
                        }
                    }
                },
                centerText: {}
            }
        },
        plugins: [centerText]
    });
} 