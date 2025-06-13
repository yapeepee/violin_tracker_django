// 修復載入動畫卡住的問題

(function() {
    'use strict';
    
    // 設定最大載入時間
    const MAX_LOADING_TIME = 3000; // 3秒
    
    // 強制隱藏所有載入元素的函數
    function forceHideAllLoaders() {
        // 隱藏全局載入器
        const pageLoader = document.getElementById('pageLoader');
        if (pageLoader) {
            pageLoader.style.display = 'none';
        }
        
        // 隱藏頁面特定的載入器
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
        
        // 隱藏所有包含 loader 類的元素
        const allLoaders = document.querySelectorAll('[class*="loader"], [class*="loading"]');
        allLoaders.forEach(loader => {
            loader.style.display = 'none';
        });
        
        // 確保 body 可以滾動
        document.body.style.overflow = 'auto';
        document.documentElement.style.overflow = 'auto';
        
        // 添加頁面載入完成的類
        document.body.classList.add('loaded');
        document.body.classList.remove('loading');
    }
    
    // 優雅地隱藏載入器
    function hideLoadersGracefully() {
        const pageLoader = document.getElementById('pageLoader');
        const loadingOverlay = document.getElementById('loadingOverlay');
        
        if (pageLoader) {
            pageLoader.style.opacity = '0';
            pageLoader.style.transition = 'opacity 0.3s ease';
            setTimeout(() => {
                pageLoader.style.display = 'none';
            }, 300);
        }
        
        if (loadingOverlay) {
            loadingOverlay.classList.add('fade-out');
            setTimeout(() => {
                loadingOverlay.style.display = 'none';
            }, 300);
        }
        
        // 確保 body 可以滾動
        document.body.style.overflow = 'auto';
        document.documentElement.style.overflow = 'auto';
        
        // 添加頁面載入完成的類
        document.body.classList.add('loaded');
        document.body.classList.remove('loading');
    }
    
    // DOM 載入完成時
    document.addEventListener('DOMContentLoaded', function() {
        // 設定安全計時器 - 無論如何都要在指定時間後隱藏載入器
        setTimeout(forceHideAllLoaders, MAX_LOADING_TIME);
    });
    
    // 頁面完全載入時
    window.addEventListener('load', function() {
        // 短暫延遲後優雅地隱藏載入器
        setTimeout(hideLoadersGracefully, 300);
    });
    
    // 處理頁面可見性變化（從其他標籤頁切換回來）
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            // 頁面變為可見時，檢查並隱藏載入器
            setTimeout(forceHideAllLoaders, 500);
        }
    });
    
    // 處理瀏覽器前進/後退
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            // 從快取載入頁面時
            forceHideAllLoaders();
        }
    });
    
    // 攔截所有連結點擊，防止重複顯示載入器
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a');
        if (link && link.href && !link.target && !link.download) {
            // 內部連結
            const url = new URL(link.href);
            if (url.origin === window.location.origin) {
                // 同源連結，添加標記防止顯示載入器過久
                sessionStorage.setItem('navigationTime', Date.now());
            }
        }
    });
    
    // 檢查是否是從內部導航過來的
    const navigationTime = sessionStorage.getItem('navigationTime');
    if (navigationTime) {
        const timeDiff = Date.now() - parseInt(navigationTime);
        if (timeDiff < 10000) { // 10秒內
            // 快速隱藏載入器
            setTimeout(forceHideAllLoaders, 100);
        }
        sessionStorage.removeItem('navigationTime');
    }
    
})();