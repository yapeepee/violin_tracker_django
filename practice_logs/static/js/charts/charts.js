import { chartColors, commonChartOptions } from './config.js';
import { formatDate, handleError } from '../utils.js';

// 存儲所有圖表實例
const charts = {};

// 載入每週練習數據
async function loadWeeklyData(studentName) {
    try {
        const params = new URLSearchParams(window.location.search);
        params.set('student_name', studentName);
        const response = await fetch(`/api/weekly-practice/?${params}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();

        charts.weeklyChart = new Chart(document.getElementById('weeklyChart'), {
            type: 'line',
            data: {
                labels: data.map(d => formatDate(new Date(d.date))),
                datasets: [{
                    label: '練習時間（分鐘）',
                    data: data.map(d => d.total_minutes),
                    borderColor: chartColors.primary,
                    backgroundColor: `${chartColors.primary}15`,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y'
                }, {
                    label: '評分',
                    data: data.map(d => d.avg_rating),
                    borderColor: chartColors.secondary,
                    backgroundColor: `${chartColors.secondary}15`,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                ...commonChartOptions,
                scales: createDualAxisScales('練習時間', '評分', true)
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
                labels: data.map(d => formatDate(new Date(d.date))),
                datasets: createRecentTrendDatasets(data)
            },
            options: {
                ...commonChartOptions,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: '練習時間（分鐘）'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: '練習曲目數'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    },
                    y2: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: '評分'
                        },
                        min: 1,
                        max: 5,
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
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

        charts.focusChart = new Chart(document.getElementById('focusChart'), {
            type: 'radar',
            data: {
                labels: data.map(d => d.focus_display),
                datasets: [{
                    label: '練習時間分布',
                    data: data.map(d => d.total_minutes),
                    backgroundColor: `${chartColors.primary}40`,
                    borderColor: chartColors.primary,
                    borderWidth: 2
                }]
            },
            options: {
                ...commonChartOptions,
                scales: {
                    r: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(139, 69, 19, 0.1)'
                        }
                    }
                }
            }
        });
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

        // 更新統計數據
        document.getElementById('totalDays').textContent = data.total_days;
        document.getElementById('practiceDays').textContent = data.practice_days;
        document.getElementById('restDays').textContent = data.rest_days;
        document.getElementById('practiceRatio').style.width = `${data.practice_ratio * 100}%`;

        // 創建日曆熱圖
        charts.restDayChart = new Chart(document.getElementById('restDayChart'), {
            type: 'scatter',
            data: {
                datasets: [{
                    label: '練習日',
                    data: data.practice_dates.map(date => ({
                        x: new Date(date),
                        y: 1
                    })),
                    backgroundColor: chartColors.primary
                }, {
                    label: '休息日',
                    data: data.rest_dates.map(date => ({
                        x: new Date(date),
                        y: 0
                    })),
                    backgroundColor: `${chartColors.primary}40`
                }]
            },
            options: {
                ...commonChartOptions,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day'
                        }
                    },
                    y: {
                        display: false
                    }
                }
            }
        });
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
            type: 'line',
            data: {
                labels: data.map(d => formatDate(new Date(d.date))),
                datasets: [{
                    label: '練習曲目數',
                    data: data.map(d => d.pieces_count),
                    borderColor: chartColors.primary,
                    backgroundColor: `${chartColors.primary}15`,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y'
                }, {
                    label: '練習次數',
                    data: data.map(d => d.total_sessions),
                    borderColor: chartColors.secondary,
                    backgroundColor: `${chartColors.secondary}15`,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                ...commonChartOptions,
                scales: createDualAxisScales('曲目數', '練習次數')
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