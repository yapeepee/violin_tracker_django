import { setupChartDefaults } from './charts/config.js';
import { setupDatePicker, handleDateRangeSubmit, handleQuickDateSelect, loadAllCharts } from './utils.js';
import {
    loadWeeklyData,
    loadPieceData,
    loadRecentTrendData,
    loadFocusStats,
    loadRestDayStats,
    loadSwitchingData
} from './charts/charts.js';

// 初始化應用
function initializeApp() {
    const studentName = document.querySelector('.page-title').textContent.replace('的練習分析', '');
    
    // 設置圖表全局樣式
    setupChartDefaults();
    
    // 設置日期選擇器
    setupDatePicker();
    
    // 綁定事件處理器
    document.getElementById('dateRangeForm').addEventListener('submit', handleDateRangeSubmit);
    document.querySelectorAll('#dateRangeForm button[data-days]').forEach(button => {
        button.addEventListener('click', handleQuickDateSelect);
    });
    
    // 載入所有圖表
    loadAllCharts(studentName);
}

// 載入所有圖表
function loadAllCharts(studentName) {
    loadWeeklyData(studentName);
    loadPieceData(studentName);
    loadRecentTrendData(studentName);
    loadFocusStats(studentName);
    loadRestDayStats(studentName);
    loadSwitchingData(studentName);
}

// 當 DOM 加載完成後初始化應用
document.addEventListener('DOMContentLoaded', initializeApp); 