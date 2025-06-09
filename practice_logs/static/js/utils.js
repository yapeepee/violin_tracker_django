// 日期處理工具
export const dateUtils = {
    formatDate(date) {
        return date.toLocaleDateString('zh-TW', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    },

    getDateRange(days) {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - days);
        return {
            start: startDate.toISOString().split('T')[0],
            end: endDate.toISOString().split('T')[0]
        };
    },

    setupDatePicker(defaultDays = 30) {
        const { start, end } = this.getDateRange(defaultDays);
        document.getElementById('startDate').value = start;
        document.getElementById('endDate').value = end;
    }
};

// 錯誤處理工具
export const errorUtils = {
    handleError(chartId, error) {
        console.error(`Error in ${chartId}:`, error);
        const container = document.getElementById(chartId).parentElement;
        container.innerHTML = `
            <div class="error-message" style="text-align: center; color: #800020; padding: 2rem;">
                <p>載入圖表時發生錯誤</p>
                <small>${error.message}</small>
            </div>
        `;
    },

    showError(message, duration = 3000) {
        const errorAlert = document.querySelector('.alert-danger');
        if (errorAlert) {
            errorAlert.textContent = message;
            errorAlert.classList.remove('d-none');
            setTimeout(() => {
                errorAlert.classList.add('d-none');
            }, duration);
        }
    }
};

// 事件處理工具
export const eventUtils = {
    handleDateRangeSubmit(event, callback) {
        event.preventDefault();
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        if (callback && typeof callback === 'function') {
            callback(startDate, endDate);
        }
    },

    handleQuickDateSelect(days, callback) {
        const { start, end } = dateUtils.getDateRange(days);
        document.getElementById('startDate').value = start;
        document.getElementById('endDate').value = end;

        if (callback && typeof callback === 'function') {
            callback(start, end);
        }
    }
};

// 圖表輔助工具
export const chartUtils = {
    getChartDimensions(container) {
        const parent = container.parentElement;
        return {
            width: parent.clientWidth,
            height: parent.clientHeight
        };
    },

    resizeChart(chart, container) {
        const { width, height } = this.getChartDimensions(container);
        chart.resize(width, height);
    }
};

// 導出原始函數以保持向後兼容
export const formatDate = dateUtils.formatDate;
export const handleError = errorUtils.handleError;
export const setupDatePicker = dateUtils.setupDatePicker.bind(dateUtils);

// 處理日期範圍表單提交
export function handleDateRangeSubmit(event) {
    event.preventDefault();
    const studentName = document.querySelector('.page-title').textContent.replace('的練習分析', '');
    loadAllCharts(studentName);
}

// 處理快速日期選擇
export function handleQuickDateSelect(event) {
    const days = parseInt(event.target.dataset.days);
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    document.getElementById('startDate').value = startDate.toISOString().split('T')[0];
    document.getElementById('endDate').value = endDate.toISOString().split('T')[0];

    const studentName = document.querySelector('.page-title').textContent.replace('的練習分析', '');
    loadAllCharts(studentName);
}

// 載入所有圖表
export function loadAllCharts(studentName) {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const params = new URLSearchParams({ start_date: startDate, end_date: endDate });

    // 載入各個圖表
    loadWeeklyData(studentName);
    loadPieceData(studentName);
    loadRecentTrendData(studentName);
    loadFocusStats(studentName);
    loadRestDayStats(studentName);
    loadSwitchingData(studentName);
} 