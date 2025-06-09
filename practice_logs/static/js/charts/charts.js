import { chartColors, commonChartOptions } from './config.js';
import { formatDate, handleError } from '../utils.js';

// 存儲所有圖表實例
const charts = {};

// 顯示載入狀態
function showLoading(chartId) {
    const canvas = document.getElementById(chartId);
    if (!canvas) return;
    
    canvas.style.opacity = '0.5';
    const container = canvas.parentElement;
    
    // 創建或更新載入指示器
    let loader = container.querySelector('.chart-loader');
    if (!loader) {
        loader = document.createElement('div');
        loader.className = 'chart-loader';
        loader.innerHTML = '載入中...';
        loader.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255, 255, 255, 0.9);
            padding: 10px 20px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            z-index: 1000;
        `;
        container.style.position = 'relative';
        container.appendChild(loader);
    }
    loader.style.display = 'block';
}

// 隱藏載入狀態
function hideLoading(chartId) {
    const canvas = document.getElementById(chartId);
    if (!canvas) return;
    
    canvas.style.opacity = '1';
    const loader = canvas.parentElement.querySelector('.chart-loader');
    if (loader) {
        loader.style.display = 'none';
    }
}

// 通用的圖表載入錯誤處理
async function loadChartData(chartId, fetchFn, createChartFn) {
    showLoading(chartId);
    try {
        const data = await fetchFn();
        if (!data || (Array.isArray(data) && data.length === 0)) {
            throw new Error('無數據');
        }
        await createChartFn(data);
        hideLoading(chartId);
    } catch (error) {
        hideLoading(chartId);
        handleError(chartId, error);
        
        // 顯示友好的錯誤訊息
        const canvas = document.getElementById(chartId);
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#666';
            ctx.textAlign = 'center';
            ctx.font = '14px Arial';
            ctx.fillText(error.message === '無數據' ? '暫無數據' : '載入失敗，請稍後重試', canvas.width / 2, canvas.height / 2);
        }
    }
}

// 載入每週練習數據
export async function loadWeeklyData(studentName) {
    const chartId = 'weeklyChart';
    
    const fetchData = async () => {
        const params = new URLSearchParams(window.location.search);
        params.set('student_name', studentName);
        const response = await fetch(`/api/weekly-practice/?${params}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    };

    const createChart = async (data) => {
        if (charts.weeklyChart) {
            charts.weeklyChart.destroy();
        }

        const studentInfoElement = document.getElementById('studentInfo');
        if (studentInfoElement && studentName) {
            studentInfoElement.textContent = `學生：${studentName}`;
        }

        // 計算每天的練習次數
        const practiceCountByDate = {};
        data.forEach(d => {
            const date = formatDate(new Date(d.date));
            practiceCountByDate[date] = (practiceCountByDate[date] || 0) + 1;
        });

        charts.weeklyChart = new Chart(document.getElementById('weeklyChart'), {
            type: 'line',
            data: {
                labels: data.map(d => formatDate(new Date(d.date))),
                datasets: [{
                    label: '練習時間（分鐘）',
                    data: data.map(d => d.total_minutes),
                    borderColor: chartColors.primary,
                    backgroundColor: `${chartColors.primary}30`,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y',
                    borderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }, {
                    label: '練習次數',
                    data: data.map(d => practiceCountByDate[formatDate(new Date(d.date))]),
                    borderColor: chartColors.secondary,
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    tension: 0.4,
                    yAxisID: 'y1',
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                ...commonChartOptions,
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: '練習時間（分鐘）',
                            color: chartColors.primary,
                            font: {
                                size: 13,
                                weight: 'bold'
                            }
                        },
                        grid: {
                            color: `${chartColors.primary}15`
                        },
                        ticks: {
                            color: chartColors.primary
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: '練習次數',
                            color: chartColors.secondary,
                            font: {
                                size: 13,
                                weight: 'bold'
                            }
                        },
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: chartColors.secondary,
                            stepSize: 1
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                },
                plugins: {
                    ...commonChartOptions.plugins,
                    tooltip: {
                        ...commonChartOptions.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += context.parsed.y;
                                }
                                return label;
                            }
                        }
                    }
                }
            }
        });
    };

    await loadChartData(chartId, fetchData, createChart);
}

// 載入樂曲練習數據
export async function loadPieceData(studentName) {
    const chartId = 'pieceChart';
    
    const fetchData = async () => {
        const params = new URLSearchParams(window.location.search);
        params.set('student_name', studentName);
        const response = await fetch(`/api/piece-practice/?${params}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    };

    const createChart = async (data) => {
        if (charts.pieceChart) {
            charts.pieceChart.destroy();
        }

        // 按練習時間排序數據
        data.sort((a, b) => b.total_minutes - a.total_minutes);

        // 計算評分的縮放比例（將評分轉換為相對於最大練習時間的比例）
        const maxMinutes = Math.max(...data.map(d => d.total_minutes));
        const scaledRatings = data.map(d => (d.avg_rating / 5) * maxMinutes);

        charts.pieceChart = new Chart(document.getElementById(chartId), {
            type: 'bar',
            data: {
                labels: data.map(d => d.piece),
                datasets: [{
                    label: '練習時間（分鐘）',
                    data: data.map(d => d.total_minutes),
                    backgroundColor: `${chartColors.primary}cc`,
                    borderColor: chartColors.primary,
                    borderWidth: 1,
                    borderRadius: 4,
                    barThickness: 16,
                    minBarLength: 10
                }, {
                    label: '評分（相對比例）',
                    data: scaledRatings,
                    backgroundColor: `${chartColors.secondary}cc`,
                    borderColor: chartColors.secondary,
                    borderWidth: 1,
                    borderRadius: 4,
                    barThickness: 16,
                    minBarLength: 10
                }]
            },
            options: {
                ...commonChartOptions,
                indexAxis: 'y',  // 水平方向的條形圖
                scales: {
                    x: {
                        position: 'top',
                        title: {
                            display: true,
                            text: '練習時間（分鐘）',
                            color: chartColors.primary,
                            font: {
                                size: 13,
                                weight: 'bold'
                            }
                        },
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: chartColors.primary
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            padding: 10,
                            callback: function(value, index) {
                                const label = this.getLabelForValue(value);
                                // 如果曲目名稱太長，截斷並添加省略號
                                return label.length > 20 ? label.substring(0, 20) + '...' : label;
                            }
                        }
                    }
                },
                plugins: {
                    ...commonChartOptions.plugins,
                    tooltip: {
                        ...commonChartOptions.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.x !== null) {
                                    if (context.datasetIndex === 0) {
                                        label += `${context.parsed.x} 分鐘`;
                                    } else {
                                        // 將縮放後的值轉換回原始評分
                                        const originalRating = (context.parsed.x / maxMinutes * 5).toFixed(1);
                                        label += `${originalRating} 分`;
                                    }
                                }
                                return label;
                            },
                            title: function(tooltipItems) {
                                // 在工具提示中顯示完整的曲目名稱
                                return data[tooltipItems[0].dataIndex].piece;
                            }
                        }
                    },
                    legend: {
                        position: 'top',
                        align: 'start',
                        labels: {
                            boxWidth: 15,
                            usePointStyle: true,
                            pointStyle: 'rect',
                            padding: 15
                        }
                    }
                },
                layout: {
                    padding: {
                        top: 30,  // 為頂部圖例留出空間
                        right: 20
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuart'
                },
                barPercentage: 0.8,  // 控制條形組的寬度
                categoryPercentage: 0.9  // 控制組內條形的間距
            }
        });
    };

    await loadChartData(chartId, fetchData, createChart);
}

// 載入最近練習趨勢
export async function loadRecentTrendData(studentName) {
    const chartId = 'recentTrendChart';
    
    const fetchData = async () => {
        const params = new URLSearchParams(window.location.search);
        params.set('student_name', studentName);
        const response = await fetch(`/api/recent-trend/?${params}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    };

    const createChart = async (data) => {
        if (charts.recentTrendChart) {
            charts.recentTrendChart.destroy();
        }

        charts.recentTrendChart = new Chart(document.getElementById(chartId), {
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
    };

    await loadChartData(chartId, fetchData, createChart);
}

// 載入練習重點分析
export async function loadFocusStats(studentName) {
    const chartId = 'focusChart';
    
    const fetchData = async () => {
        const params = new URLSearchParams(window.location.search);
        params.set('student_name', studentName);
        const response = await fetch(`/api/focus-stats/?${params}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    };

    const createChart = async (data) => {
        if (charts.focusChart) {
            charts.focusChart.destroy();
        }

        charts.focusChart = new Chart(document.getElementById(chartId), {
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
    };

    await loadChartData(chartId, fetchData, createChart);
}

// 載入曲目成效比較
export async function loadPieceEffectivenessData(studentName) {
    const chartId = 'pieceEffectivenessChart';
    
    const fetchData = async () => {
        const params = new URLSearchParams(window.location.search);
        params.set('student_name', studentName);
        const response = await fetch(`/api/piece-practice/?${params}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    };

    const createChart = async (data) => {
        if (charts.pieceEffectivenessChart) {
            charts.pieceEffectivenessChart.destroy();
        }

        // 只取前6首曲子
        const topPieces = data.slice(0, 6);

        // 定義雷達圖的維度
        const dimensions = [
            '投入時間',
            '分數提升',
            '技巧掌握',
            '技巧練習',
            '節奏掌握',
            '音準掌握',
            '表現力'
        ];

        // 為每首曲子創建數據集
        const datasets = topPieces.map((piece, index) => ({
            label: piece.piece,
            data: [
                piece.dimensions.time_investment,
                piece.dimensions.score_progress,
                piece.dimensions.mastery,
                piece.dimensions.technique,
                piece.dimensions.rhythm,
                piece.dimensions.intonation,
                piece.dimensions.expression
            ],
            backgroundColor: `${chartColors.primary}20`,
            borderColor: Object.values(chartColors)[index % Object.keys(chartColors).length],
            borderWidth: 2,
            pointBackgroundColor: Object.values(chartColors)[index % Object.keys(chartColors).length],
            pointRadius: 4,
            pointHoverRadius: 6
        }));

        charts.pieceEffectivenessChart = new Chart(document.getElementById(chartId), {
            type: 'radar',
            data: {
                labels: dimensions,
                datasets: datasets
            },
            options: {
                ...commonChartOptions,
                scales: {
                    r: {
                        beginAtZero: true,
                        min: 0,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        },
                        pointLabels: {
                            font: {
                                size: 12,
                                weight: 'bold'
                            }
                        },
                        grid: {
                            color: `${chartColors.primary}20`
                        },
                        angleLines: {
                            color: `${chartColors.primary}20`
                        }
                    }
                },
                plugins: {
                    ...commonChartOptions.plugins,
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const piece = topPieces[context.datasetIndex];
                                const dimension = dimensions[context.dataIndex];
                                const value = context.raw;
                                
                                let tooltipLines = [
                                    `${piece.piece} - ${dimension}: ${value}%`
                                ];
                                
                                // 添加額外信息
                                if (dimension === '投入時間') {
                                    tooltipLines.push(`練習次數: ${piece.practice_count}次`);
                                } else if (dimension === '分數提升') {
                                    tooltipLines.push(`平均評分: ${piece.avg_rating}分`);
                                }
                                
                                return tooltipLines;
                            }
                        }
                    },
                    legend: {
                        position: 'right',
                        align: 'start',
                        labels: {
                            boxWidth: 15,
                            padding: 15,
                            font: {
                                size: 11
                            }
                        }
                    }
                },
                elements: {
                    line: {
                        tension: 0.2
                    }
                }
            }
        });

        // 添加點擊事件處理
        const canvas = document.getElementById(chartId);
        canvas.onclick = function(evt) {
            const points = charts.pieceEffectivenessChart.getElementsAtEventForMode(
                evt,
                'nearest',
                { intersect: true },
                true
            );
            
            if (points.length) {
                const piece = topPieces[points[0].datasetIndex];
                // TODO: 實現跳轉到練習建議頁面的功能
                console.log(`點擊了 ${piece.piece} 的數據點`);
            }
        };
    };

    await loadChartData(chartId, fetchData, createChart);
}

// 載入時間效果分析
export async function loadTimeEffectAnalysis(studentName) {
    const chartId = 'timeEffectChart';
    
    const fetchData = async () => {
        const params = new URLSearchParams(window.location.search);
        params.set('student_name', studentName);
        const response = await fetch(`/api/piece-practice/?${params}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    };

    const createChart = async (data) => {
        if (charts.timeEffectChart) {
            charts.timeEffectChart.destroy();
        }

        // 按練習時間排序
        data.sort((a, b) => b.total_minutes - a.total_minutes);
        const topPieces = data.slice(0, 8); // 只顯示前8首曲子

        charts.timeEffectChart = new Chart(document.getElementById(chartId), {
            type: 'scatter',
            data: {
                datasets: [{
                    label: '練習效果分析',
                    data: topPieces.map(d => ({
                        x: d.total_minutes,
                        y: d.avg_rating,
                        piece: d.piece,
                        efficiency: d.efficiency,
                        progress: d.score_progress
                    })),
                    backgroundColor: topPieces.map(d => {
                        // 根據效率等級設定顏色
                        switch(d.efficiency_level) {
                            case 'high': return chartColors.success + 'cc';
                            case 'medium': return chartColors.primary + 'cc';
                            default: return chartColors.secondary + 'cc';
                        }
                    }),
                    borderColor: chartColors.primary,
                    borderWidth: 1,
                    pointRadius: 8,
                    pointHoverRadius: 12
                }]
            },
            options: {
                ...commonChartOptions,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '練習時間（分鐘）',
                            color: chartColors.primary,
                            font: {
                                size: 13,
                                weight: 'bold'
                            }
                        },
                        grid: {
                            display: true,
                            color: `${chartColors.primary}15`
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: '平均評分',
                            color: chartColors.primary,
                            font: {
                                size: 13,
                                weight: 'bold'
                            }
                        },
                        min: 1,
                        max: 5,
                        grid: {
                            display: true,
                            color: `${chartColors.primary}15`
                        }
                    }
                },
                plugins: {
                    ...commonChartOptions.plugins,
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const point = context.raw;
                                const efficiencyText = {
                                    'high': '高',
                                    'medium': '中',
                                    'low': '低'
                                }[point.efficiency_level] || '低';
                                const progressText = point.progress >= 0 ? 
                                    `進步 ${point.progress.toFixed(1)} 分` : 
                                    `退步 ${Math.abs(point.progress).toFixed(1)} 分`;
                                
                                return [
                                    `曲目：${point.piece}`,
                                    `練習時間：${point.x} 分鐘`,
                                    `平均評分：${point.y.toFixed(1)} 分`,
                                    `效率等級：${efficiencyText}`,
                                    `評分變化：${progressText}`
                                ];
                            }
                        }
                    }
                }
            }
        });
    };

    await loadChartData(chartId, fetchData, createChart);
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