# 🚀 CRYPTORA – AI-Powered Cryptocurrency Conversational Assistant
### **Built by Vaibhav Gupta**

## 📌 Project Overview
Cryptora is a full-stack AI cryptocurrency assistant that provides:

- Real-time price, market cap, volume & supply  
- OHLC & market chart trend analysis  
- Historical price queries  
- NFT and exchange data  
- Crypto news with sentiment, event, and date-based filtering  
- Domain-specific reasoning via a LoRA fine-tuned LLaMA3.2-3B model  
- Voice input + text-to-speech output  
- Memory-enhanced conversations  
- Animated premium UI  

## 🌐 Live Deployment
https://cryptora-cryptocurrency-chatbot-production.up.railway.app/

## 📦 Hugging Face Resources
Dataset: https://huggingface.co/datasets/Vaibhav7625/crypto_qna_dataset  
Model: https://huggingface.co/Vaibhav7625/Crypto-Llama-3B-GGUF  

## 🧠 System Architecture
```
User (Text / Voice)
        ↓
Frontend (HTML + CSS + JS)
        ↓
Flask Backend (flask_app.py)
        ↓
Intent Engine (Gemini Flash)
        ↓
Routing Logic (gemini_core.py)
 ├── CoinGecko API
 ├── CryptoPanic API
 ├── LLaMA LoRA Model
 └── Memory Adapter
        ↓
Response → UI + Voice Output
```

## ✨ Features
- Intent detection (18+ types)
- Advanced news engine
- Real-time crypto analytics
- LLaMA3.2 LoRA domain reasoning
- Voice input + auto speak output
- Responsive animated UI

## 📁 Folder Structure
```
cryptora/
├── flask_app.py
├── gemini_core.py
├── Dockerfile
├── requirements.txt
├── templates/index.html
└── static/
    ├── css/
    ├── js/
    └── img/
```

## ⚙️ Installation
```
git clone https://github.com/Vaibhav7625/Cryptora-CryptoCurrency-Chatbot
pip install -r requirements.txt
```

Create `.env`:
```
GEMINI_API_KEY=
CRYPTO_PANIC_API_KEY=
```

Run:
```
python flask_app.py
```

## 🐳 Docker
```
docker build -t cryptora .
docker run -p 5000:5000 cryptora
```
## 🔧 Technical Details
APIs Used

- CoinGecko → live data, charts, OHLC, categories
- CryptoPanic → filtered and event-based news
- Newspaper3k → article summaries
- HuggingFace Model → LoRA inference endpoint
- Gemini Flash → intent parsing & metadata extraction


Memory System

Tracks:
- last crypto
- last date
- last intent

Enables follow-up queries like:
> “And what about Ethereum?”


Frontend Logic Includes:

- live voice recognition
- auto-speak mode
- real-time animations
- time-stamped messages
```

## 👨‍💻 Author
Vaibhav Gupta
```

## 🌟 Thank you for checking out our project!
