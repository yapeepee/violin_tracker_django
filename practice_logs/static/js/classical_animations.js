/**
 * 🎻 古典樂風格動畫與互動效果
 * 為小提琴練習記錄系統添加優雅的古典音樂風格動畫
 */

class ClassicalAnimations {
    constructor() {
        this.audioContext = null;
        this.isInitialized = false;
        this.init();
    }

    init() {
        this.setupMusicNoteAnimations();
        this.setupHoverEffects();
        this.setupScrollAnimations();
        this.setupParticleEffects();
        this.isInitialized = true;
    }

    /**
     * 音符飄落動畫
     */
    createFloatingNotes() {
        const notes = ['♪', '♫', '♬', '♩', '♭', '♯'];
        const colors = ['#B8860B', '#722F37', '#556B2F', '#CD7F32'];
        
        for (let i = 0; i < 5; i++) {
            setTimeout(() => {
                this.createSingleNote(notes, colors);
            }, i * 1000);
        }
    }

    createSingleNote(notes, colors) {
        const note = document.createElement('div');
        note.textContent = notes[Math.floor(Math.random() * notes.length)];
        note.style.cssText = `
            position: fixed;
            top: -20px;
            left: ${Math.random() * window.innerWidth}px;
            font-size: ${20 + Math.random() * 20}px;
            color: ${colors[Math.floor(Math.random() * colors.length)]};
            pointer-events: none;
            z-index: 1000;
            animation: floatDown ${3 + Math.random() * 2}s linear forwards;
            opacity: 0.7;
        `;
        
        document.body.appendChild(note);
        
        setTimeout(() => {
            note.remove();
        }, 5000);
    }

    /**
     * 成就解鎖慶祝動畫
     */
    celebrateAchievement(achievement) {
        const modal = this.createCelebrationModal(achievement);
        document.body.appendChild(modal);
        
        // 煙火效果
        this.createFireworks();
        
        // 音符雨
        this.createNoteRain();
        
        // 閃光效果
        this.createSparkles();
        
        // 3秒後自動關閉
        setTimeout(() => {
            modal.style.animation = 'fadeOut 0.5s ease-in';
            setTimeout(() => modal.remove(), 500);
        }, 3000);
    }

    createCelebrationModal(achievement) {
        const modal = document.createElement('div');
        modal.innerHTML = `
            <div class="achievement-celebration-modal">
                <div class="achievement-content">
                    <div class="achievement-crown">👑</div>
                    <div class="achievement-badge-large">
                        ${achievement.icon}
                    </div>
                    <h2 class="achievement-title">${achievement.name}</h2>
                    <p class="achievement-description">${achievement.description}</p>
                    <div class="celebration-particles"></div>
                </div>
            </div>
        `;
        
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            animation: celebrationFadeIn 0.5s ease-out;
        `;
        
        return modal;
    }

    createFireworks() {
        const fireworksContainer = document.createElement('div');
        fireworksContainer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9999;
        `;
        
        for (let i = 0; i < 3; i++) {
            setTimeout(() => {
                this.createSingleFirework(fireworksContainer);
            }, i * 500);
        }
        
        document.body.appendChild(fireworksContainer);
        setTimeout(() => fireworksContainer.remove(), 3000);
    }

    createSingleFirework(container) {
        const centerX = Math.random() * window.innerWidth;
        const centerY = Math.random() * window.innerHeight;
        
        for (let i = 0; i < 20; i++) {
            const particle = document.createElement('div');
            particle.style.cssText = `
                position: absolute;
                width: 4px;
                height: 4px;
                background: ${this.getRandomColor()};
                border-radius: 50%;
                left: ${centerX}px;
                top: ${centerY}px;
                animation: fireworkParticle 1s ease-out forwards;
            `;
            
            const angle = (i / 20) * 360;
            const distance = 50 + Math.random() * 100;
            particle.style.setProperty('--end-x', `${Math.cos(angle * Math.PI / 180) * distance}px`);
            particle.style.setProperty('--end-y', `${Math.sin(angle * Math.PI / 180) * distance}px`);
            
            container.appendChild(particle);
        }
    }

    createNoteRain() {
        const notes = ['♪', '♫', '♬', '♩'];
        for (let i = 0; i < 20; i++) {
            setTimeout(() => {
                this.createRainNote(notes);
            }, i * 100);
        }
    }

    createRainNote(notes) {
        const note = document.createElement('div');
        note.textContent = notes[Math.floor(Math.random() * notes.length)];
        note.style.cssText = `
            position: fixed;
            top: -30px;
            left: ${Math.random() * window.innerWidth}px;
            font-size: ${15 + Math.random() * 15}px;
            color: #B8860B;
            pointer-events: none;
            z-index: 9998;
            animation: noteRain 2s linear forwards;
        `;
        
        document.body.appendChild(note);
        setTimeout(() => note.remove(), 2000);
    }

    /**
     * 懸停效果設置
     */
    setupHoverEffects() {
        // 卡片懸停效果
        document.addEventListener('mouseenter', (e) => {
            if (e.target.classList.contains('practice-card')) {
                this.addCardHoverEffect(e.target);
            }
        }, true);

        // 按鈕懸停音效
        document.addEventListener('mouseenter', (e) => {
            if (e.target.classList.contains('btn-classical')) {
                this.playHoverSound();
            }
        }, true);

        // 星級評分懸停
        document.addEventListener('mouseenter', (e) => {
            if (e.target.classList.contains('rating-star')) {
                this.animateStarHover(e.target);
            }
        }, true);
    }

    addCardHoverEffect(card) {
        card.style.transform = 'translateY(-5px) scale(1.02)';
        
        // 添加光暈效果
        const glow = document.createElement('div');
        glow.style.cssText = `
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            background: linear-gradient(45deg, #B8860B, #FFBF00);
            border-radius: inherit;
            z-index: -1;
            opacity: 0;
            animation: cardGlow 0.3s ease-out forwards;
        `;
        
        card.style.position = 'relative';
        card.appendChild(glow);
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
            glow.remove();
        }, { once: true });
    }

    animateStarHover(star) {
        star.style.animation = 'starTwinkle 0.5s ease-in-out';
        setTimeout(() => {
            star.style.animation = '';
        }, 500);
    }

    /**
     * 滾動動畫
     */
    setupScrollAnimations() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    
                    // 特殊動畫處理
                    if (entry.target.classList.contains('stat-card')) {
                        this.animateStatCard(entry.target);
                    }
                }
            });
        }, { threshold: 0.1 });

        // 觀察所有需要動畫的元素
        document.querySelectorAll('.practice-card, .stat-card, .achievement-badge').forEach(el => {
            observer.observe(el);
        });
    }

    animateStatCard(card) {
        const statValue = card.querySelector('.stat-value');
        if (statValue) {
            const finalValue = parseInt(statValue.textContent);
            let currentValue = 0;
            const increment = finalValue / 30;
            
            const timer = setInterval(() => {
                currentValue += increment;
                if (currentValue >= finalValue) {
                    currentValue = finalValue;
                    clearInterval(timer);
                }
                statValue.textContent = Math.floor(currentValue);
            }, 50);
        }
    }

    /**
     * 粒子效果
     */
    setupParticleEffects() {
        this.createBackgroundParticles();
    }

    createBackgroundParticles() {
        const particleContainer = document.createElement('div');
        particleContainer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
        `;
        
        for (let i = 0; i < 20; i++) {
            const particle = document.createElement('div');
            particle.textContent = '♪';
            particle.style.cssText = `
                position: absolute;
                color: rgba(184, 134, 11, 0.1);
                font-size: ${10 + Math.random() * 10}px;
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
                animation: gentleFloat ${10 + Math.random() * 10}s infinite ease-in-out;
            `;
            
            particleContainer.appendChild(particle);
        }
        
        document.body.appendChild(particleContainer);
    }

    /**
     * 音效系統
     */
    async initAudioContext() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
    }

    playHoverSound() {
        if (!this.audioContext) return;
        
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        oscillator.frequency.setValueAtTime(800, this.audioContext.currentTime);
        gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
        gainNode.gain.linearRampToValueAtTime(0.1, this.audioContext.currentTime + 0.01);
        gainNode.gain.exponentialRampToValueAtTime(0.001, this.audioContext.currentTime + 0.1);
        
        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + 0.1);
    }

    playSuccessChord() {
        if (!this.audioContext) return;
        
        const frequencies = [523.25, 659.25, 783.99]; // C-E-G major chord
        
        frequencies.forEach((freq, index) => {
            setTimeout(() => {
                const oscillator = this.audioContext.createOscillator();
                const gainNode = this.audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(this.audioContext.destination);
                
                oscillator.frequency.setValueAtTime(freq, this.audioContext.currentTime);
                gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
                gainNode.gain.linearRampToValueAtTime(0.2, this.audioContext.currentTime + 0.01);
                gainNode.gain.exponentialRampToValueAtTime(0.001, this.audioContext.currentTime + 1);
                
                oscillator.start(this.audioContext.currentTime);
                oscillator.stop(this.audioContext.currentTime + 1);
            }, index * 100);
        });
    }

    /**
     * 工具函數
     */
    getRandomColor() {
        const colors = ['#B8860B', '#722F37', '#556B2F', '#CD7F32', '#FFBF00'];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    createSparkles() {
        for (let i = 0; i < 50; i++) {
            setTimeout(() => {
                const sparkle = document.createElement('div');
                sparkle.textContent = '✨';
                sparkle.style.cssText = `
                    position: fixed;
                    left: ${Math.random() * window.innerWidth}px;
                    top: ${Math.random() * window.innerHeight}px;
                    font-size: ${10 + Math.random() * 10}px;
                    pointer-events: none;
                    z-index: 9997;
                    animation: sparkle 1s ease-out forwards;
                `;
                
                document.body.appendChild(sparkle);
                setTimeout(() => sparkle.remove(), 1000);
            }, i * 50);
        }
    }
}

/**
 * CSS 動畫定義（動態注入）
 */
const animationStyles = `
    @keyframes floatDown {
        to {
            transform: translateY(${window.innerHeight + 50}px) rotate(360deg);
            opacity: 0;
        }
    }

    @keyframes celebrationFadeIn {
        from {
            opacity: 0;
            transform: scale(0.5);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }

    @keyframes fireworkParticle {
        to {
            transform: translate(var(--end-x), var(--end-y));
            opacity: 0;
        }
    }

    @keyframes noteRain {
        to {
            transform: translateY(${window.innerHeight + 50}px) rotate(720deg);
            opacity: 0;
        }
    }

    @keyframes cardGlow {
        to {
            opacity: 0.3;
        }
    }

    @keyframes starTwinkle {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.3) rotate(180deg); }
    }

    @keyframes gentleFloat {
        0%, 100% {
            transform: translateY(0px) rotate(0deg);
        }
        25% {
            transform: translateY(-20px) rotate(90deg);
        }
        75% {
            transform: translateY(20px) rotate(270deg);
        }
    }

    @keyframes sparkle {
        0% {
            opacity: 0;
            transform: scale(0) rotate(0deg);
        }
        50% {
            opacity: 1;
            transform: scale(1) rotate(180deg);
        }
        100% {
            opacity: 0;
            transform: scale(0) rotate(360deg);
        }
    }

    .animate-in {
        animation: fadeInUp 0.6s ease-out;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .achievement-celebration-modal .achievement-content {
        background: linear-gradient(135deg, #FDF5E6, #F4F1E8);
        border-radius: 20px;
        padding: 3rem;
        text-align: center;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        border: 3px solid #B8860B;
        position: relative;
        overflow: hidden;
    }

    .achievement-content::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(184, 134, 11, 0.1), transparent);
        animation: shimmer 2s infinite;
    }

    .achievement-crown {
        font-size: 3rem;
        margin-bottom: 1rem;
        animation: bounce 1s infinite;
    }

    .achievement-badge-large {
        font-size: 5rem;
        margin: 1rem 0;
        animation: pulse 1s infinite;
    }

    .achievement-title {
        font-family: 'Playfair Display', serif;
        color: #722F37;
        font-size: 2rem;
        margin-bottom: 1rem;
    }

    .achievement-description {
        font-family: 'Crimson Text', serif;
        color: #556B2F;
        font-size: 1.2rem;
    }

    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-10px); }
        60% { transform: translateY(-5px); }
    }
`;

// 注入動畫樣式
const styleSheet = document.createElement('style');
styleSheet.textContent = animationStyles;
document.head.appendChild(styleSheet);

// 全域實例
window.classicalAnimations = new ClassicalAnimations();

// DOM 載入完成後初始化
document.addEventListener('DOMContentLoaded', () => {
    // 用戶首次互動後初始化音效系統
    document.addEventListener('click', () => {
        window.classicalAnimations.initAudioContext();
    }, { once: true });
});

// 導出給其他模組使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ClassicalAnimations;
}