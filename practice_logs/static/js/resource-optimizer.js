/**
 * 前端資源優化器
 * 處理延遲載入、資源預載、圖片優化等
 */

(function() {
    'use strict';
    
    // 資源優化器類別
    class ResourceOptimizer {
        constructor() {
            this.lazyImages = [];
            this.preloadQueue = [];
            this.cachedResources = new Map();
            this.performanceMetrics = {};
            
            this.init();
        }
        
        init() {
            // 監聽 DOM 載入完成
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
            } else {
                this.onDOMReady();
            }
            
            // 監聽頁面完全載入
            window.addEventListener('load', () => this.onPageLoad());
        }
        
        onDOMReady() {
            // 初始化延遲載入
            this.initLazyLoading();
            
            // 優化圖片
            this.optimizeImages();
            
            // 預載關鍵資源
            this.preloadCriticalResources();
            
            // 延遲載入非關鍵 CSS
            this.deferNonCriticalCSS();
            
            // 優化第三方腳本
            this.optimizeThirdPartyScripts();
        }
        
        onPageLoad() {
            // 收集效能指標
            this.collectPerformanceMetrics();
            
            // 預載下一頁可能需要的資源
            this.prefetchNextPageResources();
        }
        
        /**
         * 初始化圖片延遲載入
         */
        initLazyLoading() {
            // 使用 Intersection Observer API
            if ('IntersectionObserver' in window) {
                const imageObserver = new IntersectionObserver((entries, observer) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            this.loadImage(img);
                            observer.unobserve(img);
                        }
                    });
                }, {
                    rootMargin: '50px' // 提前 50px 開始載入
                });
                
                // 找出所有需要延遲載入的圖片
                document.querySelectorAll('img[data-src]').forEach(img => {
                    imageObserver.observe(img);
                    this.lazyImages.push(img);
                });
                
                // 延遲載入背景圖片
                document.querySelectorAll('[data-bg-src]').forEach(element => {
                    imageObserver.observe(element);
                });
            } else {
                // 降級方案：滾動時載入
                this.fallbackLazyLoad();
            }
        }
        
        /**
         * 載入圖片
         */
        loadImage(img) {
            const src = img.dataset.src;
            const srcset = img.dataset.srcset;
            
            if (src) {
                // 預載圖片
                const tempImg = new Image();
                tempImg.onload = () => {
                    img.src = src;
                    if (srcset) {
                        img.srcset = srcset;
                    }
                    img.classList.add('loaded');
                    
                    // 移除 data 屬性
                    delete img.dataset.src;
                    delete img.dataset.srcset;
                };
                tempImg.src = src;
            }
            
            // 處理背景圖片
            const bgSrc = img.dataset.bgSrc;
            if (bgSrc) {
                img.style.backgroundImage = `url(${bgSrc})`;
                img.classList.add('bg-loaded');
                delete img.dataset.bgSrc;
            }
        }
        
        /**
         * 降級的延遲載入方案
         */
        fallbackLazyLoad() {
            let throttleTimer;
            const throttle = (callback, time) => {
                if (throttleTimer) return;
                throttleTimer = true;
                setTimeout(() => {
                    callback();
                    throttleTimer = false;
                }, time);
            };
            
            const lazyLoad = () => {
                this.lazyImages.forEach(img => {
                    if (this.isInViewport(img)) {
                        this.loadImage(img);
                        this.lazyImages = this.lazyImages.filter(i => i !== img);
                    }
                });
            };
            
            window.addEventListener('scroll', () => throttle(lazyLoad, 20));
            window.addEventListener('resize', () => throttle(lazyLoad, 20));
            
            // 初始檢查
            lazyLoad();
        }
        
        /**
         * 檢查元素是否在視窗內
         */
        isInViewport(element) {
            const rect = element.getBoundingClientRect();
            return (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                rect.right <= (window.innerWidth || document.documentElement.clientWidth)
            );
        }
        
        /**
         * 優化圖片格式和大小
         */
        optimizeImages() {
            // 支援 WebP 格式檢測
            const supportsWebP = this.checkWebPSupport();
            
            if (supportsWebP) {
                document.querySelectorAll('img[data-webp]').forEach(img => {
                    const webpSrc = img.dataset.webp;
                    if (webpSrc) {
                        img.src = webpSrc;
                    }
                });
            }
            
            // 根據設備像素比載入適當大小的圖片
            const dpr = window.devicePixelRatio || 1;
            document.querySelectorAll('img[data-src-2x]').forEach(img => {
                if (dpr > 1.5 && img.dataset.src2x) {
                    img.dataset.src = img.dataset.src2x;
                }
            });
        }
        
        /**
         * 檢查 WebP 支援
         */
        checkWebPSupport() {
            const canvas = document.createElement('canvas');
            canvas.width = canvas.height = 1;
            return canvas.toDataURL('image/webp').indexOf('image/webp') === 0;
        }
        
        /**
         * 預載關鍵資源
         */
        preloadCriticalResources() {
            // 預載字體
            const fonts = [
                '/static/fonts/NotoSansTC-Regular.woff2',
                '/static/fonts/NotoSansTC-Medium.woff2'
            ];
            
            fonts.forEach(font => {
                const link = document.createElement('link');
                link.rel = 'preload';
                link.as = 'font';
                link.type = 'font/woff2';
                link.crossOrigin = 'anonymous';
                link.href = font;
                document.head.appendChild(link);
            });
            
            // 預載關鍵 CSS
            const criticalCSS = [
                '/static/css/critical.css'
            ];
            
            criticalCSS.forEach(css => {
                const link = document.createElement('link');
                link.rel = 'preload';
                link.as = 'style';
                link.href = css;
                document.head.appendChild(link);
            });
        }
        
        /**
         * 延遲載入非關鍵 CSS
         */
        deferNonCriticalCSS() {
            // 找出所有標記為延遲的樣式表
            document.querySelectorAll('link[data-defer]').forEach(link => {
                // 改為 print 媒體類型，避免阻塞渲染
                link.media = 'print';
                
                // 載入完成後改回 all
                link.onload = function() {
                    this.media = 'all';
                };
            });
        }
        
        /**
         * 優化第三方腳本載入
         */
        optimizeThirdPartyScripts() {
            // 延遲載入分析腳本
            setTimeout(() => {
                // Google Analytics
                if (window.GA_TRACKING_ID) {
                    const script = document.createElement('script');
                    script.async = true;
                    script.src = `https://www.googletagmanager.com/gtag/js?id=${window.GA_TRACKING_ID}`;
                    document.head.appendChild(script);
                }
            }, 3000);
            
            // 使用 requestIdleCallback 載入非關鍵腳本
            if ('requestIdleCallback' in window) {
                requestIdleCallback(() => {
                    this.loadNonCriticalScripts();
                });
            } else {
                setTimeout(() => {
                    this.loadNonCriticalScripts();
                }, 2000);
            }
        }
        
        /**
         * 載入非關鍵腳本
         */
        loadNonCriticalScripts() {
            // 社交媒體分享按鈕
            // 聊天小工具
            // 其他第三方整合
        }
        
        /**
         * 預取下一頁資源
         */
        prefetchNextPageResources() {
            // 找出可能的下一頁連結
            const nextPageLinks = document.querySelectorAll(
                'a[href^="/my-practices/"], a[href^="/analytics/"], .pagination a'
            );
            
            nextPageLinks.forEach(link => {
                // 使用 prefetch 提示
                const prefetchLink = document.createElement('link');
                prefetchLink.rel = 'prefetch';
                prefetchLink.href = link.href;
                document.head.appendChild(prefetchLink);
            });
        }
        
        /**
         * 收集效能指標
         */
        collectPerformanceMetrics() {
            if ('performance' in window) {
                const perfData = window.performance.timing;
                const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
                const domReadyTime = perfData.domContentLoadedEventEnd - perfData.navigationStart;
                const resourceLoadTime = perfData.loadEventEnd - perfData.responseEnd;
                
                this.performanceMetrics = {
                    pageLoadTime,
                    domReadyTime,
                    resourceLoadTime,
                    // 其他指標
                };
                
                // 發送到分析服務（如果需要）
                console.log('Performance metrics:', this.performanceMetrics);
            }
        }
        
        /**
         * 資源快取管理
         */
        cacheResource(url, data) {
            this.cachedResources.set(url, {
                data,
                timestamp: Date.now()
            });
            
            // 限制快取大小
            if (this.cachedResources.size > 50) {
                const oldestKey = this.cachedResources.keys().next().value;
                this.cachedResources.delete(oldestKey);
            }
        }
        
        getCachedResource(url, maxAge = 300000) { // 5分鐘
            const cached = this.cachedResources.get(url);
            if (cached && Date.now() - cached.timestamp < maxAge) {
                return cached.data;
            }
            return null;
        }
    }
    
    // 初始化資源優化器
    window.resourceOptimizer = new ResourceOptimizer();
    
    // 暴露公共 API
    window.ResourceOptimizer = {
        // 手動觸發延遲載入
        lazyLoad: () => window.resourceOptimizer.initLazyLoading(),
        
        // 預載資源
        preload: (url, type) => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = type;
            link.href = url;
            document.head.appendChild(link);
        },
        
        // 獲取效能指標
        getMetrics: () => window.resourceOptimizer.performanceMetrics
    };
    
})();