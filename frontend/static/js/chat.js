(function() {
  // Get owner ID from script tag data attribute
  var scriptTag = document.currentScript || document.querySelector('script[data-owner-id]');
  var ownerId = scriptTag ? scriptTag.getAttribute('data-owner-id') : '';
  var brandColor = '#4f46e5';
  var conversationHistory = [];

  // Inject styles
  var style = document.createElement('style');
  style.innerHTML = `
    .quikbok-bubble {
      position: fixed; bottom: 32px; right: 32px; z-index: 9999;
      background: ${brandColor}; color: #fff; width: 64px; height: 64px;
      border-radius: 50%; box-shadow: 0 4px 24px rgba(79,70,229,0.35);
      display: flex; align-items: center; justify-content: center;
      cursor: pointer; animation: quikbok-pulse 2s infinite;
      transition: transform 0.2s;
    }
    .quikbok-bubble:hover { transform: scale(1.1); }
    @keyframes quikbok-pulse {
      0% { box-shadow: 0 0 0 0 rgba(79,70,229,0.4); }
      70% { box-shadow: 0 0 0 16px transparent; }
      100% { box-shadow: 0 0 0 0 transparent; }
    }
    .quikbok-window {
      position: fixed; bottom: 112px; right: 32px; z-index: 9999;
      width: 380px; max-width: 95vw; height: 520px; background: #fff;
      border-radius: 20px; box-shadow: 0 12px 48px rgba(0,0,0,0.15);
      display: none; flex-direction: column; overflow: hidden;
      font-family: 'Inter', system-ui, sans-serif;
      border: 1px solid rgba(0,0,0,0.06);
    }
    .quikbok-header {
      background: linear-gradient(135deg, ${brandColor}, #6366f1);
      color: #fff; padding: 18px 20px; font-weight: 600;
      display: flex; align-items: center; justify-content: space-between;
      font-size: 15px;
    }
    .quikbok-header-left { display: flex; align-items: center; gap: 12px; }
    .quikbok-header-avatar { width: 36px; height: 36px; border-radius: 50%; background: rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; }
    .quikbok-header-info .quikbok-header-name { font-weight: 700; }
    .quikbok-header-info .quikbok-header-status { font-size: 11px; opacity: 0.85; display: flex; align-items: center; gap: 4px; }
    .quikbok-header-info .quikbok-header-status::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: #34d399; display: inline-block; }
    .quikbok-close { cursor: pointer; font-size: 22px; opacity: 0.8; transition: opacity 0.2s; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 50%; }
    .quikbok-close:hover { opacity: 1; background: rgba(255,255,255,0.15); }
    .quikbok-messages { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; background: #f9fafb; }
    .quikbok-input-row { display: flex; border-top: 1px solid #e5e7eb; background: #fff; padding: 12px; gap: 8px; }
    .quikbok-input { flex: 1; padding: 10px 14px; border: 1px solid #e5e7eb; outline: none; border-radius: 12px; font-size: 14px; font-family: inherit; background: #f9fafb; transition: border-color 0.2s; }
    .quikbok-input:focus { border-color: ${brandColor}; background: #fff; }
    .quikbok-send { background: ${brandColor}; color: #fff; border: none; width: 40px; height: 40px; border-radius: 12px; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; justify-content: center; }
    .quikbok-send:hover { background: #4338ca; transform: scale(1.05); }
    .quikbok-send:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
    .quikbok-msg-user { background: ${brandColor}; color: #fff; border-radius: 16px 16px 4px 16px; padding: 10px 14px; max-width: 80%; align-self: flex-end; font-size: 14px; line-height: 1.5; box-shadow: 0 1px 3px rgba(79,70,229,0.2); }
    .quikbok-msg-ai { background: #fff; color: #1f2937; border-radius: 16px 16px 16px 4px; padding: 10px 14px; max-width: 80%; align-self: flex-start; font-size: 14px; line-height: 1.5; border: 1px solid #e5e7eb; }
    .quikbok-typing { display: flex; align-items: center; gap: 8px; padding: 10px 14px; background: #fff; border-radius: 16px 16px 16px 4px; border: 1px solid #e5e7eb; align-self: flex-start; max-width: 80%; }
    .quikbok-typing-dots { display: flex; gap: 4px; }
    .quikbok-typing-dot { width: 7px; height: 7px; border-radius: 50%; background: #9ca3af; animation: quikbok-bounce 1.4s infinite ease-in-out both; }
    .quikbok-typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .quikbok-typing-dot:nth-child(2) { animation-delay: -0.16s; }
    @keyframes quikbok-bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
    .quikbok-booking-card { background: linear-gradient(135deg, #ecfdf5, #f0fdf4); border: 1px solid #86efac; border-radius: 12px; padding: 12px 14px; margin-top: 4px; font-size: 13px; }
    .quikbok-booking-card strong { color: #166534; }
    .quikbok-welcome { text-align: center; padding: 24px 16px; color: #9ca3af; font-size: 13px; }
  `;
  document.head.appendChild(style);

  // Create chat bubble
  var bubble = document.createElement('div');
  bubble.className = 'quikbok-bubble';
  bubble.id = 'quikbok-chat-bubble';
  bubble.innerHTML = '<svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';
  document.body.appendChild(bubble);

  // Create chat window
  var windowDiv = document.createElement('div');
  windowDiv.className = 'quikbok-window';
  windowDiv.id = 'quikbok-chat-window';
  windowDiv.innerHTML = `
    <div class="quikbok-header">
      <div class="quikbok-header-left">
        <div class="quikbok-header-avatar">AI</div>
        <div class="quikbok-header-info">
          <div class="quikbok-header-name">Quikbok Assistant</div>
          <div class="quikbok-header-status">Online</div>
        </div>
      </div>
      <span class="quikbok-close">&times;</span>
    </div>
    <div class="quikbok-messages">
      <div class="quikbok-welcome">
        <div style="font-size:28px; margin-bottom:8px;">👋</div>
        <div style="font-weight:600; color:#374151; margin-bottom:4px;">Hi there!</div>
        <div>How can I help you with your booking today?</div>
      </div>
    </div>
    <form class="quikbok-input-row">
      <input class="quikbok-input" type="text" placeholder="Type your message..." autocomplete="off" />
      <button class="quikbok-send" type="submit">
        <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"/></svg>
      </button>
    </form>
  `;
  document.body.appendChild(windowDiv);

  var messagesDiv = windowDiv.querySelector('.quikbok-messages');
  var input = windowDiv.querySelector('.quikbok-input');
  var form = windowDiv.querySelector('form');
  var closeBtn = windowDiv.querySelector('.quikbok-close');
  var sendBtn = windowDiv.querySelector('.quikbok-send');

  function scrollToBottom() {
    setTimeout(function() { messagesDiv.scrollTop = messagesDiv.scrollHeight; }, 50);
  }

  function addMessage(text, isUser) {
    // Remove welcome message on first interaction
    var welcome = messagesDiv.querySelector('.quikbok-welcome');
    if (welcome) welcome.remove();

    var msg = document.createElement('div');
    msg.className = isUser ? 'quikbok-msg-user' : 'quikbok-msg-ai';
    msg.textContent = text;
    messagesDiv.appendChild(msg);
    scrollToBottom();
  }

  function addBookingCard(details) {
    var card = document.createElement('div');
    card.className = 'quikbok-booking-card';
    card.innerHTML = '<strong>✅ Booking Saved!</strong><br>' +
      '📋 ' + details.name + '<br>' +
      '📅 ' + details.date + '<br>' +
      '🏨 ' + details.service + '<br>' +
      '📞 ' + details.phone;
    messagesDiv.appendChild(card);
    scrollToBottom();
  }

  function showTyping() {
    var typing = document.createElement('div');
    typing.className = 'quikbok-typing';
    typing.id = 'quikbok-typing';
    typing.innerHTML = '<div class="quikbok-typing-dots"><div class="quikbok-typing-dot"></div><div class="quikbok-typing-dot"></div><div class="quikbok-typing-dot"></div></div><span style="font-size:12px;color:#6b7280;">Typing...</span>';
    messagesDiv.appendChild(typing);
    scrollToBottom();
  }

  function hideTyping() {
    var typing = messagesDiv.querySelector('#quikbok-typing');
    if (typing) typing.remove();
  }

  function setLoading(on) {
    sendBtn.disabled = on;
    input.disabled = on;
  }

  function sendMessage(msg) {
    addMessage(msg, true);
    showTyping();
    setLoading(true);

    var baseUrl = window.location.protocol + '//' + window.location.host;
    fetch(baseUrl + '/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        owner_id: ownerId,
        message: msg,
        conversation_history: conversationHistory
      })
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      hideTyping();
      setLoading(false);
      if (data.reply) {
        addMessage(data.reply, false);
        if (data.conversation_history) {
          conversationHistory = data.conversation_history;
        }
        if (data.booking_complete && data.booking_details) {
          addBookingCard(data.booking_details);
        }
      } else if (data.error) {
        addMessage('Sorry, something went wrong: ' + data.error, false);
      } else {
        addMessage('Sorry, something went wrong.', false);
      }
    })
    .catch(function(err) {
      hideTyping();
      setLoading(false);
      addMessage('Connection error. Please try again.', false);
    });
  }

  bubble.onclick = function() {
    windowDiv.style.display = windowDiv.style.display === 'flex' ? 'none' : 'flex';
    if (windowDiv.style.display === 'flex') input.focus();
  };
  closeBtn.onclick = function() {
    windowDiv.style.display = 'none';
  };
  form.onsubmit = function(e) {
    e.preventDefault();
    var msg = input.value.trim();
    if (!msg) return;
    sendMessage(msg);
    input.value = '';
  };
  
  // Add Enter key binding
  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      var msg = input.value.trim();
      if (!msg) return;
      sendMessage(msg);
      input.value = '';
    }
  });
})();
