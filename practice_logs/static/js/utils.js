// 日期格式化
export function formatDate(date) {
    return date.toLocaleDateString('zh-TW', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// 錯誤處理
export function handleError(chartId, error) {
    console.error(`Error in ${chartId}:`, error);
    const container = document.getElementById(chartId).parentElement;
    container.innerHTML = `
        <div class="error-message" style="text-align: center; color: #800020; padding: 2rem;">
            <p>載入圖表時發生錯誤</p>
            <small>${error.message}</small>
        </div>
    `;
}

// 設置日期選擇器
export function setupDatePicker() {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);  // 預設顯示最近30天

    document.getElementById('startDate').value = startDate.toISOString().split('T')[0];
    document.getElementById('endDate').value = endDate.toISOString().split('T')[0];
}

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