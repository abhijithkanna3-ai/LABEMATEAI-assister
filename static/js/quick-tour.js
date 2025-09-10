// Modern Quick Tour System for LabMate AI
class QuickTour {
    constructor() {
        this.currentStep = 0;
        this.tourSteps = [
            {
                title: 'Welcome to LabMate AI!',
                description: 'Your AI-powered laboratory assistant is here to help you with chemistry calculations, safety protocols, and experiment management.',
                highlight: 'Let me show you around the key features of this powerful tool.',
                icon: 'fas fa-rocket'
            },
            {
                title: 'Quick Tour Button',
                description: 'You can always restart this tour by clicking this button anytime you need a refresher.',
                highlight: 'This tour will help you discover all the amazing features LabMate AI has to offer.',
                icon: 'fas fa-route'
            },
            {
                title: 'Voice Commands',
                description: 'Use voice commands to interact with LabMate AI hands-free! Perfect for when your hands are busy in the lab.',
                highlight: 'Try saying "Calculate molarity" or "Show safety data" to get started.',
                icon: 'fas fa-microphone'
            },
            {
                title: 'Quick Actions',
                description: 'Access calculators, MSDS lookup, and safety protocols quickly from these convenient action cards.',
                highlight: 'These shortcuts will save you time during your experiments.',
                icon: 'fas fa-bolt'
            },
            {
                title: 'Chemistry Calculators',
                description: 'Click here to access specialized chemistry calculators for molarity, concentration, and more.',
                highlight: 'Our calculators support 10+ common chemicals with built-in safety data.',
                icon: 'fas fa-calculator'
            },
            {
                title: 'MSDS Lookup',
                description: 'Quick access to Material Safety Data Sheets for chemicals you\'re working with.',
                highlight: 'Always check safety data before handling any chemicals.',
                icon: 'fas fa-file-medical'
            },
            {
                title: 'Safety Protocols',
                description: 'Important safety information and emergency procedures for laboratory work.',
                highlight: 'Safety first! Review these protocols regularly.',
                icon: 'fas fa-shield-alt'
            },
            {
                title: 'AI Assistant',
                description: 'Your intelligent chatbot is always available in the bottom-right corner!',
                highlight: 'Ask questions about chemistry, get help with calculations, or discuss your experiments.',
                icon: 'fas fa-robot'
            },
            {
                title: 'Navigation Menu',
                description: 'Use the navigation bar to access all features: Dashboard, Calculator, MSDS, Safety, Documentation, and Activity Logs.',
                highlight: 'Everything you need is just one click away!',
                icon: 'fas fa-compass'
            }
        ];
        
        this.modal = null;
        this.isActive = false;
        this.highlightedElement = null;
    }
    
    start() {
        if (this.isActive) {
            this.end();
            return;
        }
        
        this.isActive = true;
        this.currentStep = 0;
        this.createModal();
        this.showStep(0);
        
        // Add keyboard navigation
        document.addEventListener('keydown', this.handleKeydown.bind(this));
    }
    
    createModal() {
        // Remove existing modal if any
        const existingModal = document.getElementById('quickTourModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Create modal HTML
        const modalHTML = `
            <div class="quick-tour-modal" id="quickTourModal">
                <div class="quick-tour-content">
                    <div class="quick-tour-header">
                        <h5 class="quick-tour-title">
                            <i class="fas fa-route"></i>
                            Quick Tour
                        </h5>
                        <button type="button" class="quick-tour-close" id="closeTourBtn" aria-label="Close">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="quick-tour-body">
                        <div id="tourContent" class="quick-tour-step-enter">
                            <div class="quick-tour-step">
                                Step <span id="currentStep">1</span> of <span id="totalSteps">9</span>
                            </div>
                            <p id="tourDescription" class="quick-tour-description">Welcome to LabMate AI!</p>
                            <div id="tourHighlight" class="quick-tour-highlight">
                                <i class="fas fa-lightbulb"></i>
                                <span id="highlightText">Let me show you around!</span>
                            </div>
                        </div>
                        <div class="quick-tour-actions">
                            <button type="button" class="quick-tour-btn quick-tour-btn-prev" id="prevBtn" disabled>
                                <i class="fas fa-chevron-left"></i>
                                Previous
                            </button>
                            <button type="button" class="quick-tour-btn quick-tour-btn-next" id="nextBtn">
                                Next
                                <i class="fas fa-chevron-right"></i>
                            </button>
                            <button type="button" class="quick-tour-btn quick-tour-btn-skip" id="skipBtn">
                                Skip Tour
                            </button>
                        </div>
                        <div class="quick-tour-progress">
                            <div class="quick-tour-dot active"></div>
                            <div class="quick-tour-dot"></div>
                            <div class="quick-tour-dot"></div>
                            <div class="quick-tour-dot"></div>
                            <div class="quick-tour-dot"></div>
                            <div class="quick-tour-dot"></div>
                            <div class="quick-tour-dot"></div>
                            <div class="quick-tour-dot"></div>
                            <div class="quick-tour-dot"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('quickTourModal');
        
        // Add event listeners
        this.addEventListeners();
    }
    
    addEventListeners() {
        const closeBtn = document.getElementById('closeTourBtn');
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const skipBtn = document.getElementById('skipBtn');
        
        closeBtn.addEventListener('click', () => this.end());
        prevBtn.addEventListener('click', () => this.previous());
        nextBtn.addEventListener('click', () => this.next());
        skipBtn.addEventListener('click', () => this.end());
        
        // Close on backdrop click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.end();
            }
        });
    }
    
    showStep(stepIndex) {
        if (stepIndex >= this.tourSteps.length) {
            this.end();
            return;
        }
        
        const step = this.tourSteps[stepIndex];
        
        // Update content
        document.getElementById('currentStep').textContent = stepIndex + 1;
        document.getElementById('totalSteps').textContent = this.tourSteps.length;
        document.getElementById('tourDescription').textContent = step.description;
        document.getElementById('highlightText').textContent = step.highlight;
        
        // Update icon in title
        const titleIcon = document.querySelector('.quick-tour-title i');
        titleIcon.className = step.icon;
        
        // Update buttons
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        
        prevBtn.disabled = stepIndex === 0;
        
        if (stepIndex === this.tourSteps.length - 1) {
            nextBtn.innerHTML = '<i class="fas fa-check"></i> Finish';
        } else {
            nextBtn.innerHTML = 'Next <i class="fas fa-chevron-right"></i>';
        }
        
        // Update progress dots
        this.updateProgressDots(stepIndex);
        
        // Add step animation
        const content = document.getElementById('tourContent');
        content.classList.remove('quick-tour-step-enter');
        setTimeout(() => {
            content.classList.add('quick-tour-step-enter');
        }, 10);
        
        this.currentStep = stepIndex;
    }
    
    updateProgressDots(currentStep) {
        const dots = document.querySelectorAll('.quick-tour-dot');
        dots.forEach((dot, index) => {
            dot.classList.remove('active', 'completed');
            if (index < currentStep) {
                dot.classList.add('completed');
            } else if (index === currentStep) {
                dot.classList.add('active');
            }
        });
    }
    
    next() {
        if (this.currentStep < this.tourSteps.length - 1) {
            this.showStep(this.currentStep + 1);
        } else {
            this.end();
        }
    }
    
    previous() {
        if (this.currentStep > 0) {
            this.showStep(this.currentStep - 1);
        }
    }
    
    handleKeydown(e) {
        if (!this.isActive) return;
        
        switch (e.key) {
            case 'Escape':
                this.end();
                break;
            case 'ArrowRight':
            case 'Enter':
                e.preventDefault();
                this.next();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                this.previous();
                break;
        }
    }
    
    end() {
        this.isActive = false;
        
        if (this.modal) {
            this.modal.remove();
            this.modal = null;
        }
        
        // Remove keyboard listener
        document.removeEventListener('keydown', this.handleKeydown.bind(this));
        
        // Show completion message
        this.showCompletionMessage();
    }
    
    showCompletionMessage() {
        const message = document.createElement('div');
        message.className = 'tour-completion';
        message.innerHTML = `
            <div class="alert alert-success alert-dismissible fade show" role="alert" style="position: fixed; top: 20px; right: 20px; z-index: 10001; min-width: 300px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <i class="fas fa-check-circle" style="font-size: 20px; color: #10b981;"></i>
                    <div>
                        <strong>Tour Complete!</strong><br>
                        <small>You're now ready to use LabMate AI effectively!</small>
                    </div>
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" style="position: absolute; top: 10px; right: 15px;"></button>
            </div>
        `;
        
        document.body.appendChild(message);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (message.parentNode) {
                message.remove();
            }
        }, 5000);
    }
}

// Global functions
let quickTour;

function startQuickTour() {
    if (!quickTour) {
        quickTour = new QuickTour();
    }
    quickTour.start();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if user is logged in
    if (document.querySelector('nav.navbar')) {
        quickTour = new QuickTour();
    }
});