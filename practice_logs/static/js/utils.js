// 日期格式化
export function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-TW');
}

// API錯誤處理
export function handleError(elementId, error) {
    console.error(`Error loading data for ${elementId}:`, error);
    const element = document.getElementById(elementId);
    if (element) {
        element.parentElement.innerHTML = `
            <div class="alert alert-danger" role="alert">
                載入資料時發生錯誤：${error.message || '未知錯誤'}
            </div>
        `;
    }
}

// 日期選擇器設置
export function setupDatePicker() {
    const today = new Date().toISOString().split('T')[0];
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
    const oneYearAgoStr = oneYearAgo.toISOString().split('T')[0];

    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');

    // 設置日期範圍限制
    startDateInput.max = today;
    startDateInput.min = oneYearAgoStr;
    endDateInput.max = today;
    endDateInput.min = oneYearAgoStr;

    // 設置預設值
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('start_date')) {
        startDateInput.value = urlParams.get('start_date');
    }
    if (urlParams.has('end_date')) {
        endDateInput.value = urlParams.get('end_date');
    } else {
        endDateInput.value = today;
        const defaultStart = new Date();
        defaultStart.setDate(defaultStart.getDate() - 30);
        startDateInput.value = defaultStart.toISOString().split('T')[0];
    }
}

// 日期範圍表單提交處理
export function handleDateRangeSubmit(e) {
    e.preventDefault();
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    if (startDate && endDate) {
        const url = new URL(window.location.href);
        url.searchParams.set('start_date', startDate);
        url.searchParams.set('end_date', endDate);
        window.location.href = url.toString();
    }
}

// 快速日期選擇處理
export function handleQuickDateSelect() {
    const days = parseInt(this.dataset.days);
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - days);

    document.getElementById('endDate').value = endDate.toISOString().split('T')[0];
    document.getElementById('startDate').value = startDate.toISOString().split('T')[0];

    document.getElementById('dateRangeForm').dispatchEvent(new Event('submit'));
} 