import google.generativeai as genai
import requests
from datetime import datetime, timedelta
from langchain_community.chat_message_histories import ChatMessageHistory
from googlesearch import search
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from newspaper import Article
from googlesearch import search
import time
import re
from dotenv import load_dotenv
import os

load_dotenv()

# Fetch API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CRYPTO_PANIC_API_KEY = os.getenv("CRYPTO_PANIC_API_KEY")

# Configure APIs
genai.configure(api_key=GEMINI_API_KEY)

BASE_URL = "https://cryptopanic.com/api/v1/posts/"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

class MemoryAdapter:
    def __init__(self):
        self._hist = ChatMessageHistory()

    def save_context(self, inputs, outputs):
        user_text = inputs.get("input", "") if isinstance(inputs, dict) else inputs
        if isinstance(outputs, dict):
            ai_text = outputs.get("output", "")
        else:
            ai_text = outputs or ""

        if user_text:
            try:
                self._hist.add_user_message(user_text)
            except:
                self._hist.add_message({"type": "human", "content": user_text})

        if ai_text:
            try:
                self._hist.add_ai_message(ai_text)
            except:
                self._hist.add_message({"type": "ai", "content": ai_text})

    @property
    def chat_memory(self):
        class ChatMemoryWrapper:
            def __init__(self, hist):
                self.hist = hist

            @property
            def messages(self):
                try:
                    return self.hist.messages
                except:
                    return []
        return ChatMemoryWrapper(self._hist)

memory = MemoryAdapter()

# Function to extract intent and cryptocurrency from user input using Gemini
def detect_intent_and_crypto(user_input):
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
    You are an AI that extracts structured data from cryptocurrency, NFT, and exchange-related queries.
    Your job is to identify:
    - The **intent** of the query.
    - The **cryptocurrency / NFT / Exchange name** in the correct CoinGecko API format.
    - The **date** (if the query involves historical data, including relative terms like "6 months ago").
    - The **number of results/days** (if applicable, e.g., "top 10 gainers" or "market chart for 7 days").

    **Possible intents:**  
    - "price" (if asking about price)  
    - "market_cap" (if asking about market cap)  
    - "supply" (if asking about supply)  
    - "volume" (if asking about 24h trading volume)  
    - "history" (if asking for historical data on a specific date or a relative date)  
    - "market_chart" (if asking for a chart of market trends)  
    - "ohlc" (if asking for OHLC price data)  
    - "list_coins" (if asking for a list of supported coins)  
    - "categories" (if asking about crypto categories)  
    - "nft" (NFT price or details)
    - "exchange" (specific exchange details)
    - "list_exchanges" (list of exchanges)
    - "news" (if asking for crypto, NFT, or exchange-related news)
    - "previous" (if the query references a previous response (e.g., "What about ETH?"))
    - "general" (if asking a general crypto questions, exchanges, security, best platforms, or recommendations)  

    **Rules:**  
    - Convert any cryptocurrency symbol (e.g., BTC, ETH, SOL) into its full CoinGecko-compatible name.  
    - Identify NFT names if the user asks about NFTs.
    - Identify exchange names if the user asks about crypto exchanges.
    - Ensure the cryptocurrency name is **lowercase** and correctly formatted for API use.
    - If the user provides a relative time frame (e.g., "6 months ago"), calculate the exact **DD-MM-YYYY** date.
    - If no valid crypto is found, return "unknown".  
    - If the user does not specify a date, return "unknown".  
    - If a **number** is mentioned (like "top 10 coins" or "chart for 7 days"), extract it.  

    **Response format:**  
    Intent: [intent]  
    Asset: [crypto/NFT/exchange name]  
    Date: [exact DD-MM-YYYY date or 'unknown']  
    Number: [number of results/days]  

    **Example Queries & Responses:**  
    ---
    **Query:** "What was the price of BTC 6 months ago?"  
    **Response:**  
    Intent: history  
    Crypto: bitcoin  
    Date: { (datetime.today() - timedelta(days=30*6)).strftime('%d-%m-%Y') }  
    Number: unknown  

    ---
    **Query:** "What was the price of BTC 10 days ago?"  
    **Response:**  
    Intent: history  
    Crypto: bitcoin  
    Date: { (datetime.today() - timedelta(days=10)).strftime('%d-%m-%Y') }  
    Number: unknown  
    ---

    **Query:** "List the top 10 cryptocurrencies."  
    **Response:**  
    Intent: list_coins  
    Crypto: unknown  
    Date: unknown  
    Number: 10  

    ---
    **Query:** "Show me BTC market chart for 7 days."  
    **Response:**  
    Intent: market_chart  
    Crypto: bitcoin  
    Date: unknown  
    Number: 7  

    ---
    **Query:** "What was the price of SOL on 15-08-2024?"  
    **Response:**  
    Intent: history  
    Crypto: solana  
    Date: 15-08-2024  
    Number: unknown  

    ---
    **Query:** "Tell me about OpenSea NFT collection."  
    **Response:**  
    Intent: nft  
    Asset: opensea  
    Date: unknown  
    Number: unknown  

    ---
    **Query:** "How secure is Kraken exchange?"  
    **Response:**  
    Intent: general  
    Asset: kraken  
    Date: unknown  
    Number: unknown

    ---
    **Query:** "List top 5 crypto exchanges."  
    **Response:**  
    Intent: list_exchanges  
    Asset: unknown  
    Date: unknown  
    Number: 5  

    ---
    Now, extract the intent, asset, date (converted if relative), and number of results from this query:

    **User Query:** "{user_input}"
    """

    response = model.generate_content(prompt).text

    intent, asset, date, number = "unknown", "unknown", "unknown", "unknown"

    for line in response.split("\n"):
        if "Intent:" in line:
            intent = line.split(":")[1].strip().lower()
        if "Asset:" in line:
            asset = line.split(":")[1].strip().lower()
        if "Date:" in line:
            date = line.split(":")[1].strip().lower()
        if "Number:" in line:
            number = line.split(":")[1].strip().lower()

    return intent, asset, date, number

def classify_news_intent(user_input):
    """
    Classifies the user's intent within the news category and extracts event keywords if applicable.
    Returns in format: "<intent>,<keyword>" where keyword is 'none' if not relevant.
    """
    prompt = f"""
You are an AI assistant. A user is asking for cryptocurrency news. 

Your job is to:
1. Classify the sub-intent of their request from the following options:
    - general_news
    - news_by_sentiment
    - event_related_news
    - summarize_article
    - breaking_news
    - news_by_date
    - news_by_asset
    - unknown

2. If the sub-intent is 'event_related_news', also extract the most relevant keyword (one or two words only) that describes the event. Example: crash, hack, ETF, lawsuit, rug pull, scam, ban, etc.

If the sub-intent is not event-related, return 'none' for the keyword.

Respond in this format ONLY: "<intent>,<keyword>"

User Query: "{user_input}"
"""
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip().lower()

def parse_flexible_date(date_str):
    # Convert relative dates like "6 months ago" to DD-MM-YYYY
    if "ago" in date_str:
        try:
            num, unit = date_str.split()[:2]
            num = int(num)

            if "day" in unit:
                target_date = datetime.today() - timedelta(days=num)
            elif "month" in unit:
                target_date = datetime.today() - timedelta(days=num * 30)
            elif "year" in unit:
                target_date = datetime.today() - timedelta(days=num * 365)
            else:
                return None, "Invalid time format. Please use days, months, or years."

            date_str = target_date.strftime("%d-%m-%Y")

        except ValueError:
            return None, "Invalid time format. Use numbers followed by days/months/years."

    try:
        requested_date = datetime.strptime(date_str, "%d-%m-%Y")
        return requested_date.date(), None
    except ValueError:
        return None, "Invalid date format. Please use DD-MM-YYYY."

def summarize_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        article.nlp()  # Enables natural language processing to generate a summary

        return {
            "title": article.title,
            "summary": article.summary
        }
    except Exception as e:
        return f"An error occurred: {e}"

def news_related_query(user_input, asset, date, number):
    intent_keyword = classify_news_intent(user_input)
    sub_intent, keyword = intent_keyword.split(",")

    if sub_intent == "previous":
        if memory.chat_memory.messages:
            last_output = memory.chat_memory.messages[-1].content
            last_values = last_output.split(",")
            sub_intent = last_values[0]
            if asset == "unknown": asset = last_values[1]
            if date == "unknown": date = last_values[2]
            if number == "unknown": number = last_values[3]
            if keyword == "none": keyword = last_values[4]
        else:
            return "⚠️ No previous data found in memory."

    # Save to memory
    memory.save_context({"input": user_input}, {
        "output": f"{sub_intent},{asset},{date},{number},{keyword}"
    })

    params = {
        "auth_token": CRYPTO_PANIC_API_KEY,
        "public": "true",
    }

    filter_by_date = False
    sentiment = "neutral"

    if sub_intent == "general_news":
        if asset != "unknown":
            params["currencies"] = asset
        params["kind"] = "news"

    elif sub_intent == "news_by_sentiment":
        if "bullish" in user_input.lower():
            sentiment = "bullish"
        elif "bearish" in user_input.lower():
            sentiment = "bearish"
        elif "important" in user_input.lower():
            sentiment = "important"
        if not sentiment:
            return "❓ Could not determine sentiment filter."
        params["filter"] = sentiment
        if asset != "unknown":
            params["currencies"] = asset

    elif sub_intent == "event_related_news":
        if keyword == "none":
            return "❓ No specific event keyword found."
        params["q"] = keyword
        if asset != "unknown":
            params["currencies"] = asset

    elif sub_intent == "news_by_asset":
        if asset == "unknown":
            return "⚠️ Please specify a crypto asset."
        params["currencies"] = asset

    elif sub_intent == "news_by_date":
        if date == "unknown":
            return "📅 Please specify the date for historical news."

        date_obj, error = parse_flexible_date(date)
        if error:
            return f"⚠️ {error}"

        if asset != "unknown":
            params["currencies"] = asset

        filter_by_date = True

    elif sub_intent == "summarize_article":
        url = input("Please provide the article URL you'd like summarized: ")
        
        summary = summarize_article(url)
        
        # Checking if the result is a summary or an error
        if isinstance(summary, dict):
            return f"📰 **Title**: {summary['title']}\n\n📄 **Summary**: {summary['summary']}"
        else:
            return summary  # In case of an error, return the error message

    elif sub_intent == "breaking_news":
        params["filter"] = "hot"

    else:
        return "❓ I couldn't understand the specific type of news you're looking for."

    if number != "unknown":
        params["page_size"] = int(number)

    response = requests.get(BASE_URL, params=params)
    
    if response.status_code != 200:
        return f"🚨 API error: {response.status_code}"

    articles = response.json().get("results", [])

    articles = [
        a for a in articles
        if a.get("sentiment", "neutral").lower() == sentiment.lower()
    ]

    if sub_intent == "news_by_date" and filter_by_date:
        articles = [
            a for a in articles
            if datetime.strptime(a["published_at"][:10], "%Y-%m-%d").date() == date_obj
        ]

    if not articles:
        return "🔍 No relevant news found."
    
    articles=articles[:int(number) if number != "unknown" else 5]

    # Format news with descriptions and real article link
    return format_news_response(articles)

# Function to get real article link using Google Search
def get_article_link(article_name, news_website):
    query = f"{article_name} site:{news_website}"
    try:
        for url in search(query, num=1, stop=1, lang="en"):
            return url
    except Exception as e:
        print("Error:", e)
    return None

# Function to get article description from a URL using Selenium
def get_article_description(cryptopanic_url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.set_page_load_timeout(10)
        driver.get(cryptopanic_url)
        time.sleep(5)
        description_div = driver.find_element(By.CLASS_NAME, "description-body")
        description_text = description_div.text
    except Exception as e:
        description_text = f"Error fetching description."
    finally:
        driver.quit()

    return description_text

# Function to format the news response with extra details (Description and Real Link)
def format_news_response(articles):
    result = ""
    for a in articles:
        title = a.get("title", "No Title")
        url = a.get("url", "No URL")
        published_at = a.get("published_at", "")[:10]
        sentiment = a.get("sentiment", "Neutral").capitalize()
        domain = a.get("domain", "Unknown Source")
        try:
            description = get_article_description(url)  # if you're using Selenium for this
        except Exception as e:
            description = "cannot fetch the description"

        
        real_url = get_article_link(title, domain)
        url = real_url if real_url else url

        result += (
            f"📰 {title}\n"
            f"📅 Date: {published_at}\n"
            f"📊 Sentiment: {sentiment}\n"
            f"🌐 Source: {domain}\n"
            f"📝 Description: {description}\n"
            f"🔗 Real Article Link: {url}\n\n"
        )
    return result.strip()

def get_supported_coins(limit=20):
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Status:", response.status_code, response.text)
        return "Sorry, I couldn't fetch the list of cryptocurrencies."

    data = response.json()

    # ✅ Extract well-known cryptos (market cap > $1B)
    well_known_coins = [coin['name'] for coin in data if coin.get('market_cap', 0) > 1_000_000_000]

    # ✅ Limit based on user request
    well_known_coins = well_known_coins[:limit]

    # ✅ Format output with ranking numbers
    crypto_list = "\n".join([f"{i+1}. {coin}" for i, coin in enumerate(well_known_coins)])

    return f"Here are the **top {limit} cryptocurrencies**:\n{crypto_list}"

def get_historical_data(crypto, date_str):
    # ✅ Convert relative dates (e.g., "6 months ago") to an actual date
    if "ago" in date_str:
        try:
            num, unit = date_str.split()[:2]
            num = int(num)

            if "day" in unit:
                target_date = datetime.today() - timedelta(days=num)
            elif "month" in unit:
                target_date = datetime.today() - timedelta(days=num * 30)
            elif "year" in unit:
                target_date = datetime.today() - timedelta(days=num * 365)
            else:
                return "Invalid time format. Please use days, months, or years."

            date_str = target_date.strftime("%d-%m-%Y")

        except ValueError:
            return "Invalid time format. Please use numbers followed by days, months, or years."

    # ✅ Validate final date format
    try:
        requested_date = datetime.strptime(date_str, "%d-%m-%Y")
    except ValueError:
        return "Invalid date format. Please use DD-MM-YYYY."

    # ✅ Ensure the date is within the past 365 days (CoinGecko Limitation)
    today = datetime.today()
    one_year_ago = today - timedelta(days=365)

    if requested_date > today:
        return "❌ Future prices are not available. Please enter a past date within the last year."

    if requested_date < one_year_ago:
        return "❌ CoinGecko API provides historical data only for the last 365 days. Please enter a more recent date."

    # ✅ Fetch historical price from CoinGecko
    url = f"https://api.coingecko.com/api/v3/coins/{crypto}/history?date={requested_date.strftime('%d-%m-%Y')}&localization=false"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Status:", response.status_code, response.text)
        return f"Couldn't fetch historical data for {crypto} on {date_str}."

    data = response.json()

    if "market_data" not in data or "current_price" not in data["market_data"]:
        return f"No historical data available for {crypto} on {date_str}."

    price = data["market_data"]["current_price"].get("usd", "N/A")

    return f"On {date_str}, {crypto.capitalize()} was priced at **${price}**."


def get_market_chart(crypto, days=30):
    url = f"https://api.coingecko.com/api/v3/coins/{crypto}/market_chart?vs_currency=usd&days={days}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Status:", response.status_code, response.text)
        return f"Couldn't fetch market chart data for {crypto}."

    data = response.json()
    prices = data.get("prices", [])

    if len(prices) < 2:  # Not enough data to determine trend
        return f"No market trend data available for {crypto}."

    # Extract first & last price
    first_price = prices[0][1]   # Price X days ago
    latest_price = prices[-1][1]  # Most recent price

    # Determine trend
    if latest_price > first_price:
        trend = "📈 Uptrend (bullish)"
    elif latest_price < first_price:
        trend = "📉 Downtrend (bearish)"
    else:
        trend = "➡️ No major trend (stable)"

    return (f"Market trend for {crypto.capitalize()} over {days} days:\n"
            f"💰 Price {days} days ago: **${first_price:.2f}**\n"
            f"💰 Latest price: **${latest_price:.2f}**\n"
            f"📊 Trend: {trend}")

def get_ohlc(crypto, days=7):
    url = f"https://api.coingecko.com/api/v3/coins/{crypto}/ohlc?vs_currency=usd&days={days}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Status:", response.status_code, response.text)
        return f"Couldn't fetch OHLC data for {crypto}."

    data = response.json()
    if not data:
        return f"No OHLC data available for {crypto}."

    last_entry = data[-1]  # [timestamp, open, high, low, close]
    return (f"{crypto.capitalize()} OHLC Data (Last Entry):\n"
            f"Open: ${last_entry[1]}, High: ${last_entry[2]}, Low: ${last_entry[3]}, Close: ${last_entry[4]}")

def get_crypto_categories():
    url = "https://api.coingecko.com/api/v3/coins/categories"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Status:", response.status_code, response.text)
        return "Couldn't fetch crypto categories."

    data = response.json()
    categories = ", ".join([category["name"] for category in data[:10]])  # Limit to 10 categories

    return f"Some popular crypto categories: {categories}."

# ✅ Fetch NFT Data
def get_nft_data(nft_name):
    url = f"https://api.coingecko.com/api/v3/nfts/{nft_name}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Status:", response.status_code, response.text)
        return f"Couldn't fetch NFT data for {nft_name}."

    data = response.json()
    floor_price = data.get("floor_price", {}).get("usd", "N/A")
    market_cap = data.get("market_cap", {}).get("usd", "N/A")

    return f"NFT Collection: {nft_name.capitalize()}\n💰 Floor Price: **${floor_price}**\n📈 Market Cap: **${market_cap}**"

# ✅ Fetch List of Exchanges
def get_exchanges(limit=10):
    url = "https://api.coingecko.com/api/v3/exchanges"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Status:", response.status_code, response.text)
        return "Couldn't fetch the list of exchanges."

    data = response.json()
    exchange_list = "\n".join([f"{i+1}. {exchange['name']}" for i, exchange in enumerate(data[:limit])])

    return f"Here are the **top {limit} cryptocurrency exchanges**:\n{exchange_list}"

# ✅ Fetch Specific Exchange Details
def get_exchange_details(exchange):
    url = f"https://api.coingecko.com/api/v3/exchanges/{exchange}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Status:", response.status_code, response.text)
        return f"Couldn't fetch data for {exchange}."

    data = response.json()
    year_established = data.get("year_established", "N/A")
    country = data.get("country", "N/A")
    trade_volume = data.get("trade_volume_24h_btc", "N/A")

    return f"Exchange: {exchange.capitalize()}\n🌍 Country: **{country}**\n📅 Established: **{year_established}**\n📊 24h BTC Trade Volume: **{trade_volume} BTC**"

# Function to fetch crypto market data from CoinGecko API
def get_crypto_data(crypto, intent):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto}&vs_currencies=usd"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Status:", response.status_code, response.text)
        return "Sorry, I couldn't fetch the data. Try again later."

    data = response.json()

    if intent == "price":
        return f"The current price of {crypto.capitalize()} is ${data['market_data']['current_price']['usd']}"
    
    if intent == "market_cap":
        return f"The market cap of {crypto.capitalize()} is ${data['market_data']['market_cap']['usd']}"
    
    if intent == "supply":
        return f"The circulating supply of {crypto.capitalize()} is {data['market_data']['circulating_supply']} coins"
    
    if intent == "volume":
        return f"The 24h trading volume of {crypto.capitalize()} is ${data['market_data']['total_volume']['usd']}"

    return "I couldn't process your request."

def format_bold_text(text):
    # Replace * **bold text** * with <strong>bold text</strong>
    formatted_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    return formatted_text

def clean_incomplete_sentence(text):
    # Split text into sentences
    parts = re.split(r'(?<=[.!?])\s+', text)

    # If the last chunk does NOT end with punctuation → drop it
    if not re.search(r'[.!?]$', parts[-1]):
        parts = parts[:-1]

    return "\n".join(parts).strip()

def ask_gemini(query):
    try:
        url = "https://Vaibhav7625-Crypto-Llama-3B-Instruct.hf.space/infer"
        payload = {"prompt": query}
        
        response = requests.post(url, json=payload, timeout=300)
        result = response.json()["response"].strip()

        # Trim incomplete last line
        cleaned = clean_incomplete_sentence(result)

        return format_bold_text(cleaned.strip())

    except Exception as e:
        print("Error:", e)
        return f"An unexpected error occurred 😔\nTry again later."

# Function to process user input and decide which API to call
def process_user_input(user_input):
    intent, asset, date, number = detect_intent_and_crypto(user_input)

    try:
        number = int(number)
    except ValueError:
        number = 10  # Default value

    # ✅ Ensure number is within a valid range (1 to 100)
    number = max(1, min(number, 100)) 

    if intent == "previous":
        # Fetch the last stored message from memory
        if memory.chat_memory.messages:
            last_output = memory.chat_memory.messages[-1].content
            last_values = last_output.split(",")
            intent=last_values[0]
            if asset == "unknown": asset = last_values[1]
            if date == "unknown": date = last_values[2]
            if number == "unknown": number = last_values[3]
        else:
            return "No previous data found in memory."
        
    memory.save_context({"input": user_input}, {
        "output": f"{intent},{asset},{date},{number}"
        })
    
    if intent == "news":
        return news_related_query(user_input, asset, date, number)

    if intent in ["price", "market_cap", "supply", "volume"]:
        if asset != "unknown":
            return get_crypto_data(asset, intent)
        return "Please specify a cryptocurrency (e.g., Bitcoin, Ethereum)."

    if intent == "list_coins":
        return get_supported_coins(number)
    
    if intent == "nft" and asset != "unknown":
        return get_nft_data(asset)

    if intent == "list_exchanges":
        return get_exchanges(number)

    if intent == "exchange" and asset != "unknown":
        return get_exchange_details(asset)

    if intent == "history" and asset != "unknown" and date != "unknown":
        return get_historical_data(asset, date)

    if intent == "market_chart" and asset != "unknown":
        return get_market_chart(asset,number)

    if intent == "ohlc" and asset != "unknown":
        return get_ohlc(asset)

    if intent == "categories":
        return get_crypto_categories()

    if intent == "general":
        return ask_gemini(user_input)

    return "I'm not sure how to answer that. Try asking about a cryptocurrency or its market data."