// 顏色系統
export const chartColors = {
    primary: '#8B4513',    // 溫暖的深褐色
    secondary: '#DAA520',  // 金色
    accent: '#800020',     // 酒紅色
    success: '#556B2F',    // 橄欖綠
    light: '#FFF8E7',      // 溫暧的米色
    dark: '#2F1810',       // 深木色
    
    // 輔助函數
    withOpacity: (color, opacity) => {
        return `${color}${Math.floor(opacity * 255).toString(16).padStart(2, '0')}`;
    }
};

// 字體系統
export const chartFonts = {
    primary: '"Baskerville", "Times New Roman", serif',
    secondary: '"Optima", "Segoe UI", sans-serif',
    size: {
        small: 12,
        medium: 14,
        large: 16,
        title: 18
    }
};

// 動畫配置
export const chartAnimations = {
    duration: 750,
    easing: 'easeInOutQuart',
    responsive: true,
    onComplete: (animation) => {
        // 動畫完成後的回調
    }
};

// 響應式斷點
export const chartBreakpoints = {
    small: 576,
    medium: 768,
    large: 992,
    xlarge: 1200
};

// 通用圖表配置
export const commonChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    
    // 插件配置
    plugins: {
        legend: {
            position: 'bottom',
            labels: {
                padding: 20,
                usePointStyle: true,
                pointStyle: 'circle',
                font: {
                    family: chartFonts.primary,
                    size: chartFonts.size.small
                }
            }
        },
        tooltip: {
            backgroundColor: chartColors.withOpacity(chartColors.dark, 0.8),
            titleFont: {
                family: chartFonts.primary,
                size: chartFonts.size.medium
            },
            bodyFont: {
                family: chartFonts.secondary,
                size: chartFonts.size.small
            },
            padding: 12,
            cornerRadius: 6
        }
    },
    
    // 刻度配置
    scales: {
        r: {
            grid: {
                color: chartColors.withOpacity(chartColors.primary, 0.1)
            },
            ticks: {
                font: {
                    family: chartFonts.secondary,
                    size: chartFonts.size.small
                }
            }
        }
    },
    
    // 動畫配置
    animation: chartAnimations,
    
    // 響應式配置
    responsive: true,
    maintainAspectRatio: false,
    
    // 互動配置
    interaction: {
        mode: 'nearest',
        intersect: false,
        axis: 'x'
    }
};

// 設置圖表默認值
export function setupChartDefaults() {
    Chart.defaults.color = chartColors.dark;
    Chart.defaults.font.family = chartFonts.primary;
    Chart.defaults.font.size = chartFonts.size.small;
    
    // 根據視窗大小調整字體
    const updateFontSizes = () => {
        const width = window.innerWidth;
        let scaleFactor = 1;
        
        if (width < chartBreakpoints.small) {
            scaleFactor = 0.8;
        } else if (width < chartBreakpoints.medium) {
            scaleFactor = 0.9;
        }
        
        Chart.defaults.font.size = chartFonts.size.small * scaleFactor;
    };
    
    // 監聽視窗大小變化
    window.addEventListener('resize', updateFontSizes);
    updateFontSizes();
} 