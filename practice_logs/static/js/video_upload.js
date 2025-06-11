/**
 * 🎥 影片上傳系統
 * 優雅的拖拽上傳，進度追蹤，縮圖生成
 */

class VideoUploadManager {
    constructor(config = {}) {
        this.config = {
            maxFileSize: 100 * 1024 * 1024, // 100MB
            allowedTypes: ['video/mp4', 'video/avi', 'video/mov', 'video/webm'],
            uploadEndpoint: '/api/practice-recordings/upload/',
            thumbnailEndpoint: '/api/generate-thumbnail/',
            chunkSize: 1024 * 1024, // 1MB chunks
            ...config
        };
        
        this.currentUploads = new Map();
        this.init();
    }

    init() {
        this.setupDropZones();
        this.setupFileInputs();
        this.setupProgressTracking();
    }

    /**
     * 設置拖拽上傳區域
     */
    setupDropZones() {
        document.querySelectorAll('.video-upload-area').forEach(dropZone => {
            this.initializeDropZone(dropZone);
        });
    }

    initializeDropZone(dropZone) {
        // 防止預設拖拽行為
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        // 視覺回饋
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('dragover');
                this.showDropHint(dropZone);
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('dragover');
                this.hideDropHint(dropZone);
            });
        });

        // 處理文件拖拽
        dropZone.addEventListener('drop', (e) => {
            const files = Array.from(e.dataTransfer.files);
            this.handleFiles(files, dropZone);
        });

        // 點擊上傳
        dropZone.addEventListener('click', () => {
            this.triggerFileSelect(dropZone);
        });
    }

    showDropHint(dropZone) {
        if (!dropZone.querySelector('.drop-hint')) {
            const hint = document.createElement('div');
            hint.className = 'drop-hint';
            hint.innerHTML = `
                <div class="drop-hint-content">
                    <div class="drop-icon">🎬</div>
                    <div class="drop-text">放開以上傳練習影片</div>
                </div>
            `;
            dropZone.appendChild(hint);
        }
    }

    hideDropHint(dropZone) {
        const hint = dropZone.querySelector('.drop-hint');
        if (hint) {
            hint.remove();
        }
    }

    triggerFileSelect(dropZone) {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = this.config.allowedTypes.join(',');
        input.multiple = false;
        
        input.onchange = (e) => {
            const files = Array.from(e.target.files);
            this.handleFiles(files, dropZone);
        };
        
        input.click();
    }

    /**
     * 文件處理
     */
    async handleFiles(files, dropZone) {
        for (const file of files) {
            if (this.validateFile(file)) {
                await this.processFile(file, dropZone);
            }
        }
    }

    validateFile(file) {
        // 檢查文件類型
        if (!this.config.allowedTypes.includes(file.type)) {
            this.showError(`不支援的文件格式: ${file.type}`);
            return false;
        }

        // 檢查文件大小
        if (file.size > this.config.maxFileSize) {
            this.showError(`文件過大: ${this.formatFileSize(file.size)}。最大允許: ${this.formatFileSize(this.config.maxFileSize)}`);
            return false;
        }

        return true;
    }

    async processFile(file, dropZone) {
        const uploadId = this.generateUploadId();
        
        try {
            // 創建上傳進度UI
            const progressContainer = this.createProgressUI(file, uploadId, dropZone);
            
            // 生成縮圖
            const thumbnail = await this.generateThumbnail(file);
            
            // 獲取影片資訊
            const videoInfo = await this.getVideoInfo(file);
            
            // 開始上傳
            const uploadResult = await this.uploadFile(file, uploadId, {
                thumbnail,
                ...videoInfo
            });
            
            // 更新UI
            this.onUploadSuccess(uploadResult, progressContainer);
            
        } catch (error) {
            console.error('Upload failed:', error);
            this.onUploadError(error, uploadId);
        }
    }

    createProgressUI(file, uploadId, container) {
        const progressContainer = document.createElement('div');
        progressContainer.className = 'upload-progress-container';
        progressContainer.id = `upload-${uploadId}`;
        
        progressContainer.innerHTML = `
            <div class="upload-preview">
                <div class="upload-thumbnail">
                    <div class="loading-spinner">🎵</div>
                </div>
                <div class="upload-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${this.formatFileSize(file.size)}</div>
                    <div class="upload-status">正在處理...</div>
                </div>
            </div>
            <div class="progress-classical">
                <div class="progress-bar-classical" style="width: 0%"></div>
            </div>
            <div class="upload-actions">
                <button class="btn-cancel" onclick="videoUpload.cancelUpload('${uploadId}')">
                    取消
                </button>
            </div>
        `;
        
        // 替換或添加到容器
        const existingProgress = container.querySelector('.upload-progress-container');
        if (existingProgress) {
            container.replaceChild(progressContainer, existingProgress);
        } else {
            container.appendChild(progressContainer);
        }
        
        this.currentUploads.set(uploadId, {
            file,
            container: progressContainer,
            cancelled: false
        });
        
        return progressContainer;
    }

    async generateThumbnail(file) {
        return new Promise((resolve) => {
            const video = document.createElement('video');
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            video.onloadedmetadata = () => {
                // 跳到影片的1/4處生成縮圖
                video.currentTime = video.duration * 0.25;
            };
            
            video.onseeked = () => {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0);
                
                canvas.toBlob((blob) => {
                    resolve(blob);
                }, 'image/jpeg', 0.8);
            };
            
            video.onerror = () => {
                resolve(null);
            };
            
            video.src = URL.createObjectURL(file);
        });
    }

    async getVideoInfo(file) {
        return new Promise((resolve) => {
            const video = document.createElement('video');
            
            video.onloadedmetadata = () => {
                resolve({
                    duration: video.duration,
                    width: video.videoWidth,
                    height: video.videoHeight,
                    size: file.size
                });
            };
            
            video.onerror = () => {
                resolve({
                    duration: null,
                    width: null,
                    height: null,
                    size: file.size
                });
            };
            
            video.src = URL.createObjectURL(file);
        });
    }

    async uploadFile(file, uploadId, metadata) {
        const formData = new FormData();
        formData.append('video_file', file);
        formData.append('metadata', JSON.stringify(metadata));
        
        if (metadata.thumbnail) {
            formData.append('thumbnail', metadata.thumbnail, 'thumbnail.jpg');
        }
        
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            const upload = this.currentUploads.get(uploadId);
            
            if (!upload || upload.cancelled) {
                reject(new Error('Upload cancelled'));
                return;
            }
            
            // 進度追蹤
            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    this.updateProgress(uploadId, percentComplete);
                }
            };
            
            xhr.onload = () => {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (e) {
                        reject(new Error('Invalid response format'));
                    }
                } else {
                    reject(new Error(`Upload failed: ${xhr.statusText}`));
                }
            };
            
            xhr.onerror = () => {
                reject(new Error('Network error during upload'));
            };
            
            xhr.open('POST', this.config.uploadEndpoint);
            
            // 添加CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            if (csrfToken) {
                xhr.setRequestHeader('X-CSRFToken', csrfToken);
            }
            
            xhr.send(formData);
            
            // 保存xhr以便取消
            upload.xhr = xhr;
        });
    }

    updateProgress(uploadId, percentage) {
        const upload = this.currentUploads.get(uploadId);
        if (!upload) return;
        
        const progressBar = upload.container.querySelector('.progress-bar-classical');
        const statusElement = upload.container.querySelector('.upload-status');
        
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
        }
        
        if (statusElement) {
            if (percentage < 100) {
                statusElement.textContent = `上傳中... ${Math.round(percentage)}%`;
            } else {
                statusElement.textContent = '處理中...';
            }
        }
        
        // 播放進度音效
        if (percentage % 25 === 0 && window.classicalAnimations) {
            window.classicalAnimations.playHoverSound();
        }
    }

    onUploadSuccess(result, progressContainer) {
        const statusElement = progressContainer.querySelector('.upload-status');
        const actionsElement = progressContainer.querySelector('.upload-actions');
        const thumbnailElement = progressContainer.querySelector('.upload-thumbnail');
        
        if (statusElement) {
            statusElement.innerHTML = '✅ 上傳完成！';
            statusElement.className = 'upload-status success';
        }
        
        if (actionsElement) {
            actionsElement.innerHTML = `
                <button class="btn-classical" onclick="window.location.reload()">
                    查看記錄
                </button>
            `;
        }
        
        // 顯示縮圖
        if (result.thumbnail_url && thumbnailElement) {
            thumbnailElement.innerHTML = `
                <img src="${result.thumbnail_url}" alt="Video thumbnail" class="thumbnail-preview">
                <div class="play-overlay">▶️</div>
            `;
        }
        
        // 播放成功音效
        if (window.classicalAnimations) {
            window.classicalAnimations.playSuccessChord();
        }
        
        // 顯示成功通知
        this.showSuccess('影片上傳成功！您可以繼續填寫練習記錄。');
    }

    onUploadError(error, uploadId) {
        const upload = this.currentUploads.get(uploadId);
        if (!upload) return;
        
        const statusElement = upload.container.querySelector('.upload-status');
        const actionsElement = upload.container.querySelector('.upload-actions');
        
        if (statusElement) {
            statusElement.innerHTML = `❌ 上傳失敗: ${error.message}`;
            statusElement.className = 'upload-status error';
        }
        
        if (actionsElement) {
            actionsElement.innerHTML = `
                <button class="btn-burgundy" onclick="videoUpload.retryUpload('${uploadId}')">
                    重試
                </button>
                <button class="btn-cancel" onclick="videoUpload.removeUpload('${uploadId}')">
                    移除
                </button>
            `;
        }
        
        this.showError(`上傳失敗: ${error.message}`);
    }

    /**
     * 控制方法
     */
    cancelUpload(uploadId) {
        const upload = this.currentUploads.get(uploadId);
        if (!upload) return;
        
        upload.cancelled = true;
        
        if (upload.xhr) {
            upload.xhr.abort();
        }
        
        this.removeUpload(uploadId);
    }

    removeUpload(uploadId) {
        const upload = this.currentUploads.get(uploadId);
        if (!upload) return;
        
        upload.container.remove();
        this.currentUploads.delete(uploadId);
    }

    retryUpload(uploadId) {
        const upload = this.currentUploads.get(uploadId);
        if (!upload) return;
        
        // 重置狀態
        upload.cancelled = false;
        
        // 重新開始上傳
        this.processFile(upload.file, upload.container.parentElement);
    }

    /**
     * 工具方法
     */
    generateUploadId() {
        return 'upload_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification-classical ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">
                    ${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}
                </span>
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // 添加到頁面
        let container = document.querySelector('.notifications-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notifications-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        
        container.appendChild(notification);
        
        // 自動消失
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'fadeOut 0.3s ease-in';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }

    /**
     * 設置文件輸入
     */
    setupFileInputs() {
        document.querySelectorAll('input[type="file"][accept*="video"]').forEach(input => {
            input.addEventListener('change', (e) => {
                const files = Array.from(e.target.files);
                const dropZone = input.closest('.video-upload-area') || 
                              document.querySelector('.video-upload-area');
                this.handleFiles(files, dropZone);
            });
        });
    }

    setupProgressTracking() {
        // 頁面卸載時清理
        window.addEventListener('beforeunload', () => {
            this.currentUploads.forEach((upload, uploadId) => {
                if (upload.xhr) {
                    upload.xhr.abort();
                }
            });
        });
    }
}

// 添加必要的CSS
const videoUploadStyles = `
    .drop-hint {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(184, 134, 11, 0.1);
        border: 3px dashed #B8860B;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10;
    }

    .drop-hint-content {
        text-align: center;
        color: #B8860B;
        font-family: 'Playfair Display', serif;
    }

    .drop-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        animation: bounce 1s infinite;
    }

    .drop-text {
        font-size: 1.2rem;
        font-weight: 600;
    }

    .upload-progress-container {
        background: #FDF5E6;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(184, 134, 11, 0.2);
    }

    .upload-preview {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .upload-thumbnail {
        width: 80px;
        height: 60px;
        background: #F4F1E8;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        overflow: hidden;
    }

    .loading-spinner {
        animation: spin 1s linear infinite;
        font-size: 1.5rem;
    }

    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .thumbnail-preview {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .play-overlay {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0, 0, 0, 0.7);
        border-radius: 50%;
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 0.8rem;
    }

    .upload-info {
        flex: 1;
    }

    .file-name {
        font-weight: 600;
        color: #722F37;
        margin-bottom: 0.25rem;
    }

    .file-size {
        color: #556B2F;
        font-size: 0.9rem;
        margin-bottom: 0.25rem;
    }

    .upload-status {
        font-size: 0.9rem;
        font-weight: 500;
    }

    .upload-status.success {
        color: #28a745;
    }

    .upload-status.error {
        color: #dc3545;
    }

    .upload-actions {
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
    }

    .btn-cancel {
        background: #6c757d;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.9rem;
    }

    .btn-cancel:hover {
        background: #5a6268;
    }

    .notification-content {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1rem;
    }

    .notification-close {
        background: none;
        border: none;
        font-size: 1.2rem;
        cursor: pointer;
        margin-left: auto;
        color: inherit;
        opacity: 0.7;
    }

    .notification-close:hover {
        opacity: 1;
    }
`;

// 注入樣式
const styleSheet = document.createElement('style');
styleSheet.textContent = videoUploadStyles;
document.head.appendChild(styleSheet);

// 全域實例
window.videoUpload = new VideoUploadManager();

// 導出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VideoUploadManager;
}