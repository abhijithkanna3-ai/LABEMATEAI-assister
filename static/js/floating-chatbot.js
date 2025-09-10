// Floating Chatbot Widget JavaScript
class FloatingChatbot {
    constructor() {
        this.chatToggle = document.getElementById('chatToggle');
        this.chatWindow = document.getElementById('chatWindow');
        this.chatMessages = document.getElementById('chatMessagesWidget');
        this.messageInput = document.getElementById('messageInputWidget');
        this.sendBtn = document.getElementById('sendBtnWidget');
        this.minimizeBtn = document.getElementById('minimizeChat');
        this.closeBtn = document.getElementById('closeChat');
        this.messageBadge = document.getElementById('messageBadge');
        
        this.isOpen = false;
        this.isMinimized = false;
        this.unreadCount = 0;
        
        this.initializeEventListeners();
        this.loadRecentMessages();
    }
    
    initializeEventListeners() {
        // Toggle chat window
        this.chatToggle.addEventListener('click', () => this.toggleChat());
        
        // Send message
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter key
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Minimize chat
        this.minimizeBtn.addEventListener('click', () => this.minimizeChat());
        
        // Close chat
        this.closeBtn.addEventListener('click', () => this.closeChat());
        
        // Example links
        document.querySelectorAll('.example-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const example = e.target.getAttribute('data-example');
                this.messageInput.value = example;
                this.sendMessage();
            });
        });
        
        // Click outside to close
        document.addEventListener('click', (e) => {
            if (this.isOpen && !this.chatWindow.contains(e.target) && !this.chatToggle.contains(e.target)) {
                this.closeChat();
            }
        });
        
        // Auto-resize input
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
        });
    }
    
    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }
    
    openChat() {
        this.chatWindow.style.display = 'flex';
        this.isOpen = true;
        this.isMinimized = false;
        this.unreadCount = 0;
        this.messageBadge.style.display = 'none';
        this.messageInput.focus();
        
        // Close welcome popup if it exists
        const welcomePopup = document.getElementById('welcomePopup');
        if (welcomePopup) {
            welcomePopup.style.display = 'none';
        }
        
        // Add opening animation
        this.chatWindow.style.animation = 'slideUp 0.3s ease-out';
    }
    
    closeChat() {
        this.chatWindow.style.display = 'none';
        this.isOpen = false;
        this.isMinimized = false;
    }
    
    minimizeChat() {
        this.chatWindow.style.height = '60px';
        this.chatMessages.style.display = 'none';
        this.messageInput.parentElement.parentElement.style.display = 'none';
        this.isMinimized = true;
        
        // Change minimize button to expand
        this.minimizeBtn.innerHTML = '<i class="fas fa-plus"></i>';
        this.minimizeBtn.title = 'Expand';
    }
    
    expandChat() {
        this.chatWindow.style.height = '500px';
        this.chatMessages.style.display = 'block';
        this.messageInput.parentElement.parentElement.style.display = 'block';
        this.isMinimized = false;
        
        // Change expand button to minimize
        this.minimizeBtn.innerHTML = '<i class="fas fa-minus"></i>';
        this.minimizeBtn.title = 'Minimize';
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Disable send button
        this.sendBtn.disabled = true;
        
        try {
            const response = await fetch('/chatbot/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            this.hideTypingIndicator();
            
            if (data.success) {
                // Add bot response to chat
                this.addMessage(data.response, 'bot');
            } else {
                this.addMessage('Sorry, I encountered an error. Please try again.', 'bot', true);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage('Sorry, I encountered a network error. Please check your connection and try again.', 'bot', true);
        } finally {
            this.sendBtn.disabled = false;
            this.messageInput.focus();
        }
    }
    
    addMessage(content, sender, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-widget ${sender} ${isError ? 'error' : ''}`;
        
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="message-bubble-widget">
                    <div class="message-content">${this.escapeHtml(content)}</div>
                    <div class="message-time-widget">${timestamp}</div>
                </div>
                <div class="message-avatar-widget">
                    <i class="fas fa-user"></i>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-avatar-widget">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-bubble-widget">
                    <div class="message-content">${this.formatBotResponse(content)}</div>
                    <div class="message-time-widget">${timestamp}</div>
                </div>
            `;
        }
        
        // Remove welcome message if it exists
        const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Show notification badge if chat is closed
        if (!this.isOpen && sender === 'bot') {
            this.showNotificationBadge();
        }
    }
    
    formatBotResponse(content) {
        // Convert markdown-like formatting to HTML
        let formatted = this.escapeHtml(content);
        
        // Bold text
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Line breaks
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Emojis
        formatted = formatted.replace(/✅/g, '<span class="text-success">✅</span>');
        formatted = formatted.replace(/❌/g, '<span class="text-danger">❌</span>');
        formatted = formatted.replace(/⚠️/g, '<span class="text-warning">⚠️</span>');
        formatted = formatted.replace(/🧪/g, '<span class="text-info">🧪</span>');
        formatted = formatted.replace(/🤖/g, '<span class="text-primary">🤖</span>');
        
        return formatted;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message-widget bot typing-indicator';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `
            <div class="message-avatar-widget">
                <i class="fas fa-robot"></i>
            </div>
            <div class="typing-indicator">
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    showNotificationBadge() {
        this.unreadCount++;
        this.messageBadge.textContent = this.unreadCount;
        this.messageBadge.style.display = 'flex';
    }
    
    async loadRecentMessages() {
        try {
            const response = await fetch('/chatbot/history?per_page=5');
            const data = await response.json();
            
            if (data.success && data.messages.length > 0) {
                // Clear welcome message
                const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
                if (welcomeMessage) {
                    welcomeMessage.remove();
                }
                
                // Add messages in reverse order (oldest first)
                data.messages.reverse().forEach(msg => {
                    if (msg.is_user_message && msg.message) {
                        this.addMessage(msg.message, 'user');
                    } else if (!msg.is_user_message && msg.response) {
                        this.addMessage(msg.response, 'bot');
                    }
                });
            }
        } catch (error) {
            console.error('Error loading recent messages:', error);
        }
    }
    
    // Public method to open chat from external sources
    openChatFromExternal() {
        this.openChat();
    }
    
    // Public method to send a message from external sources
    sendMessageFromExternal(message) {
        this.messageInput.value = message;
        this.sendMessage();
    }
}

// Initialize floating chatbot when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if user is logged in
    if (document.querySelector('nav.navbar')) {
        window.floatingChatbot = new FloatingChatbot();
    }
});

// Global functions for external access
window.openChatbot = function() {
    if (window.floatingChatbot) {
        window.floatingChatbot.openChatFromExternal();
    }
};

window.sendChatbotMessage = function(message) {
    if (window.floatingChatbot) {
        window.floatingChatbot.sendMessageFromExternal(message);
    }
};
