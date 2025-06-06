// 圖表顏色系統
export const chartColors = {
    primary: '#8B4513',    // 溫暖的深褐色
    secondary: '#DAA520',  // 金色
    accent: '#800020',     // 酒紅色
    success: '#556B2F',    // 橄欖綠
    light: '#FFF8E7',      // 溫暧的米色
    dark: '#2F1810'        // 深木色
};

// 通用圖表配置
export const commonChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'bottom',
            labels: {
                padding: 20,
                usePointStyle: true,
                pointStyle: 'circle',
                font: {
                    family: '"Baskerville", "Times New Roman", serif',
                    size: 12
                }
            }
        }
    },
    scales: {
        r: {
            grid: {
                color: 'rgba(139, 69, 19, 0.1)'
            }
        }
    }
};

// 圖表全局樣式
export function setupChartDefaults() {
    Chart.defaults.color = chartColors.dark;
    Chart.defaults.font.family = '"Baskerville", "Times New Roman", serif';
} 