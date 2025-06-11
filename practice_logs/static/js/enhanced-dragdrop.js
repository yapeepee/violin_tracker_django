/**
 * Enhanced Drag and Drop System for Student Management
 * 提供進階拖放功能、視覺回饋、自動保存和撤銷功能
 */

class EnhancedDragDrop {
    constructor() {
        this.draggedElement = null;
        this.dropTargets = [];
        this.history = [];
        this.maxHistory = 20;
        this.autoSaveTimer = null;
        this.isDragging = false;
        this.init();
    }

    init() {
        this.setupDragAndDrop();
        this.setupKeyboardShortcuts();
        this.setupTouchSupport();
        this.createDragIndicator();
        this.createUndoRedoButtons();
    }

    setupDragAndDrop() {
        // 設置可拖動元素
        document.querySelectorAll('.student-card').forEach(card => {
            card.draggable = true;
            card.addEventListener('dragstart', (e) => this.handleDragStart(e));
            card.addEventListener('dragend', (e) => this.handleDragEnd(e));
            card.addEventListener('dragenter', (e) => this.handleDragEnter(e));
            
            // 添加拖動手柄
            const handle = document.createElement('div');
            handle.className = 'drag-handle';
            handle.innerHTML = '<i class="fas fa-grip-vertical"></i>';
            card.insertBefore(handle, card.firstChild);
        });

        // 設置放置區域
        document.querySelectorAll('.drop-zone').forEach(zone => {
            zone.addEventListener('dragover', (e) => this.handleDragOver(e));
            zone.addEventListener('drop', (e) => this.handleDrop(e));
            zone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
            zone.addEventListener('dragenter', (e) => this.handleDragEnter(e));
        });
    }

    handleDragStart(e) {
        this.isDragging = true;
        this.draggedElement = e.target.closest('.student-card');
        
        // 記錄原始位置
        this.originalParent = this.draggedElement.parentElement;
        this.originalNextSibling = this.draggedElement.nextSibling;
        
        // 設置拖動效果
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setDragImage(this.createDragImage(this.draggedElement), 50, 50);
        
        // 添加拖動樣式
        this.draggedElement.classList.add('dragging');
        document.body.classList.add('dragging-active');
        
        // 顯示可放置區域
        this.highlightDropZones();
        
        // 發送開始拖動事件
        this.emit('dragstart', { element: this.draggedElement });
    }

    handleDragEnd(e) {
        this.isDragging = false;
        
        // 移除拖動樣式
        if (this.draggedElement) {
            this.draggedElement.classList.remove('dragging');
        }
        document.body.classList.remove('dragging-active');
        
        // 清除高亮
        this.clearHighlights();
        
        // 重置狀態
        this.draggedElement = null;
        
        // 發送結束拖動事件
        this.emit('dragend', {});
    }

    handleDragOver(e) {
        if (!this.isDragging) return;
        
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        
        const dropZone = e.currentTarget;
        const afterElement = this.getDragAfterElement(dropZone, e.clientY);
        
        if (afterElement == null) {
            dropZone.appendChild(this.createPlaceholder());
        } else {
            dropZone.insertBefore(this.createPlaceholder(), afterElement);
        }
        
        // 添加視覺反饋
        dropZone.classList.add('drag-over');
        this.updateDropIndicator(e);
    }

    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const dropZone = e.currentTarget;
        dropZone.classList.remove('drag-over');
        
        // 移除佔位符
        const placeholder = dropZone.querySelector('.drag-placeholder');
        if (placeholder) {
            placeholder.remove();
        }
        
        if (this.draggedElement && dropZone !== this.originalParent) {
            // 移除空狀態提示
            const emptyGroup = dropZone.querySelector('.empty-group');
            if (emptyGroup) {
                emptyGroup.remove();
            }
            
            // 獲取放置位置
            const afterElement = this.getDragAfterElement(dropZone, e.clientY);
            
            // 記錄操作到歷史
            this.addToHistory({
                element: this.draggedElement,
                fromParent: this.originalParent,
                toParent: dropZone,
                fromNextSibling: this.originalNextSibling,
                toNextSibling: afterElement
            });
            
            // 執行移動
            if (afterElement == null) {
                dropZone.appendChild(this.draggedElement);
            } else {
                dropZone.insertBefore(this.draggedElement, afterElement);
            }
            
            // 更新服務器
            this.updateServer(this.draggedElement, dropZone);
            
            // 添加動畫
            this.animateMove(this.draggedElement);
            
            // 發送放置事件
            this.emit('drop', {
                element: this.draggedElement,
                from: this.originalParent,
                to: dropZone
            });
        }
    }

    handleDragEnter(e) {
        if (!this.isDragging) return;
        
        const dropZone = e.currentTarget;
        if (dropZone.classList.contains('drop-zone')) {
            dropZone.classList.add('drag-enter');
        }
    }

    handleDragLeave(e) {
        const dropZone = e.currentTarget;
        dropZone.classList.remove('drag-enter', 'drag-over');
        
        // 移除佔位符
        const placeholder = dropZone.querySelector('.drag-placeholder');
        if (placeholder) {
            placeholder.remove();
        }
    }

    // 獲取拖動後的位置
    getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.student-card:not(.dragging)')];
        
        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    // 創建拖動圖像
    createDragImage(element) {
        const dragImage = element.cloneNode(true);
        dragImage.style.position = 'absolute';
        dragImage.style.top = '-1000px';
        dragImage.style.opacity = '0.8';
        dragImage.style.transform = 'rotate(3deg)';
        document.body.appendChild(dragImage);
        
        setTimeout(() => dragImage.remove(), 0);
        
        return dragImage;
    }

    // 創建佔位符
    createPlaceholder() {
        const existing = document.querySelector('.drag-placeholder');
        if (existing) existing.remove();
        
        const placeholder = document.createElement('div');
        placeholder.className = 'drag-placeholder';
        placeholder.style.height = this.draggedElement.offsetHeight + 'px';
        placeholder.style.margin = window.getComputedStyle(this.draggedElement).margin;
        placeholder.style.border = '2px dashed #4A90E2';
        placeholder.style.borderRadius = '10px';
        placeholder.style.background = 'rgba(74, 144, 226, 0.1)';
        placeholder.style.transition = 'all 0.3s ease';
        
        return placeholder;
    }

    // 高亮可放置區域
    highlightDropZones() {
        document.querySelectorAll('.drop-zone').forEach(zone => {
            if (zone !== this.draggedElement.parentElement) {
                zone.classList.add('drop-available');
            }
        });
    }

    // 清除高亮
    clearHighlights() {
        document.querySelectorAll('.drop-zone').forEach(zone => {
            zone.classList.remove('drop-available', 'drag-over', 'drag-enter');
        });
        
        // 移除所有佔位符
        document.querySelectorAll('.drag-placeholder').forEach(p => p.remove());
    }

    // 創建拖動指示器
    createDragIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'drag-indicator';
        indicator.className = 'drag-indicator';
        indicator.style.display = 'none';
        indicator.innerHTML = '<i class="fas fa-arrows-alt"></i>';
        document.body.appendChild(indicator);
        
        document.addEventListener('dragover', (e) => {
            if (this.isDragging) {
                indicator.style.display = 'block';
                indicator.style.left = e.clientX + 10 + 'px';
                indicator.style.top = e.clientY + 10 + 'px';
            }
        });
        
        document.addEventListener('dragend', () => {
            indicator.style.display = 'none';
        });
    }

    // 更新放置指示器
    updateDropIndicator(e) {
        const indicator = document.getElementById('drag-indicator');
        if (indicator) {
            indicator.style.left = e.clientX + 10 + 'px';
            indicator.style.top = e.clientY + 10 + 'px';
        }
    }

    // 添加移動動畫
    animateMove(element) {
        element.style.animation = 'dropIn 0.4s ease-out';
        
        element.addEventListener('animationend', () => {
            element.style.animation = '';
        }, { once: true });
    }

    // 更新服務器
    async updateServer(element, newParent) {
        const studentId = element.dataset.studentId;
        const newGroup = newParent.dataset.group;
        
        // 顯示保存指示器
        this.showSaveIndicator();
        
        try {
            const response = await fetch('/api/teacher/update-student-group/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    student_id: studentId,
                    group: newGroup
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('已成功移動學生', 'success');
            } else {
                this.showNotification(data.error || '移動失敗', 'error');
                // 恢復原位
                this.revertMove();
            }
        } catch (error) {
            console.error('Error updating student group:', error);
            this.showNotification('網絡錯誤，請稍後再試', 'error');
            this.revertMove();
        }
        
        this.hideSaveIndicator();
    }

    // 歷史記錄管理
    addToHistory(action) {
        this.history.push(action);
        if (this.history.length > this.maxHistory) {
            this.history.shift();
        }
        this.updateUndoRedoButtons();
    }

    undo() {
        if (this.history.length === 0) return;
        
        const lastAction = this.history.pop();
        const { element, fromParent, fromNextSibling } = lastAction;
        
        if (fromNextSibling) {
            fromParent.insertBefore(element, fromNextSibling);
        } else {
            fromParent.appendChild(element);
        }
        
        this.updateServer(element, fromParent);
        this.animateMove(element);
        this.updateUndoRedoButtons();
    }

    // 創建撤銷/重做按鈕
    createUndoRedoButtons() {
        const container = document.createElement('div');
        container.className = 'undo-redo-container';
        container.innerHTML = `
            <button id="undoBtn" class="undo-btn" title="撤銷 (Ctrl+Z)">
                <i class="fas fa-undo"></i>
            </button>
            <button id="redoBtn" class="redo-btn" title="重做 (Ctrl+Y)" disabled>
                <i class="fas fa-redo"></i>
            </button>
        `;
        
        document.querySelector('.toolbar-actions').appendChild(container);
        
        document.getElementById('undoBtn').addEventListener('click', () => this.undo());
        this.updateUndoRedoButtons();
    }

    updateUndoRedoButtons() {
        const undoBtn = document.getElementById('undoBtn');
        if (undoBtn) {
            undoBtn.disabled = this.history.length === 0;
        }
    }

    // 鍵盤快捷鍵
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                if (e.key === 'z') {
                    e.preventDefault();
                    this.undo();
                }
            }
        });
    }

    // 觸控支援
    setupTouchSupport() {
        let touchItem = null;
        let touchOffset = { x: 0, y: 0 };
        
        document.querySelectorAll('.student-card').forEach(card => {
            card.addEventListener('touchstart', (e) => {
                touchItem = e.target.closest('.student-card');
                const touch = e.touches[0];
                const rect = touchItem.getBoundingClientRect();
                touchOffset.x = touch.clientX - rect.left;
                touchOffset.y = touch.clientY - rect.top;
                
                touchItem.style.position = 'fixed';
                touchItem.style.zIndex = '1000';
                touchItem.style.opacity = '0.8';
                touchItem.classList.add('dragging');
            });
            
            card.addEventListener('touchmove', (e) => {
                if (!touchItem) return;
                e.preventDefault();
                
                const touch = e.touches[0];
                touchItem.style.left = (touch.clientX - touchOffset.x) + 'px';
                touchItem.style.top = (touch.clientY - touchOffset.y) + 'px';
                
                // 檢測放置目標
                const elementBelow = document.elementFromPoint(touch.clientX, touch.clientY);
                const dropZone = elementBelow?.closest('.drop-zone');
                
                if (dropZone && dropZone !== touchItem.parentElement) {
                    dropZone.classList.add('drag-over');
                }
            });
            
            card.addEventListener('touchend', (e) => {
                if (!touchItem) return;
                
                const touch = e.changedTouches[0];
                const elementBelow = document.elementFromPoint(touch.clientX, touch.clientY);
                const dropZone = elementBelow?.closest('.drop-zone');
                
                // 重置樣式
                touchItem.style.position = '';
                touchItem.style.zIndex = '';
                touchItem.style.opacity = '';
                touchItem.style.left = '';
                touchItem.style.top = '';
                touchItem.classList.remove('dragging');
                
                // 處理放置
                if (dropZone && dropZone !== touchItem.parentElement) {
                    dropZone.appendChild(touchItem);
                    this.updateServer(touchItem, dropZone);
                }
                
                touchItem = null;
                document.querySelectorAll('.drop-zone').forEach(zone => {
                    zone.classList.remove('drag-over');
                });
            });
        });
    }

    // 顯示保存指示器
    showSaveIndicator() {
        let indicator = document.getElementById('save-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'save-indicator';
            indicator.className = 'save-indicator';
            indicator.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 保存中...';
            document.body.appendChild(indicator);
        }
        indicator.style.display = 'block';
    }

    hideSaveIndicator() {
        const indicator = document.getElementById('save-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    // 顯示通知
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `drag-notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // 獲取Cookie
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // 事件發送器
    emit(eventName, data) {
        const event = new CustomEvent('dragdrop:' + eventName, { detail: data });
        document.dispatchEvent(event);
    }

    // 恢復移動
    revertMove() {
        if (this.originalParent && this.draggedElement) {
            if (this.originalNextSibling) {
                this.originalParent.insertBefore(this.draggedElement, this.originalNextSibling);
            } else {
                this.originalParent.appendChild(this.draggedElement);
            }
        }
    }
}

// CSS 動畫
const style = document.createElement('style');
style.textContent = `
    /* 拖動手柄 */
    .drag-handle {
        position: absolute;
        left: 5px;
        top: 50%;
        transform: translateY(-50%);
        color: #ccc;
        cursor: move;
        transition: color 0.3s ease;
    }
    
    .student-card:hover .drag-handle {
        color: #666;
    }
    
    /* 拖動中的元素 */
    .student-card.dragging {
        opacity: 0.5;
        transform: rotate(3deg);
        cursor: move;
    }
    
    /* 可放置區域 */
    .drop-zone.drop-available {
        background: rgba(74, 144, 226, 0.05);
        border-color: #4A90E2;
    }
    
    .drop-zone.drag-enter {
        background: rgba(74, 144, 226, 0.1);
        transform: scale(1.02);
    }
    
    /* 拖動指示器 */
    .drag-indicator {
        position: fixed;
        pointer-events: none;
        z-index: 10000;
        color: #4A90E2;
        font-size: 24px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* 保存指示器 */
    .save-indicator {
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        z-index: 10000;
        display: none;
    }
    
    /* 通知 */
    .drag-notification {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        z-index: 10000;
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .drag-notification.show {
        opacity: 1;
        transform: translateY(0);
    }
    
    .drag-notification.success {
        background: #4caf50;
        color: white;
    }
    
    .drag-notification.error {
        background: #f44336;
        color: white;
    }
    
    /* 撤銷/重做按鈕 */
    .undo-redo-container {
        display: inline-flex;
        gap: 5px;
    }
    
    .undo-btn, .redo-btn {
        padding: 8px 12px;
        border: 1px solid #e0e0e0;
        background: white;
        border-radius: 5px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .undo-btn:not(:disabled):hover,
    .redo-btn:not(:disabled):hover {
        background: #f5f5f5;
        border-color: #4A90E2;
        color: #4A90E2;
    }
    
    .undo-btn:disabled,
    .redo-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
    
    /* 放入動畫 */
    @keyframes dropIn {
        from {
            transform: scale(1.1);
            opacity: 0.8;
        }
        to {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    /* 拖動時的body樣式 */
    body.dragging-active {
        user-select: none;
    }
`;
document.head.appendChild(style);

// 初始化增強拖放系統
document.addEventListener('DOMContentLoaded', () => {
    window.enhancedDragDrop = new EnhancedDragDrop();
});