/**
 * 3D角色配置檔案
 * 你可以在這裡自定義角色的各種參數
 * 
 * 注意：此文件暫時被註解，3D功能暫未啟用
 */

/*

window.CHARACTER_CONFIG = {
    // 基本設定
    model: {
        path: '/static/models/character.glb',  // GLB檔案路徑
        scale: 1.0,                            // 縮放比例
        position: { x: 0, y: -1, z: 0 },      // 初始位置
        rotation: { x: 0, y: 0, z: 0 }        // 初始旋轉
    },

    // 角色資訊
    info: {
        name: '小提琴助手',     // 角色名稱
        description: '你的練習夥伴'  // 角色描述
    },

    // 動畫設定
    animations: {
        idle: {
            name: 'idle',           // 待機動畫名稱
            loop: true,             // 是否循環
            speed: 1.0              // 播放速度
        },
        practice: {
            name: 'practice',       // 練習動畫名稱
            loop: true,
            speed: 1.0
        },
        celebrate: {
            name: 'celebrate',      // 慶祝動畫名稱
            loop: false,
            speed: 1.0,
            duration: 3000          // 持續時間(毫秒)
        },
        sad: {
            name: 'sad',           // 失望動畫名稱
            loop: false,
            speed: 1.0,
            duration: 2000
        }
    },

    // 相機設定
    camera: {
        position: { x: 0, y: 1, z: 3 },      // 相機位置
        target: { x: 0, y: 0, z: 0 },        // 相機目標
        fov: 45                                // 視野角度
    },

    // 光照設定
    lighting: {
        ambient: {
            color: 0xffffff,        // 環境光顏色
            intensity: 0.6          // 環境光強度
        },
        directional: {
            color: 0xffffff,        // 主光源顏色
            intensity: 0.8,         // 主光源強度
            position: { x: 2, y: 4, z: 3 }
        },
        fill: {
            color: 0xffffff,        // 補光顏色
            intensity: 0.3,         // 補光強度
            position: { x: -2, y: 1, z: -1 }
        }
    },

    // 行為設定
    behavior: {
        autoRotate: true,           // 是否自動旋轉
        rotationSpeed: 0.005,       // 旋轉速度
        hoverEffect: true,          // 是否有懸浮效果
        clickInteraction: true      // 是否可點擊互動
    },

    // 狀態訊息
    statusMessages: {
        loading: '載入角色中...',
        ready: '準備完成！',
        practicing: '努力練習中...',
        completed: '練習完成！',
        error: '出現錯誤...',
        waiting: '等待角色檔案...'
    },

    // 音效設定（可選）
    sounds: {
        enabled: false,             // 是否啟用音效
        practice: '/static/sounds/practice.mp3',
        celebrate: '/static/sounds/celebrate.mp3',
        error: '/static/sounds/error.mp3'
    }
};

// 便利函數：獲取配置值
window.getCharacterConfig = function(path, defaultValue = null) {
    const keys = path.split('.');
    let current = window.CHARACTER_CONFIG;
    
    for (let key of keys) {
        if (current && typeof current === 'object' && key in current) {
            current = current[key];
        } else {
            return defaultValue;
        }
    }
    
    return current;
};

// 便利函數：設置配置值
window.setCharacterConfig = function(path, value) {
    const keys = path.split('.');
    const lastKey = keys.pop();
    let current = window.CHARACTER_CONFIG;
    
    for (let key of keys) {
        if (!(key in current) || typeof current[key] !== 'object') {
            current[key] = {};
        }
        current = current[key];
    }
    
    current[lastKey] = value;
};

console.log('✅ 角色配置已載入:', window.CHARACTER_CONFIG);

*/

// 暫時禁用3D功能時的替代配置
window.CHARACTER_CONFIG = {
    disabled: true,
    message: '3D角色功能暫時禁用'
};

// 空的輔助函數
window.getCharacterConfig = function(path, defaultValue) {
    return defaultValue;
};

window.setCharacterConfig = function(path, value) {
    console.log('3D配置設置已跳過:', path, value);
};

console.log('⚠️ 3D角色功能暫時禁用');