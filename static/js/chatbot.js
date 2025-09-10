// LabMate AI Chatbot JavaScript
class LabMateChatbot {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.clearChatBtn = document.getElementById('clearChatBtn');
        this.helpBtn = document.getElementById('helpBtn');
        // No modal needed - using typing indicator instead
        
        this.initializeEventListeners();
        this.loadChatHistory();
    }
    
    initializeEventListeners() {
        // Send message on button click
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter key
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Clear chat history
        this.clearChatBtn.addEventListener('click', () => this.clearChatHistory());
        
        // Help button
        this.helpBtn.addEventListener('click', () => this.showHelp());
        
        // Example links
        document.querySelectorAll('.example-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const example = e.target.getAttribute('data-example');
                this.messageInput.value = example;
                this.sendMessage();
            });
        });
        
        // Quick action buttons
        document.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.getAttribute('data-action');
                this.handleQuickAction(action);
            });
        });
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
        });
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        
        // Disable send button
        this.sendBtn.disabled = true;
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            const response = await fetch('/chatbot/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Add bot response to chat
                this.addMessage(data.response, 'bot');
            } else {
                this.addMessage('Sorry, I encountered an error. Please try again.', 'bot', true);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('Sorry, I encountered a network error. Please check your connection and try again.', 'bot', true);
        } finally {
            this.hideTypingIndicator();
            this.sendBtn.disabled = false;
            this.messageInput.focus();
        }
    }
    
    addMessage(content, sender, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message ${isError ? 'error' : ''}`;
        
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="d-flex justify-content-end mb-3">
                    <div class="message-bubble user-bubble">
                        <div class="message-content">${this.escapeHtml(content)}</div>
                        <div class="message-time">${timestamp}</div>
                    </div>
                    <div class="message-avatar user-avatar">
                        <i class="fas fa-user"></i>
                    </div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="d-flex justify-content-start mb-3">
                    <div class="message-avatar bot-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-bubble bot-bubble">
                        <div class="message-content">${this.formatBotResponse(content)}</div>
                        <div class="message-time">${timestamp}</div>
                    </div>
                </div>
            `;
        }
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
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
        typingDiv.className = 'message bot typing-indicator';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `
            <div class="d-flex justify-content-start mb-3">
                <div class="message-avatar bot-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-bubble bot-bubble">
                    <div class="typing-indicator">
                        <div class="typing-dots">
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                        </div>
                    </div>
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
    
    async loadChatHistory() {
        try {
            const response = await fetch('/chatbot/history?per_page=10');
            const data = await response.json();
            
            if (data.success && data.messages.length > 0) {
                // Clear welcome message
                this.chatMessages.innerHTML = '';
                
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
            console.error('Error loading chat history:', error);
        }
    }
    
    async clearChatHistory() {
        if (!confirm('Are you sure you want to clear all chat history? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch('/chatbot/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Clear chat messages
                this.chatMessages.innerHTML = `
                    <div class="p-3">
                        <div class="text-center text-muted mb-3">
                            <i class="fas fa-robot fa-2x mb-2"></i>
                            <p>Chat history cleared. How can I help you today?</p>
                        </div>
                    </div>
                `;
                
                // Show success message
                this.showToast('Chat history cleared successfully!', 'success');
            } else {
                this.showToast('Failed to clear chat history', 'error');
            }
        } catch (error) {
            console.error('Error clearing chat history:', error);
            this.showToast('Network error while clearing chat history', 'error');
        }
    }
    
    showHelp() {
        const helpMessage = "🤖 **LabMate AI - What I Can Do:**\n\n" +
            "**Calculations:**\n" +
            "• Calculate reagent masses for specific concentrations\n" +
            "• Example: 'Calculate 0.1M NaCl for 100mL'\n\n" +
            "**Chemical Information:**\n" +
            "• Look up chemical properties and safety data\n" +
            "• Example: 'Tell me about sodium hydroxide'\n\n" +
            "**Safety Guidance:**\n" +
            "• Get safety information for specific chemicals\n" +
            "• Example: 'Safety info for sulfuric acid'\n\n" +
            "**Experiment Help:**\n" +
            "• Plan experiments and procedures\n" +
            "• Example: 'Help me plan a titration experiment'\n\n" +
            "Just ask me anything about laboratory work!";
        
        this.addMessage(helpMessage, 'bot');
    }
    
    handleQuickAction(action) {
        const actions = {
            'calculation': 'I can help you calculate reagent masses. Try asking: "Calculate 0.1M NaCl for 100mL"',
            'chemical-info': 'I can provide chemical information. Try asking: "Tell me about sodium hydroxide"',
            'safety': 'I can provide safety information. Try asking: "Safety info for sulfuric acid"',
            'experiment': 'I can help with experiment planning. Try asking: "Help me plan a titration experiment"'
        };
        
        if (actions[action]) {
            this.addMessage(actions[action], 'bot');
        }
    }
    
    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(toast);
        
        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove after hidden
        toast.addEventListener('hidden.bs.toast', () => {
            document.body.removeChild(toast);
        });
    }
}

// Initialize chatbot when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new LabMateChatbot();
});

// Add CSS styles for chat interface
const style = document.createElement('style');
style.textContent = `
    .message-bubble {
        max-width: 70%;
        padding: 12px 16px;
        border-radius: 18px;
        position: relative;
        word-wrap: break-word;
    }
    
    .user-bubble {
        background-color: #007bff;
        color: white;
        border-bottom-right-radius: 4px;
    }
    
    .bot-bubble {
        background-color: #f8f9fa;
        color: #333;
        border: 1px solid #dee2e6;
        border-bottom-left-radius: 4px;
    }
    
    .message-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 8px;
        flex-shrink: 0;
    }
    
    .user-avatar {
        background-color: #007bff;
        color: white;
    }
    
    .bot-avatar {
        background-color: #6c757d;
        color: white;
    }
    
    .message-time {
        font-size: 0.75rem;
        opacity: 0.7;
        margin-top: 4px;
    }
    
    .message.error .bot-bubble {
        background-color: #f8d7da;
        border-color: #f5c6cb;
        color: #721c24;
    }
    
    .example-link {
        color: #007bff;
        cursor: pointer;
        text-decoration: underline;
    }
    
    .example-link:hover {
        color: #0056b3;
    }
    
    /* Typing Indicator */
    .typing-indicator {
        display: flex;
        align-items: center;
        padding: 10px 15px;
        background: white;
        border-radius: 18px;
        border: 1px solid #e9ecef;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .typing-dots {
        display: flex;
        gap: 4px;
    }
    
    .typing-dot {
        width: 6px;
        height: 6px;
        background: #6c757d;
        border-radius: 50%;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes typing {
        0%, 80%, 100% {
            transform: scale(0.8);
            opacity: 0.5;
        }
        40% {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    #chatMessages {
        scrollbar-width: thin;
        scrollbar-color: #007bff #f8f9fa;
    }
    
    #chatMessages::-webkit-scrollbar {
        width: 6px;
    }
    
    #chatMessages::-webkit-scrollbar-track {
        background: #f8f9fa;
    }
    
    #chatMessages::-webkit-scrollbar-thumb {
        background: #007bff;
        border-radius: 3px;
    }
    
    #chatMessages::-webkit-scrollbar-thumb:hover {
        background: #0056b3;
    }
`;
document.head.appendChild(style);
