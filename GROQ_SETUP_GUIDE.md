# Groq Setup Guide - FREE AI Agent

## 🆓 COMPLETELY FREE - NO PAYMENT EVER!

### ✅ Groq Free Tier:
- **14,400 requests per day** (more than enough!)
- **No credit card required**
- **No expiration date**
- **Fast inference** (very quick responses)

## 🚀 STEP-BY-STEP SETUP:

### Step 1: Get Groq API Key (2 minutes)

1. **Go to:** https://console.groq.com/
2. **Sign up** with your email (no credit card needed)
3. **Verify email** (check your inbox)
4. **Go to API Keys** section
5. **Click "Create API Key"**
6. **Copy your key** (starts with `gsk_...`)

### Step 2: Configure Azure (3 minutes)

1. **Go to Azure Portal:**
   - Navigate to `valuation-backend` App Service
   - Click **"Environment variables"** (under Settings)

2. **Add these variables:**
   ```
   USE_GROQ = true
   GROQ_API_KEY = your_groq_key_here
   GROQ_MODEL = llama-3.1-8b-instant
   ```

3. **Save and restart** the App Service

### Step 3: Test Your AI Agent

**Test the chat:**
- Go to your frontend
- Ask: "Hello! Are you using Groq now?"
- You should get a real LLM response (not fallback)

**Test AI Agent endpoints:**
```bash
# Explain results
POST /poc/ai-agent/explain-results
{"message": "Explain my valuation results"}

# Kick off valuation
POST /poc/ai-agent/kick-off-valuation  
{"message": "Help me create a new IRS swap"}

# Explain IFRS
POST /poc/ai-agent/explain-ifrs
{"message": "What is IFRS 13 compliance?"}
```

## 🎯 GROQ MODELS AVAILABLE:

### Free Models (No Payment Ever):
- **llama-3.1-8b-instant** - Fast, good quality (recommended)
- **llama-3.1-70b-versatile** - Higher quality, slightly slower
- **mixtral-8x7b-32768** - Good for complex reasoning
- **gemma-7b-it** - Google's model

### Model Comparison:
- **llama-3.1-8b-instant**: Fast, good for most tasks
- **llama-3.1-70b-versatile**: Best quality, use for complex analysis
- **mixtral-8x7b-32768**: Good for multi-step reasoning

## 🔧 TROUBLESHOOTING:

### If Still Getting Fallback Responses:

1. **Check Environment Variables:**
   - `USE_GROQ` must be `true` (not "True" or "TRUE")
   - `GROQ_API_KEY` must be your actual key
   - Restart the App Service after changes

2. **Check Azure Logs:**
   - Go to App Service → Log stream
   - Look for: "🔍 Using Groq LLM"
   - Should see: "✅ Groq response received"

3. **Test Groq Directly:**
   ```bash
   curl -X POST "https://api.groq.com/openai/v1/chat/completions" \
   -H "Authorization: Bearer YOUR_API_KEY" \
   -H "Content-Type: application/json" \
   -d '{
     "model": "llama3-8b-8192",
     "messages": [{"role": "user", "content": "Hello!"}]
   }'
   ```

## 🎓 TRAINING YOUR AI AGENT:

### Once Groq is Working:

1. **Start Conversations:**
   - "Explain this valuation result"
   - "Help me create a new swap"
   - "What's IFRS 13 compliance?"

2. **Provide Feedback:**
   - "That's correct, but add more detail"
   - "Focus on risk factors"
   - "Explain in simpler terms"

3. **Progressive Learning:**
   - AI learns from each interaction
   - Gets better at your specific needs
   - Adapts to your communication style

## 🚀 BENEFITS OF GROQ:

✅ **Completely Free** - No payment ever required
✅ **Fast Responses** - Very quick inference
✅ **High Quality** - Excellent model performance  
✅ **Reliable** - No quota issues
✅ **Easy Setup** - Just API key and environment variables
✅ **No Limits** - 14,400 requests per day is plenty

## 📊 USAGE ESTIMATES:

- **14,400 requests/day** = 432,000 requests/month
- **Typical chat:** 1-2 requests per message
- **Your usage:** Probably <100 requests/day
- **Plenty of headroom** for heavy usage

## 🎯 NEXT STEPS:

1. **Get your Groq API key** (2 minutes)
2. **Configure Azure environment variables** (3 minutes)  
3. **Test the chat** - should get real LLM responses
4. **Start training your AI auditor** through conversations
5. **Use the AI agent endpoints** for specialized tasks

**Your AI auditor will be fully functional and completely free!** 🚀
