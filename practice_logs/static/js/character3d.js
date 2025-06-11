/**
 * 3D角色模型載入器
 * 使用 Three.js 載入 GLB 格式的3D模型
 * 
 * 注意：此文件暫時被註解，3D功能暫未啟用
 * 如需使用3D角色功能，請取消註解並確保Three.js正確載入
 */

/*

class Character3D {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.character = null;
        this.mixer = null;
        this.animations = {};
        this.currentAnimation = null;
        this.clock = new THREE.Clock();
        
        // 載入配置
        this.config = window.CHARACTER_CONFIG || {};
        
        // 狀態管理
        this.isLoaded = false;
        this.isAnimating = false;
        
        this.init();
    }

    async init() {
        try {
            // 設置場景
            this.setupScene();
            this.setupCamera();
            this.setupRenderer();
            this.setupLights();
            
            // 開始渲染循環
            this.animate();
            
            // 監聽容器大小變化
            this.setupResizeListener();
            
            console.log('✅ 3D場景初始化成功');
        } catch (error) {
            console.error('❌ 3D場景初始化失敗:', error);
            this.showError('3D場景初始化失敗');
        }
    }

    setupScene() {
        this.scene = new THREE.Scene();
        this.scene.background = null; // 透明背景
    }

    setupCamera() {
        const aspect = this.container.clientWidth / this.container.clientHeight;
        const fov = this.config.camera?.fov || 45;
        const position = this.config.camera?.position || { x: 0, y: 1, z: 3 };
        const target = this.config.camera?.target || { x: 0, y: 0, z: 0 };
        
        this.camera = new THREE.PerspectiveCamera(fov, aspect, 0.1, 1000);
        this.camera.position.set(position.x, position.y, position.z);
        this.camera.lookAt(target.x, target.y, target.z);
    }

    setupRenderer() {
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true, 
            alpha: true 
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.outputColorSpace = THREE.SRGBColorSpace;
        
        this.container.appendChild(this.renderer.domElement);
    }

    setupLights() {
        const lighting = this.config.lighting || {};
        
        // 環境光
        const ambientConfig = lighting.ambient || { color: 0xffffff, intensity: 0.6 };
        const ambientLight = new THREE.AmbientLight(ambientConfig.color, ambientConfig.intensity);
        this.scene.add(ambientLight);

        // 主光源
        const directionalConfig = lighting.directional || { 
            color: 0xffffff, 
            intensity: 0.8, 
            position: { x: 2, y: 4, z: 3 } 
        };
        const directionalLight = new THREE.DirectionalLight(directionalConfig.color, directionalConfig.intensity);
        directionalLight.position.set(
            directionalConfig.position.x, 
            directionalConfig.position.y, 
            directionalConfig.position.z
        );
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 1024;
        directionalLight.shadow.mapSize.height = 1024;
        this.scene.add(directionalLight);

        // 補光
        const fillConfig = lighting.fill || { 
            color: 0xffffff, 
            intensity: 0.3, 
            position: { x: -2, y: 1, z: -1 } 
        };
        const fillLight = new THREE.DirectionalLight(fillConfig.color, fillConfig.intensity);
        fillLight.position.set(
            fillConfig.position.x, 
            fillConfig.position.y, 
            fillConfig.position.z
        );
        this.scene.add(fillLight);
    }

    async loadCharacter(modelPath) {
        try {
            const loadingMsg = this.config.statusMessages?.loading || '載入角色中...';
            this.updateStatus(loadingMsg);
            
            const loader = new THREE.GLTFLoader();
            const gltf = await new Promise((resolve, reject) => {
                loader.load(
                    modelPath || this.config.model?.path,
                    resolve,
                    (progress) => {
                        const percent = Math.round((progress.loaded / progress.total) * 100);
                        this.updateStatus(`載入中... ${percent}%`);
                    },
                    reject
                );
            });

            this.character = gltf.scene;
            
            // 從配置調整模型大小和位置
            const modelConfig = this.config.model || {};
            const scale = modelConfig.scale || 1;
            const position = modelConfig.position || { x: 0, y: -1, z: 0 };
            const rotation = modelConfig.rotation || { x: 0, y: 0, z: 0 };
            
            this.character.scale.setScalar(scale);
            this.character.position.set(position.x, position.y, position.z);
            this.character.rotation.set(rotation.x, rotation.y, rotation.z);
            
            // 啟用陰影
            this.character.traverse((node) => {
                if (node.isMesh) {
                    node.castShadow = true;
                    node.receiveShadow = true;
                }
            });

            this.scene.add(this.character);

            // 載入動畫
            if (gltf.animations && gltf.animations.length > 0) {
                this.mixer = new THREE.AnimationMixer(this.character);
                
                gltf.animations.forEach((clip) => {
                    const action = this.mixer.clipAction(clip);
                    this.animations[clip.name] = action;
                });

                // 播放預設動畫（通常是idle動畫）
                this.playAnimation('idle', true);
            }

            this.isLoaded = true;
            const readyMsg = this.config.statusMessages?.ready || '準備完成！';
            this.updateStatus(readyMsg);
            
            console.log('✅ 角色載入成功');
            console.log('🎬 可用動畫:', Object.keys(this.animations));

        } catch (error) {
            console.error('❌ 角色載入失敗:', error);
            this.showError('角色載入失敗');
        }
    }

    playAnimation(animationName, loop = false) {
        if (!this.mixer || !this.animations[animationName]) {
            console.warn(`⚠️ 動畫不存在: ${animationName}`);
            return;
        }

        // 停止當前動畫
        if (this.currentAnimation) {
            this.currentAnimation.fadeOut(0.5);
        }

        // 播放新動畫
        const action = this.animations[animationName];
        action.reset();
        action.setLoop(loop ? THREE.LoopRepeat : THREE.LoopOnce);
        action.fadeIn(0.5);
        action.play();

        this.currentAnimation = action;
        console.log(`🎬 播放動畫: ${animationName}`);
    }

    // 互動方法
    onPracticeStart() {
        this.playAnimation('practice', true);
        this.updateStatus('努力練習中...');
    }

    onPracticeComplete() {
        this.playAnimation('celebrate', false);
        this.updateStatus('練習完成！');
        
        // 3秒後回到idle狀態
        setTimeout(() => {
            this.playAnimation('idle', true);
            this.updateStatus('準備下次練習...');
        }, 3000);
    }

    onError() {
        this.playAnimation('sad', false);
        this.updateStatus('出現錯誤...');
    }

    // 工具方法
    updateStatus(status) {
        const statusElement = document.getElementById('characterStatus');
        if (statusElement) {
            statusElement.textContent = status;
        }
    }

    showError(message) {
        this.updateStatus(message);
        // 可以在這裡添加更多錯誤處理邏輯
    }

    setupResizeListener() {
        const resizeObserver = new ResizeObserver(() => {
            this.onResize();
        });
        resizeObserver.observe(this.container);
    }

    onResize() {
        if (!this.camera || !this.renderer) return;

        const width = this.container.clientWidth;
        const height = this.container.clientHeight;

        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        const delta = this.clock.getDelta();

        // 更新動畫
        if (this.mixer) {
            this.mixer.update(delta);
        }

        // 角色自動旋轉（可選）
        if (this.character && !this.isAnimating) {
            this.character.rotation.y += 0.005;
        }

        this.renderer.render(this.scene, this.camera);
    }

    // 清理資源
    dispose() {
        if (this.renderer) {
            this.renderer.dispose();
        }
        if (this.scene) {
            this.scene.clear();
        }
    }
}

// 導出給全局使用
window.Character3D = Character3D;

*/

// 暫時禁用3D功能的替代版本
window.Character3D = class {
    constructor(containerId) {
        console.log('3D角色功能暫時禁用');
    }
    
    init() {
        console.log('3D角色初始化已跳過');
        return Promise.resolve();
    }
    
    playAnimation(name) {
        console.log('3D動畫播放已跳過:', name);
    }
    
    celebrate() {
        console.log('3D慶祝動畫已跳過');
    }
};