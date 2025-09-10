// ChemLLM JavaScript functionality
class ChemLLMInterface {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.modelStatus = document.getElementById('modelStatus');
        this.modelInfo = document.getElementById('modelInfo');
        
        // Settings elements
        this.maxLength = document.getElementById('maxLength');
        this.temperature = document.getElementById('temperature');
        this.topP = document.getElementById('topP');
        
        // Value displays
        this.maxLengthValue = document.getElementById('maxLengthValue');
        this.temperatureValue = document.getElementById('temperatureValue');
        this.topPValue = document.getElementById('topPValue');
        
        // Action buttons
        this.clearChatBtn = document.getElementById('clearChat');
        this.checkStatusBtn = document.getElementById('checkStatus');
        this.exportChatBtn = document.getElementById('exportChat');
        
        this.isGenerating = false;
        this.chatHistory = [];
        
        this.initializeEventListeners();
        this.updateParameterDisplays();
    }
    
    initializeEventListeners() {
        // Send message
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Parameter sliders
        this.maxLength.addEventListener('input', () => this.updateParameterDisplays());
        this.temperature.addEventListener('input', () => this.updateParameterDisplays());
        this.topP.addEventListener('input', () => this.updateParameterDisplays());
        
        // Action buttons
        this.clearChatBtn.addEventListener('click', () => this.clearChat());
        this.checkStatusBtn.addEventListener('click', () => this.checkModelStatus());
        this.exportChatBtn.addEventListener('click', () => this.exportChat());
        
        // Example links
        document.querySelectorAll('.example-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const example = e.target.getAttribute('data-example');
                this.messageInput.value = example;
                this.messageInput.focus();
            });
        });
    }
    
    updateParameterDisplays() {
        this.maxLengthValue.textContent = this.maxLength.value;
        this.temperatureValue.textContent = this.temperature.value;
        this.topPValue.textContent = this.topP.value;
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isGenerating) return;
        
        // Add user message to chat
        this.addMessage('user', message);
        this.messageInput.value = '';
        
        // Show loading state
        this.setGeneratingState(true);
        
        try {
            const response = await fetch('/chemllm/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: message,
                    max_length: parseInt(this.maxLength.value),
                    temperature: parseFloat(this.temperature.value),
                    top_p: parseFloat(this.topP.value)
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.addMessage('assistant', data.response);
                this.chatHistory.push({
                    user: message,
                    assistant: data.response,
                    timestamp: data.timestamp,
                    parameters: {
                        max_length: parseInt(this.maxLength.value),
                        temperature: parseFloat(this.temperature.value),
                        top_p: parseFloat(this.topP.value)
                    }
                });
            } else {
                this.addMessage('error', data.error || 'An error occurred while generating the response.');
                
                // If model is not available, update status
                if (data.model_status) {
                    this.updateModelStatus(data.model_status);
                }
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('error', 'Failed to connect to the server. Please try again.');
        } finally {
            this.setGeneratingState(false);
        }
    }
    
    addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message mb-3`;
        
        const timestamp = new Date().toLocaleTimeString();
        
        if (type === 'user') {
            messageDiv.innerHTML = `
                <div class="d-flex justify-content-end">
                    <div class="user-message bg-primary text-white p-3 rounded" style="max-width: 80%;">
                        <div class="message-content">${this.formatMessage(content)}</div>
                        <small class="opacity-75">${timestamp}</small>
                    </div>
                </div>
            `;
        } else if (type === 'assistant') {
            messageDiv.innerHTML = `
                <div class="d-flex justify-content-start">
                    <div class="assistant-message bg-light border p-3 rounded" style="max-width: 80%;">
                        <div class="d-flex align-items-center mb-2">
                            <i class="fas fa-brain text-primary me-2"></i>
                            <strong>ChemLLM</strong>
                        </div>
                        <div class="message-content">${this.formatMessage(content)}</div>
                        <small class="text-muted">${timestamp}</small>
                    </div>
                </div>
            `;
        } else if (type === 'error') {
            messageDiv.innerHTML = `
                <div class="d-flex justify-content-center">
                    <div class="error-message alert alert-danger p-3 rounded" style="max-width: 80%;">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            <div>${content}</div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Remove welcome message if it exists
        const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
    }
    
    formatMessage(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    setGeneratingState(isGenerating) {
        this.isGenerating = isGenerating;
        this.sendBtn.disabled = isGenerating;
        this.messageInput.disabled = isGenerating;
        
        if (isGenerating) {
            this.sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Generating...';
            this.showLoadingModal();
        } else {
            this.sendBtn.innerHTML = '<i class="fas fa-paper-plane me-1"></i>Send';
            this.hideLoadingModal();
        }
    }
    
    showLoadingModal() {
        const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
        modal.show();
    }
    
    hideLoadingModal() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
        if (modal) {
            modal.hide();
        }
    }
    
    clearChat() {
        if (confirm('Are you sure you want to clear the chat history?')) {
            this.chatMessages.innerHTML = `
                <div class="welcome-message text-center text-muted">
                    <i class="fas fa-atom fa-3x mb-3"></i>
                    <h5>Welcome to ChemLLM!</h5>
                    <p>Ask me anything about chemistry, molecular science, reactions, or laboratory procedures.</p>
                </div>
            `;
            this.chatHistory = [];
        }
    }
    
    async checkModelStatus() {
        try {
            const response = await fetch('/chemllm/status');
            const data = await response.json();
            
            if (data.success) {
                this.updateModelStatus(data.model_info);
                this.showAlert('Model status updated successfully!', 'success');
            } else {
                this.showAlert('Failed to check model status', 'danger');
            }
        } catch (error) {
            console.error('Error checking model status:', error);
            this.showAlert('Failed to connect to the server', 'danger');
        }
    }
    
    updateModelStatus(modelInfo) {
        this.modelStatus.className = `badge ${modelInfo.status === 'loaded' ? 'bg-success' : 'bg-danger'}`;
        this.modelStatus.innerHTML = modelInfo.status === 'loaded' 
            ? '<i class="fas fa-check-circle me-1"></i>Model Ready'
            : '<i class="fas fa-exclamation-triangle me-1"></i>Model Not Available';
        
        // Update model info display
        this.modelInfo.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <strong>Model:</strong> ${modelInfo.model_name}<br>
                    <strong>Device:</strong> ${modelInfo.device}<br>
                    <strong>Type:</strong> ${modelInfo.model_type}
                </div>
                <div class="col-md-6">
                    <strong>Status:</strong> 
                    <span class="${modelInfo.status === 'loaded' ? 'text-success' : 'text-danger'}">
                        ${modelInfo.status.charAt(0).toUpperCase() + modelInfo.status.slice(1)}
                    </span><br>
                    <strong>Parameters:</strong> 7.74B<br>
                    <strong>Specialization:</strong> Chemistry & Molecule Science
                </div>
            </div>
        `;
        
        // Enable/disable send button
        this.sendBtn.disabled = modelInfo.status !== 'loaded';
    }
    
    exportChat() {
        if (this.chatHistory.length === 0) {
            this.showAlert('No chat history to export', 'warning');
            return;
        }
        
        const exportData = {
            timestamp: new Date().toISOString(),
            model: 'ChemLLM-7B-Chat-1.5-DPO',
            chat_history: this.chatHistory
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chemllm_chat_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showAlert('Chat history exported successfully!', 'success');
    }
    
    showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at the top of the main content
        const container = document.querySelector('.container-fluid');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChemLLMInterface();
});
