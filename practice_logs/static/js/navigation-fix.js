/**
 * 導航修復腳本
 * 解決瀏覽器前進/後退按鈕導致的載入問題
 */

(function() {
    'use strict';
    
    // 清除所有可能的載入元素和轉場效果
    function clearAllLoadingElements() {
        // 清除所有載入器
        const loadingSelectors = [
            '#pageLoader',
            '#loadingOverlay',
            '.unified-loader',
            '.loading-overlay',
            '.page-transition-overlay',
            '.loader',
            '.loading',
            '[class*="loading"]',
            '[class*="loader"]'
        ];
        
        loadingSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(element => {
                element.style.display = 'none';
                element.remove();
            });
        });
        
        // 確保 body 可以滾動
        document.body.style.overflow = '';
        document.body.style.pointerEvents = '';
        document.documentElement.style.overflow = '';
        
        // 移除可能的類別
        document.body.classList.remove('loading', 'transitioning', 'page-loading');
        document.body.classList.add('loaded', 'page-loaded');
    }
    
    // 禁用頁面轉場效果
    function disablePageTransitions() {
        // 覆寫 PageTransition 類別的方法
        if (typeof PageTransition !== 'undefined') {
            PageTransition.prototype.init = function() {
                console.log('PageTransition disabled for browser navigation');
            };
            PageTransition.prototype.handleLinkClick = function(e) {
                // 不做任何事，讓瀏覽器正常導航
            };
            PageTransition.prototype.createTransitionEffect = function(callback) {
                // 直接執行回調，不添加轉場效果
                if (callback) callback();
            };
        }
        
        // 移除所有現有的頁面轉場事件監聽器
        const links = document.querySelectorAll('a[href^="/"]');
        links.forEach(link => {
            // 克隆節點以移除所有事件監聽器
            const newLink = link.cloneNode(true);
            link.parentNode.replaceChild(newLink, link);
        });
    }
    
    // 處理瀏覽器的前進/後退
    window.addEventListener('pageshow', function(event) {
        // pageshow 事件在頁面顯示時觸發，包括從快取載入
        clearAllLoadingElements();
        
        if (event.persisted) {
            // 頁面從快取載入（bfcache）
            console.log('Page loaded from cache');
            disablePageTransitions();
        }
    });
    
    // 當頁面即將被隱藏時（導航到其他頁面）
    window.addEventListener('pagehide', function(event) {
        clearAllLoadingElements();
    });
    
    // 監聽 popstate 事件（瀏覽器前進/後退按鈕）
    window.addEventListener('popstate', function(event) {
        clearAllLoadingElements();
        disablePageTransitions();
    });
    
    // DOM 載入完成時
    document.addEventListener('DOMContentLoaded', function() {
        // 立即清除任何載入元素
        clearAllLoadingElements();
        
        // 檢查是否是通過瀏覽器前進/後退到達的
        if (performance && performance.navigation) {
            if (performance.navigation.type === 2) {
                // TYPE_BACK_FORWARD
                console.log('Page accessed via back/forward button');
                disablePageTransitions();
            }
        }
        
        // 現代瀏覽器的 Navigation API
        if ('navigation' in window && window.navigation) {
            const navEntry = performance.getEntriesByType('navigation')[0];
            if (navEntry && navEntry.type === 'back_forward') {
                console.log('Navigation type: back_forward');
                disablePageTransitions();
            }
        }
    });
    
    // 設定定時器作為最後的保護措施
    setTimeout(clearAllLoadingElements, 1000);
    setTimeout(clearAllLoadingElements, 2000);
    setTimeout(clearAllLoadingElements, 3000);
    
    // 監測並移除新添加的載入元素
    if ('MutationObserver' in window) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        if (node.classList && (
                            node.classList.contains('page-transition-overlay') ||
                            node.classList.contains('loading-overlay') ||
                            node.classList.contains('loader') ||
                            node.id === 'pageLoader'
                        )) {
                            // 如果是通過前進/後退導航，立即移除
                            if (performance && performance.navigation && performance.navigation.type === 2) {
                                node.remove();
                            }
                        }
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
})();