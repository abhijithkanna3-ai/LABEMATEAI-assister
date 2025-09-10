import os
import logging

# Try to import torch and transformers, make them optional
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    TORCH_AVAILABLE = True
except ImportError as e:
    TORCH_AVAILABLE = False
    torch = None
    AutoModelForCausalLM = None
    AutoTokenizer = None
    logging.warning(f"PyTorch/Transformers not available: {e}")

# Set up logging - reduce verbosity
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class ChemLLMIntegration:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_name = "AI4Chem/ChemLLM-7B-Chat-1.5-DPO"
        self.device = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
        self.is_loaded = False
        self.enabled = True  # Enable ChemLLM
        
        # Load the model
        self._load_model()
    
    def _load_model(self):
        """Load the ChemLLM model and tokenizer"""
        if not TORCH_AVAILABLE:
            logger.error("❌ PyTorch/Transformers not available. Cannot load ChemLLM model.")
            self.is_loaded = False
            self.model = None
            self.tokenizer = None
            return
            
        try:
            # logger.info(f"Loading ChemLLM model: {self.model_name}")
            # logger.info(f"Using device: {self.device}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # Load model with appropriate settings
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            
            self.is_loaded = True
            # logger.info("✅ ChemLLM model loaded successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to load ChemLLM model: {e}")
            self.is_loaded = False
            self.model = None
            self.tokenizer = None
    
    def is_available(self):
        """Check if the model is available and loaded"""
        return self.enabled and self.is_loaded and self.model is not None and self.tokenizer is not None
    
    def generate_response(self, prompt, max_length=512, temperature=0.7, top_p=0.9):
        """
        Generate a response using ChemLLM
        
        Args:
            prompt (str): Input prompt/question
            max_length (int): Maximum length of generated response
            temperature (float): Sampling temperature
            top_p (float): Top-p sampling parameter
            
        Returns:
            str: Generated response or error message
        """
        if not TORCH_AVAILABLE:
            return "ChemLLM requires PyTorch and Transformers libraries. Please install them using: pip install torch transformers"
        
        if not self.enabled:
            return "ChemLLM is temporarily disabled. Please use the regular chatbot for chemistry assistance."
        
        if not self.is_available():
            return "ChemLLM model is not available. Please check the model installation and dependencies."
        
        # Add timeout protection for very long responses (Windows compatible)
        import threading
        import time
        
        timeout_occurred = threading.Event()
        
        def timeout_handler():
            time.sleep(30)  # 30 second timeout
            timeout_occurred.set()
        
        timeout_thread = threading.Thread(target=timeout_handler)
        timeout_thread.daemon = True
        timeout_thread.start()
        
        try:
            # Prepare the prompt with chemistry context
            formatted_prompt = self._format_prompt(prompt)
            
            # Tokenize input
            inputs = self.tokenizer(
                formatted_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=1024,
                padding=True
            )
            
            # Move to device if available
            if self.device != "cpu":
                inputs = inputs.to(self.device)
            
            # Check for timeout before generation
            if timeout_occurred.is_set():
                raise TimeoutError("Model generation timed out")
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=inputs['input_ids'],
                    attention_mask=inputs['attention_mask'] if 'attention_mask' in inputs else None,
                    max_new_tokens=max_length,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.1,
                    use_cache=False  # Disable KV cache to avoid the shape error
                )
            
            # Decode response - handle potential None outputs
            if outputs is not None and len(outputs) > 0 and outputs[0] is not None and len(outputs[0]) > 0:
                try:
                    # Simple approach - decode the entire output and clean it
                    response = self.tokenizer.decode(
                        outputs[0],
                        skip_special_tokens=True
                    ).strip()
                    
                    # Remove the input prompt from the response
                    if formatted_prompt in response:
                        response = response.replace(formatted_prompt, "").strip()
                    
                except Exception as decode_error:
                    logger.error(f"Error decoding response: {decode_error}")
                    response = "I apologize, but I couldn't generate a proper response. Please try again."
            else:
                response = "I apologize, but I couldn't generate a proper response. Please try again."
            
            # Clean up response
            response = self._clean_response(response)
            
            return response
            
        except TimeoutError:
            logger.error("Model generation timed out")
            return "I apologize, but the model is taking too long to respond. Please try a shorter or simpler question."
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I encountered an error while processing your chemistry question: {str(e)}"
        finally:
            # Clean up timeout thread
            timeout_thread.join(timeout=1)
    
    def _format_prompt(self, user_question):
        """Format the user question with appropriate context for chemistry"""
        prompt = f"""You are LabMate AI, an expert chemistry assistant. You have deep knowledge of:
- Chemical reactions and mechanisms
- Laboratory procedures and techniques
- Safety protocols and chemical hazards
- Calculations and formulas
- Chemical properties and structures
- Experimental design and analysis

User Question: {user_question}

Please provide a comprehensive, accurate, and helpful response. If the question involves calculations, show your work step by step. Always prioritize safety in your recommendations.

Answer:"""
        
        return prompt
    
    def _clean_response(self, response):
        """Clean and format the generated response"""
        # Remove any remaining prompt text
        if "Answer:" in response:
            response = response.split("Answer:")[-1].strip()
        
        # Remove any incomplete sentences at the end
        sentences = response.split('.')
        if len(sentences) > 1 and not sentences[-1].strip():
            response = '.'.join(sentences[:-1]) + '.'
        
        # Ensure response is not empty
        if not response.strip():
            response = "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
        
        return response.strip()
    
    def get_model_info(self):
        """Get information about the loaded model"""
        if not self.enabled:
            return {
                "status": "disabled",
                "model_name": self.model_name,
                "device": "unknown",
                "error": "ChemLLM is temporarily disabled",
                "model_type": "ChemLLM-7B-Chat-1.5-DPO"
            }
        
        if not TORCH_AVAILABLE:
            return {
                "status": "dependencies_missing",
                "model_name": self.model_name,
                "device": "unknown",
                "error": "PyTorch/Transformers not installed",
                "model_type": "ChemLLM-7B-Chat-1.5-DPO"
            }
        
        if not self.is_available():
            return {
                "status": "not_loaded",
                "model_name": self.model_name,
                "device": self.device,
                "error": "Model failed to load",
                "model_type": "ChemLLM-7B-Chat-1.5-DPO"
            }
        
        return {
            "status": "loaded",
            "model_name": self.model_name,
            "device": self.device,
            "is_available": True,
            "model_type": "ChemLLM-7B-Chat-1.5-DPO"
        }

# Global instance
chemllm = ChemLLMIntegration()

def is_chemllm_available():
    """Check if ChemLLM is available"""
    return chemllm.is_available()

def generate_chemllm_response(prompt, **kwargs):
    """Generate a response using ChemLLM"""
    return chemllm.generate_response(prompt, **kwargs)

def get_chemllm_info():
    """Get ChemLLM model information"""
    return chemllm.get_model_info()
