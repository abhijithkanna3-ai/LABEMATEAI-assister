// Welcome Popup with Rotating Quotes
class WelcomePopup {
    constructor() {
        this.popup = document.getElementById('welcomePopup');
        this.quoteElement = document.getElementById('welcomeQuote');
        this.closeBtn = document.getElementById('closeWelcome');
        this.openChatBtn = document.getElementById('openChatFromPopup');
        
        this.quotes = [
            "Ready to assist with your laboratory work!",
            "I'm here to help with chemistry calculations and safety!",
            "Ask me anything about experiments and procedures!",
            "Need help with chemical information? I've got you covered!",
            "Let's make your lab work safer and more efficient!",
            "I can help with calculations, safety, and experiment planning!",
            "Your intelligent laboratory assistant is ready to help!",
            "Chemistry questions? I'm here to provide expert guidance!",
            "From basic concepts to complex procedures - I can help!",
            "Let's explore the fascinating world of chemistry together!",
            "Safety first! I can guide you through proper lab practices!",
            "Need to calculate molarity or prepare solutions? Just ask!",
            "I'm your go-to assistant for all things chemistry!",
            "Ready to tackle any laboratory challenge together!",
            "From MSDS to experiment design - I'm here to help!"
        ];
        
        this.currentQuoteIndex = 0;
        this.quoteInterval = null;
        this.hasShownPopup = false;
        
        this.initializeEventListeners();
        this.showWelcomePopup();
    }
    
    initializeEventListeners() {
        // Close popup
        this.closeBtn.addEventListener('click', () => this.hideWelcomePopup());
        
        // Open chat from popup
        this.openChatBtn.addEventListener('click', () => {
            this.hideWelcomePopup();
            if (window.floatingChatbot) {
                window.floatingChatbot.openChatFromExternal();
            }
        });
        
        // Close popup when clicking outside
        this.popup.addEventListener('click', (e) => {
            if (e.target === this.popup) {
                this.hideWelcomePopup();
            }
        });
    }
    
    showWelcomePopup() {
        // Only show if not already shown in this session
        if (this.hasShownPopup) return;
        
        // Show popup after a short delay
        setTimeout(() => {
            this.popup.style.display = 'block';
            this.startQuoteRotation();
            this.hasShownPopup = true;
        }, 1000);
    }
    
    hideWelcomePopup() {
        this.popup.style.display = 'none';
        this.stopQuoteRotation();
    }
    
    startQuoteRotation() {
        // Show first quote immediately
        this.updateQuote();
        
        // Rotate quotes every 30 seconds
        this.quoteInterval = setInterval(() => {
            this.updateQuote();
        }, 30000);
    }
    
    stopQuoteRotation() {
        if (this.quoteInterval) {
            clearInterval(this.quoteInterval);
            this.quoteInterval = null;
        }
    }
    
    updateQuote() {
        this.quoteElement.textContent = this.quotes[this.currentQuoteIndex];
        this.currentQuoteIndex = (this.currentQuoteIndex + 1) % this.quotes.length;
        
        // Add a subtle animation
        this.quoteElement.style.opacity = '0';
        setTimeout(() => {
            this.quoteElement.style.opacity = '1';
        }, 200);
    }
    
    // Method to show popup again (for testing)
    showAgain() {
        this.hasShownPopup = false;
        this.showWelcomePopup();
    }
}

// Initialize welcome popup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only show if user is logged in
    if (document.querySelector('nav.navbar')) {
        window.welcomePopup = new WelcomePopup();
    }
});

// Global function to show popup again (for testing)
window.showWelcomePopup = function() {
    if (window.welcomePopup) {
        window.welcomePopup.showAgain();
    }
};
