const BASE_URL = 'http://localhost:8000';

// Elements
const elStatus = document.getElementById('status-badge');
const elTitle = document.getElementById('video-title');
const elUrl = document.getElementById('video-url');
const btnProcess = document.getElementById('btn-process');
const chatContainer = document.getElementById('chat-history');
const inputField = document.getElementById('user-input');
const btnSend = document.getElementById('btn-send');

let currentVideoId = null;
let currentUrl = null;

// Helper: Extract ID robustly (matches backend logic)
function extractVideoId(url) {
    try {
        const u = new URL(url);
        // Handle youtu.be/XYZ
        if (u.hostname === 'youtu.be') {
            return u.pathname.slice(1);
        }
        // Handle youtube.com/watch?v=XYZ
        if (u.hostname.includes('youtube.com') && u.searchParams.has('v')) {
            return u.searchParams.get('v');
        }
        return null;
    } catch (e) {
        return null;
    }
}

// 1. Initialize when popup opens
document.addEventListener('DOMContentLoaded', async () => {
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (tab && (tab.url.includes('youtube.com') || tab.url.includes('youtu.be'))) {
        currentUrl = tab.url;
        const vid = extractVideoId(currentUrl);
        
        if (vid) {
            currentVideoId = vid;
            elUrl.textContent = vid;
            
            // Fetch Title
            chrome.scripting.executeScript({
                target: { tabId: tab.id },
                function: () => document.title.replace(' - YouTube', '')
            }, (results) => {
                if (results && results[0]) elTitle.textContent = results[0].result;
            });

            // CRITICAL: Check if backend already has this video!
            checkExistingStatus(vid);
        } else {
            setUIState('error', "Invalid YouTube URL");
        }
    } else {
        setUIState('error', "Not a YouTube Video");
    }
});

// 2. Check Backend for existing session
async function checkExistingStatus(vid) {
    elStatus.textContent = "Checking Server...";
    try {
        const res = await fetch(`${BASE_URL}/status/${vid}`);
        const data = await res.json();

        if (data.ok && data.status === 'ready') {
            // Video already processed! Skip to chat.
            setUIState('chat');
            addMessage('ai', "Welcome back! I remember this video. Ask me anything.");
        } else if (data.ok && data.status === 'processing') {
            // Currently processing
            setUIState('processing');
            pollStatus(vid);
        } else {
            // Not found, ready to initialize
            setUIState('init');
        }
    } catch (err) {
        elStatus.textContent = "Server Offline";
        elStatus.classList.add('error');
        console.error("Server check failed:", err);
    }
}

// 3. Process Video (Click Handler)
btnProcess.addEventListener('click', async () => {
    if (!currentUrl) return;
    
    setUIState('processing');
    addMessage('system', 'Initializing AI for this video...');

    try {
        const res = await fetch(`${BASE_URL}/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_url: currentUrl })
        });
        
        if (!res.ok) throw new Error('Backend connection failed');
        
        const data = await res.json();
        // Backend returns the ID it extracted, ensure we use that
        currentVideoId = data.video_id; 

        // Start Polling
        pollStatus(currentVideoId);

    } catch (err) {
        addMessage('system', `Error: ${err.message}`);
        setUIState('init'); // Reset to allow retry
    }
});

// 4. Status Polling
async function pollStatus(vid) {
    const interval = setInterval(async () => {
        try {
            const res = await fetch(`${BASE_URL}/status/${vid}`);
            const data = await res.json();

            if (data.has_error) {
                clearInterval(interval);
                addMessage('system', "Processing failed on server.");
                setUIState('init'); // Allow retry
                return;
            }

            if (data.status === 'ready') {
                clearInterval(interval);
                setUIState('chat');
                addMessage('ai', "Processing complete! I'm ready.");
            }
        } catch (err) {
            // Network error, keep retrying or stop?
            // For now, we'll keep retrying in background
            console.log("Polling connection error...");
        }
    }, 1000);
}

// 5. Send Message
async function sendMessage() {
    const text = inputField.value.trim();
    if (!text || !currentVideoId) return;

    // UI Updates
    addMessage('user', text);
    inputField.value = '';
    setInputDisabled(true);

    try {
        const res = await fetch(`${BASE_URL}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_id: currentVideoId, question: text })
        });
        
        const data = await res.json();
        addMessage('ai', data.answer);

    } catch (err) {
        addMessage('system', "Failed to get answer. Is server running?");
    } finally {
        setInputDisabled(false);
        inputField.focus();
    }
}

// Event Listeners
btnSend.addEventListener('click', sendMessage);
inputField.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

// --- UI Helpers ---

function setUIState(state, errorMsg = "") {
    // Reset all
    elStatus.className = 'status-badge';
    btnProcess.style.display = 'none';
    btnProcess.classList.remove('loading');
    btnProcess.disabled = true;
    setInputDisabled(true);

    switch(state) {
        case 'init':
            elStatus.textContent = "Ready";
            btnProcess.style.display = 'flex';
            btnProcess.disabled = false;
            btnProcess.querySelector('.btn-text').textContent = "Initialize AI";
            break;
        case 'processing':
            elStatus.textContent = "Processing...";
            btnProcess.style.display = 'flex';
            btnProcess.classList.add('loading');
            break;
        case 'chat':
            elStatus.textContent = "Connected";
            elStatus.classList.add('active');
            setInputDisabled(false);
            break;
        case 'error':
            elStatus.textContent = errorMsg;
            elStatus.classList.add('error');
            break;
    }
}

function setInputDisabled(disabled) {
    inputField.disabled = disabled;
    btnSend.disabled = disabled;
}

function addMessage(role, text) {
    const div = document.createElement('div');
    div.className = `msg ${role}`;
    div.textContent = text;
    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}