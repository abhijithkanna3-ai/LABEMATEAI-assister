// LabMate AI - Voice Recognition Module
// Implements Web Speech API for voice commands

class VoiceController {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.isSupported = false;
        this.currentContext = 'general'; // general, calculator, msds, safety
        
        this.initializeVoiceRecognition();
        this.setupEventListeners();
    }
    
    initializeVoiceRecognition() {
        // Check for Web Speech API support
        if ('webkitSpeechRecognition' in window) {
            this.recognition = new webkitSpeechRecognition();
            this.isSupported = true;
        } else if ('SpeechRecognition' in window) {
            this.recognition = new SpeechRecognition();
            this.isSupported = true;
        } else {
            console.warn('Speech recognition not supported in this browser');
            this.isSupported = false;
            return;
        }
        
        // Configure speech recognition
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';
        this.recognition.maxAlternatives = 1;
        
        // Set up event handlers
        this.recognition.onstart = () => {
            this.isListening = true;
            this.updateVoiceStatus('Listening...', 'listening');
            this.updateVoiceButton(true);
        };
        
        this.recognition.onend = () => {
            this.isListening = false;
            this.updateVoiceStatus('', 'idle');
            this.updateVoiceButton(false);
        };
        
        this.recognition.onerror = (event) => {
            this.handleVoiceError(event.error);
        };
        
        this.recognition.onresult = (event) => {
            this.handleVoiceResult(event);
        };
    }
    
    setupEventListeners() {
        // Global keyboard shortcut
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                this.startVoiceCommand();
            }
        });
    }
    
    startVoiceCommand(context = 'general') {
        if (!this.isSupported) {
            this.showVoiceError('Voice recognition is not supported in your browser. Please use Chrome, Safari, or Edge.');
            return;
        }
        
        if (this.isListening) {
            this.stopVoiceCommand();
            return;
        }
        
        this.currentContext = context;
        
        try {
            this.recognition.start();
        } catch (error) {
            this.handleVoiceError(error.message);
        }
    }
    
    stopVoiceCommand() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }
    
    handleVoiceResult(event) {
        const transcript = event.results[0][0].transcript.toLowerCase().trim();
        const confidence = event.results[0][0].confidence;
        
        console.log('Voice command:', transcript, 'Confidence:', confidence);
        
        this.updateVoiceStatus(`Heard: "${transcript}"`, 'processing');
        
        // Process command based on context
        switch (this.currentContext) {
            case 'calculator':
                this.processCalculatorCommand(transcript);
                break;
            case 'msds':
                this.processMSDSCommand(transcript);
                break;
            case 'safety':
                this.processSafetyCommand(transcript);
                break;
            default:
                this.processGeneralCommand(transcript);
        }
    }
    
    processCalculatorCommand(transcript) {
        // Parse calculator commands like:
        // "Calculate 0.1 M NaCl for 250mL"
        // "How much sodium hydroxide for 0.5M in 500mL"
        // "I need 2 molar glucose for 1 liter"
        
        const patterns = {
            calculate: /calculate\s+(\d*\.?\d+)\s*(m|molar|mol)\s+(.+?)\s+for\s+(\d*\.?\d+)\s*(ml|milliliters?|l|liters?)/i,
            howMuch: /how\s+much\s+(.+?)\s+for\s+(\d*\.?\d+)\s*(m|molar|mol)\s+in\s+(\d*\.?\d+)\s*(ml|milliliters?|l|liters?)/i,
            need: /(?:i\s+)?need\s+(\d*\.?\d+)\s*(m|molar|mol)\s+(.+?)\s+for\s+(\d*\.?\d+)\s*(ml|milliliters?|l|liters?)/i
        };
        
        let match = null;
        let molarity, chemical, volume, volumeUnit;
        
        // Try different patterns
        if (match = transcript.match(patterns.calculate)) {
            molarity = parseFloat(match[1]);
            chemical = this.normalizeChemicalName(match[3]);
            volume = parseFloat(match[4]);
            volumeUnit = match[5].toLowerCase();
        } else if (match = transcript.match(patterns.howMuch)) {
            chemical = this.normalizeChemicalName(match[1]);
            molarity = parseFloat(match[2]);
            volume = parseFloat(match[4]);
            volumeUnit = match[5].toLowerCase();
        } else if (match = transcript.match(patterns.need)) {
            molarity = parseFloat(match[1]);
            chemical = this.normalizeChemicalName(match[3]);
            volume = parseFloat(match[4]);
            volumeUnit = match[5].toLowerCase();
        }
        
        if (match && molarity && chemical && volume) {
            // Convert volume to mL if needed
            if (volumeUnit.startsWith('l') && volumeUnit !== 'liter' && volumeUnit !== 'liters') {
                volume *= 1000; // Convert L to mL
            }
            
            this.fillCalculatorForm(chemical, molarity, volume);
            this.updateVoiceStatus(`Setting up calculation for ${chemical}`, 'success');
        } else {
            this.updateVoiceStatus('Could not understand the calculation. Please try again.', 'error');
            this.showVoiceHelp('calculator');
        }
    }
    
    processMSDSCommand(transcript) {
        // Parse MSDS commands like:
        // "Look up sodium chloride"
        // "MSDS for hydrochloric acid"
        // "Safety data for glucose"
        
        const patterns = {
            lookup: /(?:look\s+up|search\s+for|find)\s+(.+)/i,
            msds: /msds\s+(?:for\s+)?(.+)/i,
            safety: /safety\s+data\s+(?:for\s+)?(.+)/i,
            chemical: /(.+)/i // Fallback - treat entire command as chemical name
        };
        
        let chemical = null;
        let match = null;
        
        if (match = transcript.match(patterns.lookup)) {
            chemical = this.normalizeChemicalName(match[1]);
        } else if (match = transcript.match(patterns.msds)) {
            chemical = this.normalizeChemicalName(match[1]);
        } else if (match = transcript.match(patterns.safety)) {
            chemical = this.normalizeChemicalName(match[1]);
        } else {
            chemical = this.normalizeChemicalName(transcript);
        }
        
        if (chemical) {
            this.performMSDSSearch(chemical);
            this.updateVoiceStatus(`Searching MSDS for ${chemical}`, 'success');
        } else {
            this.updateVoiceStatus('Could not understand the chemical name. Please try again.', 'error');
        }
    }
    
    processSafetyCommand(transcript) {
        // Parse safety commands like:
        // "Spill protocol"
        // "Fire emergency"
        // "Eye wash procedure"
        
        const safetyCommands = {
            'spill': ['spill', 'chemical spill', 'spill protocol'],
            'fire': ['fire', 'fire emergency', 'fire protocol'],
            'exposure': ['exposure', 'chemical exposure', 'eye wash', 'emergency shower'],
            'emergency': ['emergency', 'general emergency', 'help']
        };
        
        let commandType = null;
        
        for (const [type, keywords] of Object.entries(safetyCommands)) {
            if (keywords.some(keyword => transcript.includes(keyword))) {
                commandType = type;
                break;
            }
        }
        
        if (commandType) {
            this.showSafetyProtocol(commandType);
            this.updateVoiceStatus(`Showing ${commandType} protocol`, 'success');
        } else {
            this.updateVoiceStatus('Could not identify safety protocol. Please try again.', 'error');
            this.showVoiceHelp('safety');
        }
    }
    
    processGeneralCommand(transcript) {
        // Handle general navigation commands
        const navigationCommands = {
            'dashboard': ['dashboard', 'home', 'main'],
            'calculator': ['calculator', 'calculate', 'reagent'],
            'msds': ['msds', 'safety data', 'material safety'],
            'safety': ['safety', 'emergency', 'protocols'],
            'documentation': ['documentation', 'reports', 'experiments'],
            'activity': ['activity', 'logs', 'history']
        };
        
        let targetPage = null;
        
        for (const [page, keywords] of Object.entries(navigationCommands)) {
            if (keywords.some(keyword => transcript.includes(keyword))) {
                targetPage = page;
                break;
            }
        }
        
        if (targetPage) {
            this.navigateToPage(targetPage);
            this.updateVoiceStatus(`Navigating to ${targetPage}`, 'success');
        } else {
            this.updateVoiceStatus('Command not recognized. Try "calculator", "MSDS", or "safety".', 'error');
        }
    }
    
    normalizeChemicalName(name) {
        // Clean up and normalize chemical names
        name = name.trim().toLowerCase();
        
        // Common aliases and corrections
        const aliases = {
            'nacl': 'sodium chloride',
            'naoh': 'sodium hydroxide',
            'hcl': 'hydrochloric acid',
            'h2so4': 'sulfuric acid',
            'sulfuric': 'sulfuric acid',
            'hydrochloric': 'hydrochloric acid',
            'salt': 'sodium chloride',
            'caustic soda': 'sodium hydroxide',
            'lye': 'sodium hydroxide',
            'muriatic acid': 'hydrochloric acid',
            'glucose': 'glucose',
            'sugar': 'glucose',
            'ethanol': 'ethanol',
            'alcohol': 'ethanol',
            'acetic acid': 'acetic acid',
            'vinegar': 'acetic acid'
        };
        
        // Check for exact matches first
        if (aliases[name]) {
            return aliases[name];
        }
        
        // Check for partial matches
        for (const [alias, fullName] of Object.entries(aliases)) {
            if (name.includes(alias) || alias.includes(name)) {
                return fullName;
            }
        }
        
        // Return title case version
        return name.split(' ').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }
    
    fillCalculatorForm(chemical, molarity, volume) {
        const reagentSelect = document.getElementById('reagent');
        const molarityInput = document.getElementById('molarity');
        const volumeInput = document.getElementById('volume');
        
        if (reagentSelect && molarityInput && volumeInput) {
            // Try to find matching option in select
            const options = Array.from(reagentSelect.options);
            const matchingOption = options.find(option => 
                option.text.toLowerCase().includes(chemical.toLowerCase()) ||
                chemical.toLowerCase().includes(option.text.toLowerCase())
            );
            
            if (matchingOption) {
                reagentSelect.value = matchingOption.value;
            }
            
            molarityInput.value = molarity;
            volumeInput.value = volume;
            
            // Highlight the form
            [reagentSelect, molarityInput, volumeInput].forEach(input => {
                input.classList.add('border-primary');
                setTimeout(() => input.classList.remove('border-primary'), 2000);
            });
        }
    }
    
    performMSDSSearch(chemical) {
        const searchInput = document.getElementById('msdsSearch');
        if (searchInput) {
            searchInput.value = chemical;
            // Trigger search if function exists
            if (typeof searchMSDS === 'function') {
                searchMSDS();
            }
        }
    }
    
    showSafetyProtocol(type) {
        const modalMap = {
            'spill': 'spillModal',
            'fire': 'fireModal',
            'exposure': 'exposureModal',
            'emergency': 'generalModal'
        };
        
        const modalId = modalMap[type];
        if (modalId) {
            const modalElement = document.getElementById(modalId);
            if (modalElement) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
            }
        }
    }
    
    navigateToPage(page) {
        const urls = {
            'dashboard': '/',
            'calculator': '/calculator',
            'msds': '/msds',
            'safety': '/safety',
            'documentation': '/documentation',
            'activity': '/activity_logs'
        };
        
        if (urls[page]) {
            window.location.href = urls[page];
        }
    }
    
    updateVoiceStatus(message, type = 'info') {
        const statusElements = document.querySelectorAll('#voiceStatus, .voice-status');
        statusElements.forEach(element => {
            element.textContent = message;
            element.className = `voice-status text-${type}`;
        });
    }
    
    updateVoiceButton(isListening) {
        const voiceButtons = document.querySelectorAll('#voiceBtn, .voice-btn');
        voiceButtons.forEach(button => {
            if (isListening) {
                button.classList.add('recording');
                button.innerHTML = '<i class="fas fa-stop me-2"></i>Stop Listening';
            } else {
                button.classList.remove('recording');
                button.innerHTML = '<i class="fas fa-microphone me-2"></i>Start Voice Command';
            }
        });
    }
    
    handleVoiceError(error) {
        console.error('Voice recognition error:', error);
        
        let message = 'Voice recognition error. ';
        switch (error) {
            case 'no-speech':
                message += 'No speech was detected. Please try again.';
                break;
            case 'audio-capture':
                message += 'Microphone access denied or not available.';
                break;
            case 'not-allowed':
                message += 'Microphone permission denied. Please allow microphone access.';
                break;
            case 'network':
                message += 'Network error. Please check your connection.';
                break;
            default:
                message += 'Please try again.';
        }
        
        this.updateVoiceStatus(message, 'error');
        this.showVoiceError(message);
    }
    
    showVoiceError(message) {
        if (typeof showToast === 'function') {
            showToast(message, 'danger');
        } else if (window.LabMateAI && window.LabMateAI.showToast) {
            window.LabMateAI.showToast(message, 'danger');
        } else {
            alert(message);
        }
    }
    
    showVoiceHelp(context) {
        const helpMessages = {
            calculator: 'Try: "Calculate 0.1 M sodium chloride for 250 mL" or "How much glucose for 0.5 M in 500 mL"',
            msds: 'Try: "Look up hydrochloric acid" or "MSDS for sodium hydroxide"',
            safety: 'Try: "Spill protocol", "Fire emergency", or "Chemical exposure"'
        };
        
        const message = helpMessages[context] || 'Voice commands available for calculator, MSDS lookup, and safety protocols.';
        
        setTimeout(() => {
            this.updateVoiceStatus(message, 'info');
        }, 2000);
    }
}

// Initialize voice controller
const voiceController = new VoiceController();

// Global functions for compatibility
function startVoiceCommand(context = 'general') {
    voiceController.startVoiceCommand(context);
}

function stopVoiceCommand() {
    voiceController.stopVoiceCommand();
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { VoiceController, startVoiceCommand, stopVoiceCommand };
}
