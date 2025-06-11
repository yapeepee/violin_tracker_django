/**
 * 教師儀表板進階圖表系統
 * 提供互動式數據可視化功能
 */

class TeacherCharts {
    constructor() {
        this.charts = {};
        this.colors = {
            primary: '#4A90E2',
            success: '#5CB85C',
            warning: '#F0AD4E',
            danger: '#D9534F',
            info: '#5BC0DE',
            secondary: '#6C757D',
            light: '#F8F9FA',
            dark: '#343A40'
        };
        this.gradients = {};
        this.init();
    }

    init() {
        // 設置Chart.js全局配置
        Chart.defaults.font.family = "'Noto Sans TC', sans-serif";
        Chart.defaults.animation.duration = 1000;
        Chart.defaults.animation.easing = 'easeInOutQuart';
        
        // 初始化所有圖表
        this.initStudentProgressChart();
        this.initPracticeTimeChart();
        this.initSkillRadarChart();
        this.initAttendanceChart();
        this.initPerformanceHeatmap();
        this.initRealtimeActivityChart();
        
        // 設置響應式重繪
        this.setupResponsive();
        
        // 設置數據更新
        this.setupDataRefresh();
    }

    // 創建漸變色
    createGradient(ctx, color1, color2) {
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, color1);
        gradient.addColorStop(1, color2);
        return gradient;
    }

    // 學生進度圖表
    initStudentProgressChart() {
        const ctx = document.getElementById('studentProgressChart');
        if (!ctx) return;

        const chartCtx = ctx.getContext('2d');
        const gradient = this.createGradient(chartCtx, 
            'rgba(74, 144, 226, 0.8)', 
            'rgba(74, 144, 226, 0.1)'
        );

        this.charts.studentProgress = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '平均進度分數',
                    data: [],
                    borderColor: this.colors.primary,
                    backgroundColor: gradient,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 8,
                    pointBackgroundColor: '#fff',
                    pointBorderColor: this.colors.primary,
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        cornerRadius: 8,
                        titleFont: {
                            size: 14
                        },
                        bodyFont: {
                            size: 13
                        },
                        callbacks: {
                            label: function(context) {
                                return `進度: ${context.parsed.y}%`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 12
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            font: {
                                size: 12
                            },
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });

        // 載入數據
        this.loadStudentProgressData();
    }

    // 練習時間分布圖
    initPracticeTimeChart() {
        const ctx = document.getElementById('practiceTimeChart');
        if (!ctx) return;

        this.charts.practiceTime = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['早晨', '上午', '下午', '晚上'],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        this.colors.warning,
                        this.colors.success,
                        this.colors.info,
                        this.colors.primary
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            usePointStyle: true,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value}分鐘 (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    animateScale: true
                }
            }
        });

        // 在中心顯示總時間
        this.addCenterText(ctx);
        
        this.loadPracticeTimeData();
    }

    // 技能雷達圖
    initSkillRadarChart() {
        const ctx = document.getElementById('skillRadarChart');
        if (!ctx) return;

        this.charts.skillRadar = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['音準', '節奏', '技巧', '表現力', '讀譜', '記憶'],
                datasets: [{
                    label: '班級平均',
                    data: [],
                    borderColor: this.colors.primary,
                    backgroundColor: 'rgba(74, 144, 226, 0.2)',
                    borderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }, {
                    label: '上月平均',
                    data: [],
                    borderColor: this.colors.secondary,
                    backgroundColor: 'rgba(108, 117, 125, 0.1)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 10,
                        ticks: {
                            stepSize: 2,
                            font: {
                                size: 11
                            }
                        },
                        pointLabels: {
                            font: {
                                size: 13
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.r}/10`;
                            }
                        }
                    }
                }
            }
        });

        this.loadSkillData();
    }

    // 出席率圖表
    initAttendanceChart() {
        const ctx = document.getElementById('attendanceChart');
        if (!ctx) return;

        const chartCtx = ctx.getContext('2d');
        const successGradient = this.createGradient(chartCtx,
            'rgba(92, 184, 92, 0.8)',
            'rgba(92, 184, 92, 0.1)'
        );
        const warningGradient = this.createGradient(chartCtx,
            'rgba(240, 173, 78, 0.8)',
            'rgba(240, 173, 78, 0.1)'
        );

        this.charts.attendance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: '出席',
                    data: [],
                    backgroundColor: successGradient,
                    borderColor: this.colors.success,
                    borderWidth: 2,
                    borderRadius: 8,
                    barPercentage: 0.6
                }, {
                    label: '缺席',
                    data: [],
                    backgroundColor: warningGradient,
                    borderColor: this.colors.warning,
                    borderWidth: 2,
                    borderRadius: 8,
                    barPercentage: 0.6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 12
                            }
                        }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            usePointStyle: true,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            footer: function(tooltipItems) {
                                let sum = 0;
                                tooltipItems.forEach(function(tooltipItem) {
                                    sum += tooltipItem.parsed.y;
                                });
                                return '總計: ' + sum + ' 堂';
                            }
                        }
                    }
                }
            }
        });

        this.loadAttendanceData();
    }

    // 表現熱力圖
    initPerformanceHeatmap() {
        const container = document.getElementById('performanceHeatmap');
        if (!container) return;

        // 創建熱力圖網格
        const students = ['學生A', '學生B', '學生C', '學生D', '學生E'];
        const weeks = ['第1週', '第2週', '第3週', '第4週'];
        
        let html = '<div class="heatmap-grid">';
        
        // 標題行
        html += '<div class="heatmap-cell header"></div>';
        weeks.forEach(week => {
            html += `<div class="heatmap-cell header">${week}</div>`;
        });
        
        // 數據行
        students.forEach(student => {
            html += `<div class="heatmap-cell header">${student}</div>`;
            weeks.forEach((week, weekIndex) => {
                const value = Math.floor(Math.random() * 5) + 6; // 6-10分
                const color = this.getHeatmapColor(value);
                html += `
                    <div class="heatmap-cell" 
                         style="background-color: ${color};"
                         data-student="${student}"
                         data-week="${week}"
                         data-value="${value}">
                        ${value}
                    </div>
                `;
            });
        });
        
        html += '</div>';
        container.innerHTML = html;
        
        // 添加交互
        this.setupHeatmapInteraction();
    }

    // 實時活動圖表
    initRealtimeActivityChart() {
        const ctx = document.getElementById('realtimeActivityChart');
        if (!ctx) return;

        this.charts.realtimeActivity = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.generateTimeLabels(10),
                datasets: [{
                    label: '活躍學生數',
                    data: [],
                    borderColor: this.colors.info,
                    backgroundColor: 'rgba(91, 192, 222, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            font: {
                                size: 11
                            },
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `活躍學生: ${context.parsed.y} 位`;
                            }
                        }
                    }
                },
                animation: {
                    duration: 0 // 實時數據不需要動畫
                }
            }
        });

        // 開始實時更新
        this.startRealtimeUpdates();
    }

    // 載入學生進度數據
    async loadStudentProgressData() {
        try {
            const response = await fetch('/api/teacher/student-progress-trend/');
            const data = await response.json();
            
            this.charts.studentProgress.data.labels = data.labels;
            this.charts.studentProgress.data.datasets[0].data = data.values;
            this.charts.studentProgress.update();
            
            // 添加動畫效果
            this.animateChart(this.charts.studentProgress);
        } catch (error) {
            console.error('Failed to load progress data:', error);
        }
    }

    // 載入練習時間數據
    async loadPracticeTimeData() {
        try {
            const response = await fetch('/api/teacher/practice-time-distribution/');
            const data = await response.json();
            
            this.charts.practiceTime.data.datasets[0].data = [
                data.morning || 0,
                data.afternoon || 0,
                data.evening || 0,
                data.night || 0
            ];
            this.charts.practiceTime.update();
            
            // 更新中心文字
            const total = Object.values(data).reduce((a, b) => a + b, 0);
            this.updateCenterText(total);
        } catch (error) {
            console.error('Failed to load practice time data:', error);
        }
    }

    // 載入技能數據
    async loadSkillData() {
        try {
            const response = await fetch('/api/teacher/skill-averages/');
            const data = await response.json();
            
            this.charts.skillRadar.data.datasets[0].data = data.current;
            this.charts.skillRadar.data.datasets[1].data = data.previous;
            this.charts.skillRadar.update();
        } catch (error) {
            console.error('Failed to load skill data:', error);
        }
    }

    // 載入出席率數據
    async loadAttendanceData() {
        try {
            const response = await fetch('/api/teacher/attendance-stats/');
            const data = await response.json();
            
            this.charts.attendance.data.labels = data.labels;
            this.charts.attendance.data.datasets[0].data = data.attended;
            this.charts.attendance.data.datasets[1].data = data.missed;
            this.charts.attendance.update();
        } catch (error) {
            console.error('Failed to load attendance data:', error);
        }
    }

    // 生成時間標籤
    generateTimeLabels(count) {
        const labels = [];
        const now = new Date();
        
        for (let i = count - 1; i >= 0; i--) {
            const time = new Date(now - i * 60000); // 每分鐘
            labels.push(time.toLocaleTimeString('zh-TW', {
                hour: '2-digit',
                minute: '2-digit'
            }));
        }
        
        return labels;
    }

    // 開始實時更新
    startRealtimeUpdates() {
        // 初始數據
        const initialData = Array(10).fill(0).map(() => Math.floor(Math.random() * 5));
        this.charts.realtimeActivity.data.datasets[0].data = initialData;
        this.charts.realtimeActivity.update();
        
        // 每5秒更新一次
        setInterval(() => {
            this.updateRealtimeData();
        }, 5000);
    }

    // 更新實時數據
    updateRealtimeData() {
        const chart = this.charts.realtimeActivity;
        const data = chart.data.datasets[0].data;
        
        // 移除第一個數據點
        data.shift();
        chart.data.labels.shift();
        
        // 添加新數據點
        data.push(Math.floor(Math.random() * 8));
        const now = new Date();
        chart.data.labels.push(now.toLocaleTimeString('zh-TW', {
            hour: '2-digit',
            minute: '2-digit'
        }));
        
        chart.update('none'); // 無動畫更新
    }

    // 獲取熱力圖顏色
    getHeatmapColor(value) {
        const colors = [
            '#ffebee', '#ffcdd2', '#ef9a9a', '#e57373', '#ef5350',
            '#f44336', '#e53935', '#d32f2f', '#c62828', '#b71c1c'
        ];
        return colors[Math.min(value - 1, 9)] || colors[9];
    }

    // 設置熱力圖交互
    setupHeatmapInteraction() {
        const cells = document.querySelectorAll('.heatmap-cell:not(.header)');
        
        cells.forEach(cell => {
            cell.addEventListener('mouseenter', (e) => {
                const student = e.target.dataset.student;
                const week = e.target.dataset.week;
                const value = e.target.dataset.value;
                
                this.showHeatmapTooltip(e, student, week, value);
            });
            
            cell.addEventListener('mouseleave', () => {
                this.hideHeatmapTooltip();
            });
        });
    }

    // 顯示熱力圖提示
    showHeatmapTooltip(event, student, week, value) {
        const tooltip = document.createElement('div');
        tooltip.className = 'heatmap-tooltip';
        tooltip.innerHTML = `
            <strong>${student}</strong><br>
            ${week}: ${value}/10
        `;
        
        document.body.appendChild(tooltip);
        
        const rect = event.target.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
    }

    // 隱藏熱力圖提示
    hideHeatmapTooltip() {
        const tooltip = document.querySelector('.heatmap-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }

    // 在圓環圖中心添加文字
    addCenterText(canvas) {
        const chart = this.charts.practiceTime;
        
        Chart.register({
            id: 'centerText',
            beforeDraw: function(chart) {
                if (chart.config.type !== 'doughnut') return;
                
                const ctx = chart.ctx;
                const centerX = (chart.chartArea.left + chart.chartArea.right) / 2;
                const centerY = (chart.chartArea.top + chart.chartArea.bottom) / 2;
                
                ctx.save();
                ctx.font = 'bold 24px Noto Sans TC';
                ctx.fillStyle = '#2c3e50';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                
                const total = chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                ctx.fillText(total + '分', centerX, centerY - 10);
                
                ctx.font = '14px Noto Sans TC';
                ctx.fillStyle = '#6c757d';
                ctx.fillText('總練習時間', centerX, centerY + 15);
                
                ctx.restore();
            }
        });
    }

    // 更新中心文字
    updateCenterText(total) {
        // Chart.js 會自動處理
    }

    // 圖表動畫
    animateChart(chart) {
        chart.update('active');
    }

    // 設置響應式
    setupResponsive() {
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                Object.values(this.charts).forEach(chart => {
                    if (chart) chart.resize();
                });
            }, 250);
        });
    }

    // 設置數據刷新
    setupDataRefresh() {
        // 每5分鐘刷新一次數據
        setInterval(() => {
            this.refreshAllData();
        }, 300000);
    }

    // 刷新所有數據
    refreshAllData() {
        this.loadStudentProgressData();
        this.loadPracticeTimeData();
        this.loadSkillData();
        this.loadAttendanceData();
    }

    // 導出圖表
    exportChart(chartId, format = 'png') {
        const chart = this.charts[chartId];
        if (!chart) return;
        
        const url = chart.toBase64Image();
        const link = document.createElement('a');
        link.download = `chart_${chartId}_${Date.now()}.${format}`;
        link.href = url;
        link.click();
    }

    // 切換數據集
    toggleDataset(chartId, datasetIndex) {
        const chart = this.charts[chartId];
        if (!chart) return;
        
        const dataset = chart.data.datasets[datasetIndex];
        dataset.hidden = !dataset.hidden;
        chart.update();
    }

    // 更新圖表主題
    updateTheme(theme) {
        const isDark = theme === 'dark';
        
        Chart.defaults.color = isDark ? '#fff' : '#666';
        Chart.defaults.borderColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
        
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.update();
        });
    }
}

// CSS 樣式
const style = document.createElement('style');
style.textContent = `
    /* 圖表容器 */
    .chart-container {
        position: relative;
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        margin-bottom: 30px;
    }
    
    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    
    .chart-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #2c3e50;
    }
    
    .chart-actions {
        display: flex;
        gap: 10px;
    }
    
    .chart-btn {
        padding: 5px 10px;
        border: 1px solid #e0e0e0;
        background: white;
        border-radius: 5px;
        cursor: pointer;
        font-size: 0.85rem;
        transition: all 0.3s ease;
    }
    
    .chart-btn:hover {
        background: #f5f5f5;
        border-color: #4A90E2;
    }
    
    .chart-wrapper {
        position: relative;
        height: 300px;
    }
    
    /* 熱力圖樣式 */
    .heatmap-grid {
        display: grid;
        grid-template-columns: 100px repeat(4, 1fr);
        gap: 5px;
        padding: 10px;
    }
    
    .heatmap-cell {
        padding: 15px;
        text-align: center;
        border-radius: 8px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
    }
    
    .heatmap-cell.header {
        background: #f8f9fa;
        font-weight: 600;
        color: #666;
        cursor: default;
    }
    
    .heatmap-cell:not(.header):hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .heatmap-tooltip {
        position: absolute;
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 10px;
        border-radius: 8px;
        font-size: 0.9rem;
        pointer-events: none;
        z-index: 1000;
    }
    
    /* 統計卡片 */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
    }
    
    .stat-card {
        background: white;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .stat-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #4A90E2, #6DB3D1);
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.12);
    }
    
    .stat-icon {
        font-size: 2.5rem;
        margin-bottom: 15px;
        opacity: 0.8;
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 5px;
    }
    
    .stat-label {
        color: #6c757d;
        font-size: 0.9rem;
    }
    
    .stat-change {
        margin-top: 10px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .stat-change.positive {
        color: #5CB85C;
    }
    
    .stat-change.negative {
        color: #D9534F;
    }
    
    /* 載入動畫 */
    .chart-loading {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        text-align: center;
    }
    
    .chart-spinner {
        border: 3px solid #f3f3f3;
        border-top: 3px solid #4A90E2;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 0 auto 15px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* 響應式設計 */
    @media (max-width: 768px) {
        .chart-wrapper {
            height: 250px;
        }
        
        .heatmap-grid {
            grid-template-columns: 80px repeat(4, 1fr);
            gap: 3px;
            font-size: 0.85rem;
        }
        
        .heatmap-cell {
            padding: 10px 5px;
        }
    }
`;
document.head.appendChild(style);

// 初始化教師圖表系統
document.addEventListener('DOMContentLoaded', () => {
    window.teacherCharts = new TeacherCharts();
});