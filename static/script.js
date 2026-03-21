// Application State
let messages = [];
let isLoading = false;
let currentResume = null;
let chatHistory = [];

// DOM Elements
const welcomeScreen = document.getElementById('welcomeScreen');
const messagesContainer = document.getElementById('messagesContainer');
const loadingIndicator = document.getElementById('loadingIndicator');
const messagesEnd = document.getElementById('messagesEnd');
const clearBtn = document.getElementById('clearBtn');

// Build Form (Phase 1)
const buildForm = document.getElementById('buildForm');
const buildButton = document.getElementById('buildButton');
const buildIcon = document.getElementById('buildIcon');
const buildSpinner = document.getElementById('buildSpinner');
const fieldName = document.getElementById('fieldName');
const fieldOccupation = document.getElementById('fieldOccupation');
const fieldIndustry = document.getElementById('fieldIndustry');
const fieldJobDescription = document.getElementById('fieldJobDescription');
const fieldSummary = document.getElementById('fieldSummary');
const fieldSkills = document.getElementById('fieldSkills');
const fieldExperience = document.getElementById('fieldExperience');
const fieldEducation = document.getElementById('fieldEducation');
const fieldAwards = document.getElementById('fieldAwards');

// Chat Form (Phase 2)
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const sendIcon = document.getElementById('sendIcon');
const loadingSpinner = document.getElementById('loadingSpinner');

// Initialize
document.addEventListener('DOMContentLoaded', function () {
    setupEventListeners();
    updateSendButton();
});

function setupEventListeners() {
    buildForm.addEventListener('submit', handleBuildSubmit);
    chatForm.addEventListener('submit', handleChatSubmit);
    clearBtn.addEventListener('click', clearChat);
    messageInput.addEventListener('input', handleInputChange);
    messageInput.addEventListener('keydown', handleKeyDown);
}

// ─── Phase 1: Build ──────────────────────────────────────────────────────────

function handleBuildSubmit(e) {
    e.preventDefault();
    if (isLoading) return;
    buildResume();
}

async function buildResume() {
    const payload = {
        name: fieldName.value.trim(),
        occupation: fieldOccupation.value.trim(),
        industry: fieldIndustry.value.trim(),
        job_description: fieldJobDescription.value.trim(),
        summary: fieldSummary.value.trim(),
        skills: fieldSkills.value.trim(),
        experience: fieldExperience.value.trim(),
        education: fieldEducation.value.trim(),
        awards: fieldAwards.value.trim()
    };

    // Display a user-side summary message
    const userMessage = {
        id: Date.now().toString(),
        content: `Building resume for ${payload.name} — ${payload.occupation} in ${payload.industry}.`,
        type: 'user',
        phase: null,
        timestamp: new Date()
    };
    messages.push(userMessage);
    displayMessage(userMessage);
    hideWelcomeScreen();
    showClearButton();
    setBuildLoadingState(true);

    try {
        const response = await fetch('/build', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        const isError = !data.reply || data.reply.startsWith('System Error:');

        currentResume = isError ? null : data.reply;

        const aiMessage = {
            id: (Date.now() + 1).toString(),
            content: data.reply || 'No response received.',
            type: 'ai',
            phase: 'build',
            timestamp: new Date(),
            isError: isError
        };
        messages.push(aiMessage);
        displayMessage(aiMessage);

        // Transition to Phase 2 only on success
        if (!isError) {
            buildForm.style.display = 'none';
            chatForm.style.display = 'block';
            chatHistory = [];
            messageInput.focus();
        }

    } catch (error) {
        const errorMessage = {
            id: (Date.now() + 1).toString(),
            content: 'Error: ' + error.message,
            type: 'ai',
            phase: null,
            timestamp: new Date(),
            isError: true
        };
        messages.push(errorMessage);
        displayMessage(errorMessage);

    } finally {
        setBuildLoadingState(false);
    }
}

// ─── Phase 2: Chat ───────────────────────────────────────────────────────────

function handleChatSubmit(e) {
    e.preventDefault();
    const content = messageInput.value.trim();
    if (!content || isLoading) return;
    sendChatMessage(content);
}

function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleChatSubmit(e);
    }
}

async function sendChatMessage(content) {
    const userMessage = {
        id: Date.now().toString(),
        content: content,
        type: 'user',
        phase: null,
        timestamp: new Date()
    };
    messages.push(userMessage);
    displayMessage(userMessage);

    messageInput.value = '';
    messageInput.style.height = 'auto';
    setChatLoadingState(true);

    // Append to history before sending
    chatHistory.push({ role: 'user', content: content });

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                resume: currentResume,
                message: content,
                history: chatHistory
            })
        });

        const data = await response.json();
        const isError = !data.reply || data.reply.startsWith('System Error:');

        // Update stored resume with the latest edited version
        if (!isError) {
            currentResume = data.reply;
            chatHistory.push({ role: 'assistant', content: data.reply });
        }

        const aiMessage = {
            id: (Date.now() + 1).toString(),
            content: data.reply || 'No response received.',
            type: 'ai',
            phase: 'edit',
            timestamp: new Date(),
            isError: isError
        };
        messages.push(aiMessage);
        displayMessage(aiMessage);

    } catch (error) {
        const errorMessage = {
            id: (Date.now() + 1).toString(),
            content: 'Error: ' + error.message,
            type: 'ai',
            phase: null,
            timestamp: new Date(),
            isError: true
        };
        messages.push(errorMessage);
        displayMessage(errorMessage);

    } finally {
        setChatLoadingState(false);
    }
}

// ─── Display ─────────────────────────────────────────────────────────────────

function displayMessage(message) {
    const messageEl = document.createElement('div');
    messageEl.className = 'message ' + message.type;

    const time = message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const avatarIcon = message.type === 'user'
        ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
        : '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7 8h10M7 12h10M7 16h6"/></svg>';

    const phaseBadge = message.phase
        ? '<span class="message-model">' + (message.phase === 'build' ? 'Built' : 'Edited') + '</span>'
        : '';

    const senderLabel = message.type === 'user' ? 'You' : 'Career Strategist';

    messageEl.innerHTML = [
        '<div class="message-wrapper">',
            '<div class="message-header">',
                '<div class="message-avatar">' + avatarIcon + '</div>',
                '<div class="message-info">',
                    '<span class="message-sender">' + senderLabel + '</span>',
                    phaseBadge,
                '</div>',
            '</div>',
            '<div class="message-bubble">',
                '<div class="message-text">' + message.content + '</div>',
            '</div>',
            '<div class="message-footer">',
                '<span>' + time + '</span>',
            '</div>',
        '</div>'
    ].join('');

    messagesContainer.appendChild(messageEl);
    scrollToBottom();
}

// ─── Loading States ───────────────────────────────────────────────────────────

function setBuildLoadingState(loading) {
    isLoading = loading;
    buildButton.disabled = loading;
    buildIcon.style.display = loading ? 'none' : 'inline';
    buildSpinner.style.display = loading ? 'block' : 'none';
    loadingIndicator.style.display = loading ? 'block' : 'none';
    if (loading) scrollToBottom();
}

function setChatLoadingState(loading) {
    isLoading = loading;
    updateSendButton();
    messageInput.disabled = loading;
    sendIcon.style.display = loading ? 'none' : 'block';
    loadingSpinner.style.display = loading ? 'block' : 'none';
    loadingIndicator.style.display = loading ? 'block' : 'none';
    if (loading) scrollToBottom();
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function handleInputChange() {
    autoResizeTextarea();
    updateSendButton();
}

function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    const newHeight = Math.min(messageInput.scrollHeight, 128);
    messageInput.style.height = newHeight + 'px';
}

function updateSendButton() {
    const hasContent = messageInput.value.trim().length > 0;
    sendButton.disabled = !hasContent || isLoading;
}

function hideWelcomeScreen() { welcomeScreen.style.display = 'none'; }
function showWelcomeScreen() { welcomeScreen.style.display = 'flex'; }
function showClearButton() { clearBtn.style.display = 'flex'; }
function hideClearButton() { clearBtn.style.display = 'none'; }
function scrollToBottom() { messagesEnd.scrollIntoView({ behavior: 'smooth' }); }

function clearChat() {
    messages = [];
    chatHistory = [];
    currentResume = null;
    messagesContainer.innerHTML = '';
    buildForm.reset();
    buildForm.style.display = 'block';
    chatForm.style.display = 'none';
    showWelcomeScreen();
    hideClearButton();
    setLoadingState(false);
    updateSendButton();
}

function setLoadingState(loading) {
    isLoading = loading;
    loadingIndicator.style.display = loading ? 'block' : 'none';
}
