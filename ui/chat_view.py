"""
NeuraDocs - Chat Interface & Voice Input Component
===================================================
Renders message bubbles, streaming tokens, voice-to-text input button,
and export controls.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components
from typing import Any, Dict, List, Optional

from core.models import ChatMessage, RetrievedChunk

# ---------------------------------------------------------------------------
# Voice Input Component (Web Speech API via iframe bridge)
# ---------------------------------------------------------------------------

_VOICE_BUTTON_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    background: transparent;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    padding: 4px 0;
    height: 52px;
    overflow: hidden;
  }
  #mic-btn {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    border: 2px solid rgba(124,92,255,0.6);
    background: linear-gradient(135deg, rgba(124,92,255,0.15), rgba(53,213,255,0.10));
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.25s ease;
    position: relative;
    outline: none;
    flex-shrink: 0;
  }
  #mic-btn:hover {
    border-color: #7c5cff;
    background: linear-gradient(135deg, rgba(124,92,255,0.30), rgba(53,213,255,0.18));
    transform: scale(1.08);
    box-shadow: 0 0 14px rgba(124,92,255,0.45);
  }
  #mic-btn.recording {
    border-color: #ff4d6d;
    background: linear-gradient(135deg, rgba(255,77,109,0.25), rgba(255,92,173,0.15));
    animation: micPulse 1s infinite;
  }
  @keyframes micPulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(255,77,109,0.5); }
    50%       { box-shadow: 0 0 0 8px rgba(255,77,109,0); }
  }
  #mic-icon { font-size: 18px; line-height:1; pointer-events:none; }
  #mic-status {
    margin-left: 10px;
    font-size: 0.72rem;
    color: #6d7594;
    font-family: 'Inter', sans-serif;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 160px;
  }
  #mic-status.active { color: #35d5ff; }
  #mic-status.error  { color: #ff4d6d; }
</style>
</head>
<body>
  <button id="mic-btn" title="Click to record voice message">
    <span id="mic-icon">🎙️</span>
  </button>
  <span id="mic-status">Voice input</span>

<script>
(function() {
  var btn    = document.getElementById('mic-btn');
  var status = document.getElementById('mic-status');
  var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    status.textContent = 'Not supported in this browser';
    status.className = 'error';
    btn.disabled = true;
    btn.style.opacity = '0.4';
    btn.style.cursor = 'not-allowed';
    return;
  }

  var recognition = new SpeechRecognition();
  recognition.lang = 'en-US';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  recognition.continuous = false;

  var recording = false;

  btn.addEventListener('click', function() {
    if (recording) {
      recognition.stop();
    } else {
      try {
        recognition.start();
      } catch(e) {
        status.textContent = 'Mic error — allow microphone access';
        status.className = 'error';
      }
    }
  });

  recognition.onstart = function() {
    recording = true;
    btn.classList.add('recording');
    document.getElementById('mic-icon').textContent = '⏹️';
    status.textContent = 'Listening…';
    status.className = 'active';
  };

  recognition.onend = function() {
    recording = false;
    btn.classList.remove('recording');
    document.getElementById('mic-icon').textContent = '🎙️';
    if (status.className === 'active') {
      status.textContent = 'Voice input';
      status.className = '';
    }
  };

  recognition.onerror = function(e) {
    recording = false;
    btn.classList.remove('recording');
    document.getElementById('mic-icon').textContent = '🎙️';
    var msg = {
      'not-allowed'  : 'Microphone permission denied',
      'no-speech'    : 'No speech detected — try again',
      'network'      : 'Network error — check connection',
      'audio-capture': 'No microphone found'
    }[e.error] || ('Error: ' + e.error);
    status.textContent = msg;
    status.className = 'error';
    setTimeout(function(){ status.textContent = 'Voice input'; status.className = ''; }, 3500);
  };

  recognition.onresult = function(e) {
    var transcript = e.results[0][0].transcript.trim();
    if (!transcript) return;

    status.textContent = '✓ ' + transcript.substring(0, 40) + (transcript.length > 40 ? '…' : '');
    status.className = 'active';

    // Send transcript to Streamlit via postMessage / query param trick
    // Write it to the Streamlit chat input if accessible, else use URL param
    try {
      // Try to find and fill the Streamlit chat input in the parent frame
      var inputs = window.parent.document.querySelectorAll('textarea[data-testid="stChatInput"]');
      if (inputs.length > 0) {
        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
          window.parent.HTMLTextAreaElement.prototype, 'value'
        ).set;
        nativeInputValueSetter.call(inputs[0], transcript);
        inputs[0].dispatchEvent(new window.parent.Event('input', { bubbles: true }));
        inputs[0].focus();
      }
    } catch(err) {
      // Fallback: set query param for Streamlit to pick up
      var url = new URL(window.parent.location.href);
      url.searchParams.set('voice_input', transcript);
      window.parent.history.replaceState({}, '', url.toString());
    }

    setTimeout(function(){ status.textContent = 'Voice input'; status.className = ''; }, 3000);
  };
})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Message Bubble Renderer
# ---------------------------------------------------------------------------

def render_message_bubble(msg: ChatMessage):
    avatar = "🧑‍💻" if msg.role == "user" else "🧠"
    with st.chat_message(msg.role, avatar=avatar):
        st.markdown(msg.content)
        # Source citations are stored on the message but NOT displayed as
        # debug UI — the clean AI answer is all the user sees.


# ---------------------------------------------------------------------------
# Voice + Export Controls Row
# ---------------------------------------------------------------------------

def render_voice_and_export_controls(
    on_export_markdown=None,
    on_export_text=None,
    on_export_json=None,
):
    col_mic, col_exp1, col_exp2, col_exp3 = st.columns([2, 1, 1, 1])

    with col_mic:
        # Embedded Web Speech API voice button
        components.html(_VOICE_BUTTON_HTML, height=52, scrolling=False)

    with col_exp1:
        if st.button("📥 Export .MD", key="btn_exp_md", help="Download conversation as Markdown"):
            if on_export_markdown:
                on_export_markdown()

    with col_exp2:
        if st.button("📄 Export .TXT", key="btn_exp_txt", help="Download conversation as Text"):
            if on_export_text:
                on_export_text()

    with col_exp3:
        if st.button("💾 Export .JSON", key="btn_exp_json", help="Download conversation as JSON"):
            if on_export_json:
                on_export_json()
