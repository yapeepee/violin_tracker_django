/**
 * 安全的頁面轉場效果
 * 修復瀏覽器前進/後退的問題
 */

// 覆寫原有的 PageTransition 類別
window.PageTransition = class SafePageTransition {
    constructor() {
        // 檢查是否應該啟用轉場效果
        this.enabled = this.shouldEnableTransitions();
        if (this.enabled) {
            this.init();
        }
    }
    
    shouldEnableTransitions() {
        // 檢查是否通過瀏覽器前進/後退到達
        if (performance && performance.navigation) {
            if (performance.navigation.type === 2) {
                return false;
            }
        }
        
        // 檢查 sessionStorage 標記
        const disableTransitions = sessionStorage.getItem('disableTransitions');
        if (disableTransitions === 'true') {
            return false;
        }
        
        return true;
    }
    
    init() {
        // 只為新點擊的連結添加轉場效果
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href^="/"]');
            if (link && !link.hasAttribute('download') && !link.hasAttribute('target')) {
                this.handleTransition(e, link);
            }
        }, true);
        
        // 監聽瀏覽器前進/後退
        window.addEventListener('popstate', () => {
            sessionStorage.setItem('disableTransitions', 'true');
        });
    }
    
    handleTransition(e, link) {
        const href = link.getAttribute('href');
        
        // 標記為正常導航
        sessionStorage.setItem('normalNavigation', 'true');
        sessionStorage.removeItem('disableTransitions');
        
        // 如果是錨點連結，不處理
        if (href.startsWith('#')) {
            return;
        }
        
        e.preventDefault();
        
        // 創建轉場效果
        this.createTransitionEffect(() => {
            window.location.href = href;
        });
    }
    
    createTransitionEffect(callback) {
        // 檢查是否已經有轉場效果
        if (document.querySelector('.page-transition-overlay')) {
            callback();
            return;
        }
        
        const transition = document.createElement('div');
        transition.className = 'page-transition-overlay';
        transition.innerHTML = `
            <div class="transition-content">
                <div class="music-wave">
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                </div>
            </div>
        `;
        
        document.body.appendChild(transition);
        
        // 添加自動清理機制
        const cleanup = () => {
            if (transition && transition.parentNode) {
                transition.remove();
            }
        };
        
        // 設定多個清理時機
        setTimeout(cleanup, 2000); // 2秒後強制清理
        window.addEventListener('pagehide', cleanup);
        window.addEventListener('beforeunload', cleanup);
        
        setTimeout(() => {
            transition.classList.add('active');
            setTimeout(() => {
                callback();
                // 導航後再次清理
                setTimeout(cleanup, 100);
            }, 500);
        }, 10);
    }
};

// 初始化時清理任何遺留的轉場效果
document.addEventListener('DOMContentLoaded', function() {
    // 清理所有轉場元素
    document.querySelectorAll('.page-transition-overlay').forEach(el => el.remove());
    
    // 如果是從其他頁面返回，禁用轉場效果一段時間
    if (sessionStorage.getItem('normalNavigation') !== 'true') {
        sessionStorage.setItem('disableTransitions', 'true');
        setTimeout(() => {
            sessionStorage.removeItem('disableTransitions');
        }, 1000);
    }
    sessionStorage.removeItem('normalNavigation');
});