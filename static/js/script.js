document.addEventListener('DOMContentLoaded', function () {
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');
    const initialMessageTime = document.getElementById('initial-message-time');
    const micButton = document.getElementById('mic-button');
    const speakerButton = document.getElementById('speaker-button');

    // Voice recognition setup
    let recognition = null;
    let isRecording = false;
    
    // Speech synthesis setup
    let isSpeaking = false;
    let currentUtterance = null;

    // Initialize speech recognition if available
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onstart = function() {
            isRecording = true;
            micButton.classList.add('recording');
        };

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            messageInput.value = transcript;
            isRecording = false;
            micButton.classList.remove('recording');
        };

        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            isRecording = false;
            micButton.classList.remove('recording');
        };

        recognition.onend = function() {
            isRecording = false;
            micButton.classList.remove('recording');
        };
    } else {
        // Hide mic button if not supported
        if (micButton) micButton.style.display = 'none';
    }

    // Check speech synthesis support
    if (!('speechSynthesis' in window)) {
        if (speakerButton) speakerButton.style.display = 'none';
    }

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
        messageElement.innerHTML = message;

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
            
            // Auto-speak if speaker button is active
            if (speakerButton && speakerButton.dataset.autoSpeak === 'true') {
                speakText(data.response);
            }
        } catch (err) {
            hideTypingIndicator();
            addMessage("⚠️ Error getting response. Try again.", false);
        }
    }

    function toggleRecording() {
        if (!recognition) {
            alert('Speech recognition is not supported in your browser.');
            return;
        }

        if (isRecording) {
            recognition.stop();
        } else {
            try {
                recognition.start();
            } catch (err) {
                console.error('Error starting recognition:', err);
            }
        }
    }

    function speakText(text) {
        if (!('speechSynthesis' in window)) {
            alert('Text-to-speech is not supported in your browser.');
            return;
        }

        // Stop any ongoing speech
        if (isSpeaking) {
            window.speechSynthesis.cancel();
            isSpeaking = false;
            speakerButton.classList.remove('speaking');
            return;
        }

        // Remove HTML tags for speech
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = text;
        const cleanText = tempDiv.textContent || tempDiv.innerText || '';

        if (!cleanText.trim()) return;

        currentUtterance = new SpeechSynthesisUtterance(cleanText);
        currentUtterance.rate = 1.0;
        currentUtterance.pitch = 1.0;
        currentUtterance.volume = 1.0;

        currentUtterance.onstart = function() {
            isSpeaking = true;
            speakerButton.classList.add('speaking');
        };

        currentUtterance.onend = function() {
            isSpeaking = false;
            speakerButton.classList.remove('speaking');
        };

        currentUtterance.onerror = function(event) {
            console.error('Speech synthesis error:', event.error);
            isSpeaking = false;
            speakerButton.classList.remove('speaking');
        };

        window.speechSynthesis.speak(currentUtterance);
    }

    function toggleAutoSpeak() {
        const isAutoSpeak = speakerButton.dataset.autoSpeak === 'true';
        speakerButton.dataset.autoSpeak = isAutoSpeak ? 'false' : 'true';
        
        if (isAutoSpeak) {
            // Turning off - stop any current speech
            if (isSpeaking) {
                window.speechSynthesis.cancel();
                isSpeaking = false;
                speakerButton.classList.remove('speaking');
            }
            speakerButton.style.opacity = '0.6';
        } else {
            speakerButton.style.opacity = '1';
            // Speak the last bot message
            const lastBotMessage = Array.from(chatContainer.querySelectorAll('.bot-message')).pop();
            if (lastBotMessage) {
                const text = lastBotMessage.innerHTML.replace(/<div class="message-time">.*?<\/div>/g, '');
                speakText(text);
            }
        }
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendMessage();
    });

    if (micButton) {
        micButton.addEventListener('click', toggleRecording);
    }

    if (speakerButton) {
        speakerButton.addEventListener('click', toggleAutoSpeak);
        speakerButton.dataset.autoSpeak = 'false';
        speakerButton.style.opacity = '0.6';
    }

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

    messageInput.focus();
});