# Ollama Setup Guide for AI Auditor

## 🚀 Quick Setup (Free LLM Alternative)

### Option 1: Local Ollama (Recommended)

**1. Install Ollama:**
```bash
# Windows (PowerShell)
winget install Ollama.Ollama

# Or download from: https://ollama.ai/download
```

**2. Start Ollama:**
```bash
ollama serve
```

**3. Pull a Model:**
```bash
# Llama 3.1 (8B) - Good balance of speed and quality
ollama pull llama3.1:8b

# Or try other models:
ollama pull mistral:7b
ollama pull codellama:7b
ollama pull neural-chat:7b
```

**4. Configure Azure Environment Variables:**
- Go to Azure Portal → `valuation-backend` → Environment variables
- Add these variables:
  - `USE_OLLAMA` = `true`
  - `OLLAMA_BASE_URL` = `http://localhost:11434` (or your Ollama server URL)
  - `OLLAMA_MODEL` = `llama3.1:8b`

### Option 2: Cloud Ollama (Free)

**1. Use Groq (Free Tier):**
- Go to: https://console.groq.com/
- Get free API key
- Set environment variables:
  - `USE_OLLAMA` = `false`
  - `GROQ_API_KEY` = `your_groq_key`
  - `GROQ_MODEL` = `llama3-8b-8192`

**2. Use Hugging Face (Free):**
- Go to: https://huggingface.co/settings/tokens
- Get free API token
- Set environment variables:
  - `USE_OLLAMA` = `false`
  - `HF_API_KEY` = `your_hf_token`
  - `HF_MODEL` = `microsoft/DialoGPT-medium`

## 🎯 Training Your AI Auditor

### 1. Custom System Prompt
The system prompt is already optimized for auditing. You can customize it in `simple_app.py`:

```python
SYSTEM_PROMPT = """You are an expert AI Valuation Auditor..."""
```

### 2. Training Data
Add your specific audit procedures and methodologies:

```python
# Add to system prompt
AUDIT_METHODOLOGIES = """
- IFRS 13 compliance checklist
- Risk assessment procedures
- Documentation requirements
- Quality control processes
"""
```

### 3. Feedback Loop
The AI learns from each interaction. Provide feedback:
- "That's correct"
- "More detail needed"
- "Focus on compliance aspects"

### 4. Specialized Training
Train on specific areas:
- "Explain CVA calculation"
- "What are the audit risks for derivatives?"
- "How do I validate yield curves?"

## 🔧 Advanced Configuration

### Custom Models
```bash
# Pull specialized models
ollama pull codellama:13b  # For code analysis
ollama pull neural-chat:7b  # For conversational AI
ollama pull mistral:7b  # For general purpose
```

### Performance Tuning
```python
# In simple_app.py, adjust these parameters:
"options": {
    "temperature": 0.7,    # Creativity (0.1-1.0)
    "top_p": 0.9,         # Diversity (0.1-1.0)
    "max_tokens": 1000,   # Response length
    "repeat_penalty": 1.1  # Avoid repetition
}
```

## 🎓 Training Strategies

### 1. Role-Playing
- "Act as a senior auditor reviewing this valuation"
- "You are training a junior auditor"
- "Explain this as if to a client"

### 2. Scenario-Based Learning
- "What if the yield curve is inverted?"
- "How do you handle stale market data?"
- "What are the risks of model validation?"

### 3. Progressive Complexity
- Start with basic concepts
- Gradually introduce complex scenarios
- Build expertise over time

## 🚀 Benefits of Ollama

✅ **Free** - No API costs
✅ **Local** - Your data stays private
✅ **Customizable** - Train on your specific needs
✅ **Fast** - No network latency
✅ **Reliable** - No quota limits
✅ **Trainable** - Learn from interactions

## 🔄 Switching Between LLMs

You can easily switch between:
- Ollama (local, free)
- OpenAI (cloud, paid)
- Groq (cloud, free tier)
- Hugging Face (cloud, free)

Just change the environment variables in Azure!
