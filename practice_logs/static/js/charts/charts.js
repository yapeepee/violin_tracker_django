import { chartColors, commonChartOptions } from './config.js';
import { formatDate, handleError } from '../utils.js';

// 存儲所有圖表實例
const charts = {};

// 通用圖表載入函數
async function loadChartData(chartId, fetchData, createChart) {
    try {
        showLoading(chartId);
        const data = await fetchData();
        await createChart(data);
        hideLoading(chartId);
    } catch (error) {
        handleError(chartId, error);
    }
}

// 載入狀態管理
function showLoading(chartId) {
    const canvas = document.getElementById(chartId);
    if (!canvas) return;
    
    canvas.style.opacity = '0.5';
    const container = canvas.parentElement;
    
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

function hideLoading(chartId) {
    const canvas = document.getElementById(chartId);
    if (!canvas) return;
    
    canvas.style.opacity = '1';
    const loader = canvas.parentElement.querySelector('.chart-loader');
    if (loader) {
        loader.style.display = 'none';
    }
}

// 圖表配置生成器
function createChartConfig(type, labels, datasets, customOptions = {}) {
    return {
        type,
        data: { labels, datasets },
        options: {
            ...commonChartOptions,
            ...customOptions
        }
    };
}

// 統計信息更新
function updateStatsInfo(response) {
    const statsInfo = document.getElementById('focusStatsInfo');
    if (!statsInfo) return;

    // 優先使用 API 回傳的聚合欄位
    const total_time = response.total_minutes ?? 0;
    const avg_rating = response.avg_rating ?? 0;
    const practice_count = response.total_sessions ?? 0;

    // 找出主要練習重點
    const data = response.data || [];
    const mainFocus = data.length > 0 
        ? data.reduce((a, b) => (b.percentage || 0) > (a.percentage || 0) ? b : a) 
        : { focus_display: '無數據', percentage: 0 };

    statsInfo.innerHTML = `
        <div class="row text-center">
            <div class="col-md-4">
                <div class="stat-item">
                    <h5>總練習時間</h5>
                    <p>${total_time} 分鐘</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stat-item">
                    <h5>平均評分</h5>
                    <p>${avg_rating.toFixed(1)} 分</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stat-item">
                    <h5>練習次數</h5>
                    <p>${practice_count} 次</p>
                </div>
            </div>
            <div class="col-12 mt-3">
                <div class="stat-item">
                    <h5>主要練習重點</h5>
                    <p>${mainFocus.focus_display} (${mainFocus.percentage || 0}%)</p>
                </div>
            </div>
        </div>
    `;
    statsInfo.classList.remove('d-none');
    setTimeout(() => statsInfo.classList.add('show'), 100);
}

// 圖表數據轉換器
function transformChartData(data, type) {
    switch (type) {
        case 'weekly':
            return {
                labels: data.map(d => formatDate(new Date(d.date))),
                datasets: [{
                    label: '練習時間（分鐘）',
                    data: data.map(d => d.total_minutes),
                    borderColor: chartColors.primary,
                    backgroundColor: `${chartColors.primary}30`,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y'
                }]
            };
        case 'piece':
            return {
                labels: data.map(d => d.piece),
                datasets: [{
                    label: '練習時間比例（%）',
                    data: data.map(d => d.dimensions.time_investment),
                    backgroundColor: `${chartColors.primary}cc`
                }]
            };
        // 可以根據需要添加更多類型
        default:
            return null;
    }
}

// 載入每週練習數據
export async function loadWeeklyData(studentName) {
    const chartId = 'weeklyChart';
    
    const fetchData = async () => {
        const params = new URLSearchParams(window.location.search);
        params.set('student_name', studentName);
        const response = await fetch(`/api/weekly-practice/?${params}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    };

    const createChart = async (data) => {
        if (charts.weeklyChart) charts.weeklyChart.destroy();
        
        const chartData = transformChartData(data, 'weekly');
        charts.weeklyChart = new Chart(
            document.getElementById(chartId),
            createChartConfig('line', chartData.labels, chartData.datasets, {
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '練習時間（分鐘）'
                        }
                    }
                }
            })
        );
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
        const data = await response.json();
        console.log('樂曲練習數據:', data);  // 添加日誌
        return data;
    };

    const createChart = async (data) => {
        if (charts.pieceChart) {
            charts.pieceChart.destroy();
        }

        console.log('正在創建樂曲練習圖表，數據:', data);  // 添加日誌
        // 按練習時間排序數據
        data.sort((a, b) => b.dimensions.time_investment - a.dimensions.time_investment);

        charts.pieceChart = new Chart(document.getElementById(chartId), {
            type: 'bar',
            data: {
                labels: data.map(d => d.piece),
                datasets: [{
                    label: '練習時間比例（%）',
                    data: data.map(d => d.dimensions.time_investment),
                    backgroundColor: `${chartColors.primary}cc`,
                    borderColor: chartColors.primary,
                    borderWidth: 1,
                    borderRadius: 4,
                    barThickness: 16,
                    minBarLength: 10
                }, {
                    label: '平均評分',
                    data: data.map(d => d.avg_rating),
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
                            text: '練習時間比例（%）/ 評分',
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
                                        label += `${context.parsed.x.toFixed(1)}%`;
                                        // 添加練習次數信息
                                        const piece = data[context.dataIndex];
                                        label += ` (${piece.practice_count}次)`;
                                    } else {
                                        label += `${context.parsed.x.toFixed(1)}分`;
                                    }
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
    const pieceSelector = document.getElementById('pieceSelector');
    const statsInfo = document.getElementById('focusStatsInfo');
    
    // 載入曲目列表
    const loadPieceOptions = async () => {
        const params = new URLSearchParams(window.location.search);
        params.set('student_name', studentName);
        const response = await fetch(`/api/student-pieces/?${params}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const pieces = await response.json();
        
        // 清空現有選項
        pieceSelector.innerHTML = '';
        
        // 添加"整體分析"選項
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.innerHTML = `
            <div class="d-flex align-items-center">
                <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJmZWF0aGVyIGZlYXRoZXItbXVzaWMiPjxwYXRoIGQ9Ik05IDIwYTIgMiAwIDEgMS00IDAgMiAyIDAgMCAxIDQgMHoiPjwvcGF0aD48cGF0aCBkPSJNMTkgMTZhMiAyIDAgMSAxLTQgMCAyIDIgMCAwIDEgNCAweiI+PC9wYXRoPjxwYXRoIGQ9Ik05IDE4VjVsOC0ydjEzIj48L3BhdGg+PC9zdmc+" 
                    class="composer-avatar me-2" 
                    width="24" 
                    height="24"
                    alt="整體分析">
                <span>整體分析</span>
            </div>
        `;
        pieceSelector.appendChild(defaultOption);
        
        // 添加曲目選項
        pieces.forEach(piece => {
            const option = document.createElement('option');
            option.value = piece.piece;
            option.innerHTML = `🎵 ${piece.piece} (${piece.percentage}%)`;
            pieceSelector.appendChild(option);
        });
    };
    
    const fetchData = async () => {
        const params = new URLSearchParams(window.location.search);
        params.set('student_name', studentName);
        const selectedPiece = pieceSelector.value;
        if (selectedPiece) {
            params.set('piece', selectedPiece);
        }
        const response = await fetch(`/api/focus-stats/?${params}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const jsonResponse = await response.json();
        
        // 確保數據結構完整
        if (!jsonResponse.data || !Array.isArray(jsonResponse.data)) {
            throw new Error('無效的數據格式');
        }
        
        return jsonResponse;
    };

    const createChart = async (response) => {
        if (charts.focusChart) {
            charts.focusChart.destroy();
        }

        const data = response.data;
        
        // 確保數據非空
        if (data.length === 0) {
            throw new Error('暫無練習數據');
        }
        
        // 更新統計信息
        updateStatsInfo(response);

        // 創建圖表配置
        const chartConfig = {
            type: 'radar',
            data: {
                labels: data.map(d => d.focus_display || '未知'),
                datasets: [{
                    label: '練習時間分布',
                    data: data.map(d => d.percentage || 0),
                    backgroundColor: `${chartColors.primary}40`,
                    borderColor: chartColors.primary,
                    borderWidth: 2,
                    pointBackgroundColor: chartColors.primary,
                    pointHoverBackgroundColor: chartColors.primary,
                    pointHoverBorderColor: '#fff',
                    pointHoverRadius: 8,
                    pointHoverBorderWidth: 2
                }]
            },
            options: {
                ...commonChartOptions,
                animation: {
                    duration: 800,
                    easing: 'easeInOutQuart'
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(139, 69, 19, 0.1)'
                        },
                        ticks: {
                            callback: value => `${value}%`,
                            backdropColor: 'rgba(255, 255, 255, 0.8)'
                        },
                        pointLabels: {
                            font: {
                                size: 12,
                                weight: '600'
                            }
                        }
                    }
                },
                plugins: {
                    ...commonChartOptions.plugins,
                    title: {
                        display: true,
                        text: `${response.piece || '整體'} - 練習重點分布`,
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        padding: 20
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const focus = data[context.dataIndex] || {};
                                return [
                                    `練習時間: ${focus.percentage || 0}%`,
                                    `總時間: ${focus.total_minutes || 0} 分鐘`,
                                    `平均評分: ${focus.avg_rating || 0}`
                                ];
                            }
                        }
                    }
                },
                elements: {
                    line: {
                        tension: 0.4
                    }
                }
            }
        };

        charts.focusChart = new Chart(document.getElementById(chartId), chartConfig);
    };

    // 獲取隨機音樂表情符號
    const getRandomMusicEmoji = () => {
        const emojis = ['🎵', '🎶', '🎼', '🎹', '🎻', '🎺', '🎸'];
        return emojis[Math.floor(Math.random() * emojis.length)];
    };

    // 初始化曲目選擇器
    await loadPieceOptions();
    
    // 添加選擇器變更事件
    pieceSelector.addEventListener('change', () => {
        statsInfo.classList.remove('show');
        setTimeout(() => {
            loadChartData(chartId, fetchData, createChart);
            pieceSelector.classList.add('highlight-piece');
            setTimeout(() => pieceSelector.classList.remove('highlight-piece'), 500);
        }, 300);
    });

    // 載入初始數據
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
        const data = await response.json();
        console.log('時間效果分析數據:', data);  // 添加日誌
        return data;
    };

    const createChart = async (data) => {
        if (charts.timeEffectChart) {
            charts.timeEffectChart.destroy();
        }

        console.log('正在創建時間效果分析圖表，數據:', data);
        // 按練習時間排序
        data.sort((a, b) => b.dimensions.time_investment - a.dimensions.time_investment);
        const topPieces = data.slice(0, 8); // 只顯示前8首曲子

        charts.timeEffectChart = new Chart(document.getElementById(chartId), {
            type: 'scatter',
            data: {
                datasets: [{
                    label: '練習效果分析',
                    data: topPieces.map(d => ({
                        x: d.dimensions.time_investment,
                        y: d.avg_rating,
                        piece: d.piece,
                        practice_count: d.practice_count,
                        score_progress: d.dimensions.score_progress
                    })),
                    backgroundColor: topPieces.map(d => {
                        // 根據進步程度設定顏色
                        const progress = d.dimensions.score_progress;
                        if (progress > 10) return chartColors.success + 'cc';
                        if (progress > 0) return chartColors.primary + 'cc';
                        return chartColors.secondary + 'cc';
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
                            text: '練習時間比例（%）',
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
                                const progressText = point.score_progress >= 0 ? 
                                    `進步 ${point.score_progress.toFixed(1)}%` : 
                                    `退步 ${Math.abs(point.score_progress).toFixed(1)}%`;
                                
                                return [
                                    `曲目：${point.piece}`,
                                    `練習時間比例：${point.x.toFixed(1)}%`,
                                    `平均評分：${point.y.toFixed(1)} 分`,
                                    `練習次數：${point.practice_count} 次`,
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