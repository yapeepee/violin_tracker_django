/**
 * 優化的小提琴練習追蹤系統前端代碼
 * 包含性能優化、快取策略和錯誤處理
 */

// 全局命名空間
window.ViolinTracker = window.ViolinTracker || {};

(function(VT) {
    'use strict';

    // ===== 配置 =====
    VT.config = {
        apiTimeout: 10000,
        cacheExpiry: 300000, // 5分鐘
        debounceDelay: 300,
        lazyLoadOffset: 100,
        maxRetries: 3
    };

    // ===== 工具函數 =====
    VT.utils = {
        // 防抖函數
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // 節流函數
        throttle: function(func, limit) {
            let inThrottle;
            return function(...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },

        // 格式化日期
        formatDate: function(date) {
            const d = new Date(date);
            return d.toLocaleDateString('zh-TW', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            });
        },

        // 格式化時間
        formatDuration: function(minutes) {
            if (minutes < 60) {
                return `${minutes} 分鐘`;
            }
            const hours = Math.floor(minutes / 60);
            const mins = minutes % 60;
            return mins > 0 ? `${hours} 小時 ${mins} 分鐘` : `${hours} 小時`;
        },

        // 顯示提示訊息
        showNotification: function(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            // 動畫顯示
            requestAnimationFrame(() => {
                notification.classList.add('show');
            });
            
            // 3秒後移除
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }
    };

    // ===== 快取管理 =====
    VT.cache = {
        storage: new Map(),

        set: function(key, value, expiry = VT.config.cacheExpiry) {
            this.storage.set(key, {
                value: value,
                expiry: Date.now() + expiry
            });
        },

        get: function(key) {
            const item = this.storage.get(key);
            if (!item) return null;
            
            if (Date.now() > item.expiry) {
                this.storage.delete(key);
                return null;
            }
            
            return item.value;
        },

        clear: function(pattern) {
            if (!pattern) {
                this.storage.clear();
                return;
            }
            
            for (const key of this.storage.keys()) {
                if (key.includes(pattern)) {
                    this.storage.delete(key);
                }
            }
        }
    };

    // ===== API 管理 =====
    VT.api = {
        // 基礎請求函數
        request: async function(url, options = {}) {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), VT.config.apiTimeout);

            try {
                const response = await fetch(url, {
                    ...options,
                    signal: controller.signal,
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        ...options.headers
                    }
                });

                clearTimeout(timeoutId);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                return await response.json();
            } catch (error) {
                if (error.name === 'AbortError') {
                    throw new Error('請求超時');
                }
                throw error;
            }
        },

        // 獲取練習數據
        getPracticeData: async function(studentName, days = 30) {
            const cacheKey = `practice_data:${studentName}:${days}`;
            const cached = VT.cache.get(cacheKey);
            
            if (cached) {
                return cached;
            }

            const data = await this.request(`/api/practice-data/?student_name=${encodeURIComponent(studentName)}&days=${days}`);
            VT.cache.set(cacheKey, data);
            return data;
        },

        // 添加練習記錄
        addPracticeLog: async function(logData) {
            const response = await this.request('/api/add-log/', {
                method: 'POST',
                body: JSON.stringify(logData),
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            // 清除相關快取
            VT.cache.clear(`practice_data:${logData.student_name}`);
            
            return response;
        },

        // 獲取 CSRF Token
        getCSRFToken: function() {
            const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
            return cookie ? cookie.split('=')[1] : '';
        }
    };

    // ===== 圖表管理 =====
    VT.charts = {
        instances: new Map(),

        // 創建或更新圖表
        createOrUpdate: function(canvasId, config) {
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;

            const ctx = canvas.getContext('2d');
            
            // 如果圖表已存在，更新數據
            if (this.instances.has(canvasId)) {
                const chart = this.instances.get(canvasId);
                chart.data = config.data;
                chart.update('active');
                return chart;
            }

            // 創建新圖表
            const chart = new Chart(ctx, {
                ...config,
                options: {
                    ...config.options,
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 500
                    }
                }
            });

            this.instances.set(canvasId, chart);
            return chart;
        },

        // 銷毀圖表
        destroy: function(canvasId) {
            if (this.instances.has(canvasId)) {
                this.instances.get(canvasId).destroy();
                this.instances.delete(canvasId);
            }
        },

        // 銷毀所有圖表
        destroyAll: function() {
            this.instances.forEach(chart => chart.destroy());
            this.instances.clear();
        }
    };

    // ===== 表單處理 =====
    VT.forms = {
        // 初始化表單
        init: function() {
            this.attachEventListeners();
            this.initializeValidation();
        },

        // 附加事件監聽器
        attachEventListeners: function() {
            // 練習記錄表單
            const practiceForm = document.getElementById('practice-form');
            if (practiceForm) {
                practiceForm.addEventListener('submit', this.handlePracticeFormSubmit.bind(this));
            }

            // 自動保存草稿
            document.querySelectorAll('.auto-save').forEach(input => {
                input.addEventListener('input', VT.utils.debounce(() => {
                    this.saveDraft(input);
                }, 1000));
            });
        },

        // 處理練習表單提交
        handlePracticeFormSubmit: async function(e) {
            e.preventDefault();
            
            const form = e.target;
            const submitBtn = form.querySelector('button[type="submit"]');
            
            // 禁用提交按鈕
            submitBtn.disabled = true;
            submitBtn.textContent = '提交中...';

            try {
                const formData = new FormData(form);
                const data = Object.fromEntries(formData);
                
                // 驗證數據
                if (!this.validatePracticeData(data)) {
                    throw new Error('請填寫所有必填欄位');
                }

                // 提交數據
                const response = await VT.api.addPracticeLog(data);
                
                if (response.success) {
                    VT.utils.showNotification('練習記錄已成功添加！', 'success');
                    form.reset();
                    this.clearDraft();
                    
                    // 更新頁面數據
                    if (typeof updateDashboard === 'function') {
                        updateDashboard(data.student_name);
                    }
                } else {
                    throw new Error(response.error || '提交失敗');
                }
            } catch (error) {
                VT.utils.showNotification(error.message, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = '提交';
            }
        },

        // 驗證練習數據
        validatePracticeData: function(data) {
            const required = ['student_name', 'piece', 'minutes', 'rating'];
            
            for (const field of required) {
                if (!data[field] || data[field].trim() === '') {
                    this.showFieldError(field, '此欄位為必填');
                    return false;
                }
            }

            // 驗證數字範圍
            if (data.minutes < 1 || data.minutes > 600) {
                this.showFieldError('minutes', '練習時間必須在 1-600 分鐘之間');
                return false;
            }

            if (data.rating < 1 || data.rating > 5) {
                this.showFieldError('rating', '評分必須在 1-5 之間');
                return false;
            }

            return true;
        },

        // 顯示欄位錯誤
        showFieldError: function(fieldName, message) {
            const field = document.querySelector(`[name="${fieldName}"]`);
            if (!field) return;

            field.classList.add('error');
            
            // 顯示錯誤訊息
            let errorEl = field.parentElement.querySelector('.field-error');
            if (!errorEl) {
                errorEl = document.createElement('div');
                errorEl.className = 'field-error';
                field.parentElement.appendChild(errorEl);
            }
            errorEl.textContent = message;

            // 3秒後移除錯誤
            setTimeout(() => {
                field.classList.remove('error');
                errorEl.remove();
            }, 3000);
        },

        // 保存草稿
        saveDraft: function(input) {
            const formData = {};
            const form = input.closest('form');
            
            form.querySelectorAll('input, textarea, select').forEach(field => {
                if (field.name) {
                    formData[field.name] = field.value;
                }
            });

            localStorage.setItem('practice_draft', JSON.stringify(formData));
            VT.utils.showNotification('草稿已自動保存', 'info');
        },

        // 載入草稿
        loadDraft: function() {
            const draft = localStorage.getItem('practice_draft');
            if (!draft) return;

            try {
                const data = JSON.parse(draft);
                Object.keys(data).forEach(key => {
                    const field = document.querySelector(`[name="${key}"]`);
                    if (field) {
                        field.value = data[key];
                    }
                });
                VT.utils.showNotification('已載入上次的草稿', 'info');
            } catch (error) {
                console.error('載入草稿失敗:', error);
            }
        },

        // 清除草稿
        clearDraft: function() {
            localStorage.removeItem('practice_draft');
        },

        // 初始化表單驗證
        initializeValidation: function() {
            // HTML5 表單驗證增強
            document.querySelectorAll('form').forEach(form => {
                form.addEventListener('invalid', (e) => {
                    e.preventDefault();
                    this.showFieldError(e.target.name, e.target.validationMessage);
                }, true);
            });
        }
    };

    // ===== 延遲載入 =====
    VT.lazyLoad = {
        // 初始化延遲載入
        init: function() {
            if ('IntersectionObserver' in window) {
                this.initIntersectionObserver();
            } else {
                // 降級方案
                this.loadAllImages();
            }
        },

        // 使用 Intersection Observer
        initIntersectionObserver: function() {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.add('loaded');
                        observer.unobserve(img);
                    }
                });
            }, {
                rootMargin: `${VT.config.lazyLoadOffset}px`
            });

            // 觀察所有延遲載入圖片
            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        },

        // 載入所有圖片（降級方案）
        loadAllImages: function() {
            document.querySelectorAll('img[data-src]').forEach(img => {
                img.src = img.dataset.src;
                img.classList.add('loaded');
            });
        }
    };

    // ===== 性能監控 =====
    VT.performance = {
        // 記錄性能指標
        track: function(name, duration) {
            if (window.performance && window.performance.mark) {
                window.performance.mark(name);
            }
            
            // 發送到分析服務（如果需要）
            console.log(`Performance: ${name} took ${duration}ms`);
        },

        // 測量函數執行時間
        measure: function(fn, name) {
            return async function(...args) {
                const start = performance.now();
                try {
                    const result = await fn.apply(this, args);
                    const duration = performance.now() - start;
                    VT.performance.track(name, duration);
                    return result;
                } catch (error) {
                    const duration = performance.now() - start;
                    VT.performance.track(`${name}_error`, duration);
                    throw error;
                }
            };
        }
    };

    // ===== 初始化 =====
    VT.init = function() {
        // DOM 載入完成後初始化
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', this.onDOMReady.bind(this));
        } else {
            this.onDOMReady();
        }

        // 監聽頁面可見性變化
        document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
        
        // 監聽網絡狀態
        window.addEventListener('online', () => VT.utils.showNotification('已恢復網絡連接', 'success'));
        window.addEventListener('offline', () => VT.utils.showNotification('網絡連接已斷開', 'error'));
    };

    // DOM 準備完成
    VT.onDOMReady = function() {
        console.log('ViolinTracker initialized');
        
        // 初始化各模組
        this.forms.init();
        this.lazyLoad.init();
        
        // 載入草稿
        this.forms.loadDraft();
        
        // 初始化頁面特定功能
        this.initPageSpecific();
    };

    // 初始化頁面特定功能
    VT.initPageSpecific = function() {
        const page = document.body.dataset.page;
        
        switch (page) {
            case 'analytics':
                this.initAnalyticsPage();
                break;
            case 'practice-form':
                this.initPracticeForm();
                break;
            case 'dashboard':
                this.initDashboard();
                break;
        }
    };

    // 處理頁面可見性變化
    VT.handleVisibilityChange = function() {
        if (document.hidden) {
            // 頁面隱藏時暫停更新
            this.pauseUpdates();
        } else {
            // 頁面顯示時恢復更新
            this.resumeUpdates();
        }
    };

    // 暫停更新
    VT.pauseUpdates = function() {
        // 清除定時器等
    };

    // 恢復更新
    VT.resumeUpdates = function() {
        // 重新載入數據等
    };

    // 啟動應用
    VT.init();

})(window.ViolinTracker);

// ===== 全局錯誤處理 =====
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    ViolinTracker.utils.showNotification('發生錯誤，請重新整理頁面', 'error');
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    ViolinTracker.utils.showNotification('操作失敗，請稍後再試', 'error');
});