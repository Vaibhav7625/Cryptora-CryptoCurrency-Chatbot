document.addEventListener('DOMContentLoaded', function () {
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');
    const initialMessageTime = document.getElementById('initial-message-time');

    initialMessageTime.textContent = getCurrentTime();

    function getCurrentTime() {
        const now = new Date();
        let hours = now.getHours();
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12 || 12;
        return `Today, ${hours}:${minutes} ${ampm}`;
    }

    function addMessage(message, isUser) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', isUser ? 'user-message' : 'bot-message');
        messageElement.innerHTML = message; // ✅ changed from textContent to innerHTML

        const timeElement = document.createElement('div');
        timeElement.classList.add('message-time');
        timeElement.textContent = getCurrentTime();
        messageElement.appendChild(timeElement);

        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        if (!isUser) createCoinBurst();
    }

    function showTypingIndicator() {
        typingIndicator.style.display = 'block';
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function hideTypingIndicator() {
        typingIndicator.style.display = 'none';
    }

    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        addMessage(message, true);
        messageInput.value = '';

        messageInput.classList.add('searching');
        setTimeout(() => {
            messageInput.classList.remove('searching');
        }, 1500);

        showTypingIndicator();

        try {
            const response = await fetch("/get-response", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message })
            });

            const data = await response.json();
            hideTypingIndicator();
            addMessage(data.response, false);
        } catch (err) {
            hideTypingIndicator();
            addMessage("⚠️ Error getting response. Try again.", false);
        }
    }

    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendMessage();
    });

    // Coin animations
    function createCoinBurst() {
        for (let i = 0; i < 5; i++) {
            setTimeout(() => {
                createFloatingCoin();
            }, i * 300);
        }
    }

    function createFloatingCoin() {
        const coin = document.createElement('div');
        coin.classList.add('coin');
        coin.style.left = Math.random() * 100 + '%';
        coin.style.bottom = '0';
        const size = Math.random() * 20 + 10;
        coin.style.width = size + 'px';
        coin.style.height = size + 'px';
        const duration = Math.random() * 5 + 5;
        coin.style.animationDuration = duration + 's';
        document.body.appendChild(coin);
        setTimeout(() => coin.remove(), duration * 1000);
    }

    setInterval(createFloatingCoin, 5000);
    setTimeout(createCoinBurst, 1000);

    // Falling coin effect
    function createCoinEffect() {
        const coin = document.createElement('div');
        coin.style.position = 'absolute';
        coin.style.width = Math.random() * 15 + 5 + 'px';
        coin.style.height = coin.style.width;
        coin.style.backgroundColor = 'rgba(212, 175, 55, 0.15)';
        coin.style.borderRadius = '50%';
        coin.style.border = '1px solid rgba(212, 175, 55, 0.3)';
        coin.style.zIndex = '-1';
        coin.style.left = Math.random() * 100 + 'vw';
        coin.style.top = '-20px';
        coin.style.animation = `fall ${Math.random() * 10 + 5}s linear forwards`;
        document.body.appendChild(coin);
        setTimeout(() => coin.remove(), 15000);
    }

    const styleSheet = document.createElement('style');
    styleSheet.textContent = `
        @keyframes fall {
            from { transform: translateY(0) rotate(0deg); }
            to { transform: translateY(100vh) rotate(360deg); }
        }
    `;
    document.head.appendChild(styleSheet);

    setInterval(createCoinEffect, 3000);
    messageInput.focus();
});

// Add this to your existing script.js file

// Detect if running in WebView environment
function isRunningInWebView() {
    // This is a heuristic - WebViews often have specific User Agent strings
    const userAgent = navigator.userAgent.toLowerCase();
    return /wv/.test(userAgent) || 
           /android/.test(userAgent) && /version\/[0-9.]+/.test(userAgent) ||
           /; wv\)/.test(userAgent);
}

// Apply WebView-specific adjustments
document.addEventListener('DOMContentLoaded', function() {
    if (isRunningInWebView()) {
        // Add a class to the body to enable WebView-specific CSS
        document.body.classList.add('webview-mode');
        
        // Make sure font size is appropriate for WebView
        document.body.style.fontSize = '14px';
        
        // Ensure proper viewport height in WebView
        function setAppHeight() {
            document.documentElement.style.setProperty('--app-height', `${window.innerHeight}px`);
            document.body.style.height = `${window.innerHeight}px`;
            
            // Adjust chat container height
            const headerHeight = document.querySelector('.header').offsetHeight;
            const inputContainerHeight = document.querySelector('.input-container').offsetHeight;
            const chatContainer = document.getElementById('chat-container');
            chatContainer.style.height = `calc(${window.innerHeight}px - ${headerHeight}px - ${inputContainerHeight}px)`;
        }
        
        // Set initial height and update on resize
        setAppHeight();
        window.addEventListener('resize', setAppHeight);
        
        // Fix scrolling issues in WebView
        const chatContainer = document.getElementById('chat-container');
        
        // Enhanced scroll to bottom function for WebView
        window.scrollToBottom = function() {
            setTimeout(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }, 100);
        };
        
        // Override the addMessage function with WebView optimizations if it exists
        if (window.addMessage) {
            const originalAddMessage = window.addMessage;
            window.addMessage = function(message, sender) {
                originalAddMessage(message, sender);
                window.scrollToBottom();
            };
        }
    }
});

// Fix WebView touch events if needed
document.addEventListener('touchstart', function() {}, {passive: true});