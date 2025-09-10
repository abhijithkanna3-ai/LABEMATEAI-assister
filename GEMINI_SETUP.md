# Gemini API Setup for LabMate AI

## Getting Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

## Setting Up the API Key

### Option 1: Environment Variable (Recommended)
Set the environment variable in your system:
```bash
export GEMINI_API_KEY="your_api_key_here"
```

### Option 2: Direct Configuration
Edit the `enhanced_chatbot.py` file and replace:
```python
self.gemini_api_key = os.environ.get('GEMINI_API_KEY')
```
with:
```python
self.gemini_api_key = "your_api_key_here"
```

## Features with Gemini Integration

- **Intelligent Responses**: Context-aware answers based on your experiment history
- **Experiment Discussion**: Chat about your past experiments and get insights
- **Personalized Suggestions**: Recommendations based on your lab work
- **Advanced Chemistry Help**: More sophisticated chemical and safety guidance
- **Natural Language Processing**: Better understanding of complex queries

## Fallback Mode

If no API key is provided, the chatbot will use a rule-based system that still provides:
- Chemical calculations
- Basic chemical information
- Safety guidance
- Experiment help

## Testing

After setting up the API key, restart your application and try asking:
- "Tell me about my recent experiments"
- "What calculations have I done recently?"
- "Help me plan a new experiment based on my history"
- "What safety precautions should I take for my next experiment?"
