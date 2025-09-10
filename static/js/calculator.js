// LabMate AI - Calculator Module
// Handles reagent calculations and form interactions

class CalculatorController {
    constructor() {
        this.currentCalculation = null;
        this.calculationHistory = [];
        
        this.initializeCalculator();
        this.loadCalculationHistory();
    }
    
    initializeCalculator() {
        // Set up form submission handler
        const calculatorForm = document.getElementById('calculatorForm');
        if (calculatorForm) {
            calculatorForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmission();
            });
        }
        
        // Set up input validation
        this.setupInputValidation();
        
        // Set up auto-calculation
        this.setupAutoCalculation();
        
        // Set up keyboard shortcuts
        this.setupKeyboardShortcuts();
    }
    
    setupInputValidation() {
        const inputs = ['reagent', 'molarity', 'volume'];
        
        inputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) {
                input.addEventListener('blur', () => this.validateInput(input));
                input.addEventListener('input', () => this.clearInputError(input));
            }
        });
    }
    
    setupAutoCalculation() {
        const inputs = ['reagent', 'molarity', 'volume'];
        
        inputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) {
                input.addEventListener('input', this.debounce(() => {
                    if (this.isFormValid()) {
                        this.performCalculation(true); // Preview mode
                    }
                }, 500));
            }
        });
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Enter to calculate
            if (e.key === 'Enter' && !e.shiftKey) {
                const activeElement = document.activeElement;
                if (activeElement && activeElement.closest('#calculatorForm')) {
                    e.preventDefault();
                    this.handleFormSubmission();
                }
            }
            
            // Escape to clear form
            if (e.key === 'Escape') {
                this.clearForm();
            }
        });
    }
    
    handleFormSubmission() {
        if (!this.validateForm()) {
            return;
        }
        
        this.performCalculation(false);
    }
    
    validateForm() {
        const reagent = document.getElementById('reagent').value;
        const molarity = document.getElementById('molarity').value;
        const volume = document.getElementById('volume').value;
        
        let isValid = true;
        
        // Validate reagent selection
        if (!reagent) {
            this.showInputError('reagent', 'Please select a reagent');
            isValid = false;
        }
        
        // Validate molarity
        if (!molarity || parseFloat(molarity) <= 0) {
            this.showInputError('molarity', 'Please enter a valid molarity (> 0)');
            isValid = false;
        } else if (parseFloat(molarity) > 10) {
            this.showInputError('molarity', 'Molarity seems high. Please verify (usually < 10 M)');
        }
        
        // Validate volume
        if (!volume || parseFloat(volume) <= 0) {
            this.showInputError('volume', 'Please enter a valid volume (> 0)');
            isValid = false;
        } else if (parseFloat(volume) > 10000) {
            this.showInputError('volume', 'Volume seems high. Please verify (in mL)');
        }
        
        return isValid;
    }
    
    isFormValid() {
        const reagent = document.getElementById('reagent').value;
        const molarity = document.getElementById('molarity').value;
        const volume = document.getElementById('volume').value;
        
        return reagent && molarity && volume && 
               parseFloat(molarity) > 0 && parseFloat(volume) > 0;
    }
    
    validateInput(input) {
        const value = input.value.trim();
        const inputId = input.id;
        
        switch (inputId) {
            case 'reagent':
                if (!value) {
                    this.showInputError(inputId, 'Please select a reagent');
                }
                break;
                
            case 'molarity':
                if (!value || isNaN(parseFloat(value)) || parseFloat(value) <= 0) {
                    this.showInputError(inputId, 'Please enter a valid molarity');
                } else if (parseFloat(value) > 10) {
                    this.showInputWarning(inputId, 'High molarity - please verify');
                }
                break;
                
            case 'volume':
                if (!value || isNaN(parseFloat(value)) || parseFloat(value) <= 0) {
                    this.showInputError(inputId, 'Please enter a valid volume');
                } else if (parseFloat(value) > 10000) {
                    this.showInputWarning(inputId, 'Large volume - please verify (in mL)');
                }
                break;
        }
    }
    
    showInputError(inputId, message) {
        const input = document.getElementById(inputId);
        const feedbackElement = this.getOrCreateFeedback(input, 'invalid');
        
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
        feedbackElement.textContent = message;
    }
    
    showInputWarning(inputId, message) {
        const input = document.getElementById(inputId);
        const feedbackElement = this.getOrCreateFeedback(input, 'warning');
        
        input.classList.add('border-warning');
        feedbackElement.textContent = message;
        feedbackElement.className = 'text-warning small mt-1';
    }
    
    clearInputError(input) {
        input.classList.remove('is-invalid', 'is-valid', 'border-warning');
        const feedback = input.parentNode.querySelector('.invalid-feedback, .text-warning');
        if (feedback) {
            feedback.remove();
        }
    }
    
    getOrCreateFeedback(input, type) {
        let feedback = input.parentNode.querySelector(
            type === 'invalid' ? '.invalid-feedback' : '.text-warning'
        );
        
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = type === 'invalid' ? 'invalid-feedback' : 'text-warning small mt-1';
            input.parentNode.appendChild(feedback);
        }
        
        return feedback;
    }
    
    performCalculation(isPreview = false) {
        const formData = new FormData(document.getElementById('calculatorForm'));
        const submitButton = document.querySelector('#calculatorForm button[type="submit"]');
        
        if (!isPreview && submitButton) {
            this.showLoading(submitButton);
        }
        
        // Use form submission for server-side calculation
        const form = document.getElementById('calculatorForm');
        form.submit();
    }
    
    showLoading(element) {
        const originalContent = element.innerHTML;
        element.setAttribute('data-original-content', originalContent);
        element.disabled = true;
        element.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            Calculating...
        `;
    }
    
    hideLoading(element) {
        const originalContent = element.getAttribute('data-original-content');
        if (originalContent) {
            element.innerHTML = originalContent;
            element.disabled = false;
            element.removeAttribute('data-original-content');
        }
    }
    
    displayCalculationResult(result) {
        const resultsDiv = document.getElementById('results');
        const contentDiv = document.getElementById('resultContent');
        
        if (!resultsDiv || !contentDiv) return;
        
        const html = `
            <div class="calculation-result">
                <h5 class="text-white mb-3">
                    <i class="fas fa-check-circle me-2"></i>
                    Calculation Complete
                </h5>
                
                <div class="row g-3 mb-4">
                    <div class="col-md-3">
                        <div class="text-white-50 small">Reagent</div>
                        <div class="h6 text-white">${result.reagent}</div>
                    </div>
                    <div class="col-md-3">
                        <div class="text-white-50 small">Formula</div>
                        <div class="h6 text-white">${result.formula}</div>
                    </div>
                    <div class="col-md-3">
                        <div class="text-white-50 small">Molarity</div>
                        <div class="h6 text-white">${result.molarity} M</div>
                    </div>
                    <div class="col-md-3">
                        <div class="text-white-50 small">Volume</div>
                        <div class="h6 text-white">${result.volume_ml} mL</div>
                    </div>
                </div>
                
                <div class="row g-3 mb-4">
                    <div class="col-md-6">
                        <div class="text-white-50 small">Mass Needed</div>
                        <div class="display-6 text-white fw-bold">${result.mass_needed.toFixed(3)} g</div>
                    </div>
                    <div class="col-md-6">
                        <div class="text-white-50 small">Moles Required</div>
                        <div class="h4 text-white">${result.moles_needed.toFixed(6)} mol</div>
                    </div>
                </div>
                
                <div class="bg-white bg-opacity-10 rounded p-3">
                    <h6 class="text-white mb-2">
                        <i class="fas fa-list-ol me-2"></i>
                        Procedure Instructions
                    </h6>
                    <p class="text-white-50 mb-0">${result.instructions}</p>
                </div>
                
                <div class="mt-3 text-end">
                    <button class="btn btn-light btn-sm me-2" onclick="calculator.saveCalculation()">
                        <i class="fas fa-save me-1"></i>Save
                    </button>
                    <button class="btn btn-outline-light btn-sm me-2" onclick="calculator.exportCalculation()">
                        <i class="fas fa-download me-1"></i>Export
                    </button>
                    <button class="btn btn-outline-light btn-sm" onclick="calculator.shareCalculation()">
                        <i class="fas fa-share me-1"></i>Share
                    </button>
                </div>
            </div>
        `;
        
        contentDiv.innerHTML = html;
        resultsDiv.style.display = 'block';
        
        // Smooth scroll to results
        resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Store current calculation
        this.currentCalculation = result;
        
        // Add to history
        this.addToHistory(result);
    }
    
    addToHistory(calculation) {
        const historyItem = {
            ...calculation,
            timestamp: new Date().toISOString(),
            id: Date.now()
        };
        
        this.calculationHistory.unshift(historyItem);
        
        // Keep only last 10 calculations
        if (this.calculationHistory.length > 10) {
            this.calculationHistory = this.calculationHistory.slice(0, 10);
        }
        
        this.saveCalculationHistory();
        this.updateHistoryDisplay();
    }
    
    saveCalculationHistory() {
        try {
            localStorage.setItem('labmate-calc-history', JSON.stringify(this.calculationHistory));
        } catch (e) {
            console.warn('Could not save calculation history:', e);
        }
    }
    
    loadCalculationHistory() {
        try {
            const stored = localStorage.getItem('labmate-calc-history');
            if (stored) {
                this.calculationHistory = JSON.parse(stored);
                this.updateHistoryDisplay();
            }
        } catch (e) {
            console.warn('Could not load calculation history:', e);
            this.calculationHistory = [];
        }
    }
    
    updateHistoryDisplay() {
        // This would update a history panel if it exists on the page
        const historyContainer = document.getElementById('calculationHistory');
        if (!historyContainer) return;
        
        if (this.calculationHistory.length === 0) {
            historyContainer.innerHTML = '<p class="text-muted text-center">No calculations yet</p>';
            return;
        }
        
        const html = this.calculationHistory.map(calc => `
            <div class="card mb-2">
                <div class="card-body py-2">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <small class="fw-medium">${calc.reagent}</small><br>
                            <small class="text-muted">${calc.molarity}M × ${calc.volume_ml}mL = ${calc.mass_needed.toFixed(2)}g</small>
                        </div>
                        <div class="text-end">
                            <small class="text-muted">${new Date(calc.timestamp).toLocaleDateString()}</small><br>
                            <button class="btn btn-sm btn-outline-primary" onclick="calculator.loadCalculation(${calc.id})">
                                <i class="fas fa-redo"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
        
        historyContainer.innerHTML = html;
    }
    
    loadCalculation(id) {
        const calculation = this.calculationHistory.find(calc => calc.id === id);
        if (!calculation) return;
        
        // Fill form with stored calculation
        document.getElementById('reagent').value = calculation.reagent;
        document.getElementById('molarity').value = calculation.molarity;
        document.getElementById('volume').value = calculation.volume_ml;
        
        // Show the result
        this.displayCalculationResult(calculation);
    }
    
    saveCalculation() {
        if (!this.currentCalculation) return;
        
        // This would typically save to the server
        // For now, we'll just show a success message
        this.showToast('Calculation saved successfully!', 'success');
    }
    
    exportCalculation() {
        if (!this.currentCalculation) return;
        
        const calc = this.currentCalculation;
        const exportData = {
            reagent: calc.reagent,
            formula: calc.formula,
            molarity: calc.molarity,
            volume: calc.volume_ml,
            mass_needed: calc.mass_needed,
            instructions: calc.instructions,
            timestamp: new Date().toISOString()
        };
        
        // Create downloadable file
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `labmate-calculation-${calc.reagent.replace(/\s+/g, '-')}-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showToast('Calculation exported successfully!', 'success');
    }
    
    shareCalculation() {
        if (!this.currentCalculation) return;
        
        const calc = this.currentCalculation;
        const shareText = `LabMate AI Calculation:
${calc.reagent} (${calc.formula})
${calc.molarity} M in ${calc.volume_ml} mL
Mass needed: ${calc.mass_needed.toFixed(3)} g`;
        
        if (navigator.share) {
            navigator.share({
                title: 'LabMate AI Calculation',
                text: shareText
            });
        } else if (navigator.clipboard) {
            navigator.clipboard.writeText(shareText).then(() => {
                this.showToast('Calculation copied to clipboard!', 'success');
            });
        } else {
            // Fallback: show modal with text to copy
            alert(shareText);
        }
    }
    
    clearForm() {
        document.getElementById('calculatorForm').reset();
        
        // Clear validation states
        const inputs = document.querySelectorAll('#calculatorForm input, #calculatorForm select');
        inputs.forEach(input => this.clearInputError(input));
        
        // Hide results
        const resultsDiv = document.getElementById('results');
        if (resultsDiv) {
            resultsDiv.style.display = 'none';
        }
        
        this.currentCalculation = null;
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    showToast(message, type = 'info') {
        if (typeof window.LabMateAI !== 'undefined' && window.LabMateAI.showToast) {
            window.LabMateAI.showToast(message, type);
        } else {
            // Fallback
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
}

// Initialize calculator
const calculator = new CalculatorController();

// Global functions for compatibility
function clearCalculatorForm() {
    calculator.clearForm();
}

function exportCurrentCalculation() {
    calculator.exportCalculation();
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CalculatorController };
}
