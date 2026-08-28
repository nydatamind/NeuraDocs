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
    justify-content: center;
    height: 44px;
    width: 44px;
    overflow: hidden;
  }
  #mic-btn {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    border: 1.5px solid rgba(124,92,255,0.5);
    background: rgba(12, 14, 24, 0.8);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
    outline: none;
  }
  #mic-btn:hover {
    border-color: #35d5ff;
    transform: scale(1.05);
    box-shadow: 0 0 10px rgba(53,213,255,0.4);
  }
  #mic-btn.recording {
    border-color: #ff4d6d;
    background: rgba(255,77,109,0.15);
    animation: micPulse 1.2s infinite;
  }
  @keyframes micPulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(255,77,109,0.4); }
    50%       { box-shadow: 0 0 0 6px rgba(255,77,109,0); }
  }
  #mic-icon { font-size: 16px; line-height:1; pointer-events:none; }
</style>
</head>
<body>
  <button id="mic-btn" title="Click to speak">
    <span id="mic-icon">🎙️</span>
  </button>

<script>
(function() {
  var btn = document.getElementById('mic-btn');
  var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    btn.disabled = true;
    btn.style.opacity = '0.3';
    btn.style.cursor = 'not-allowed';
    btn.title = 'Speech Recognition not supported in this browser';
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
        console.error('Microphone access failed:', e);
      }
    }
  });

  recognition.onstart = function() {
    recording = true;
    btn.classList.add('recording');
    document.getElementById('mic-icon').textContent = '⏹️';
  };

  recognition.onend = function() {
    recording = false;
    btn.classList.remove('recording');
    document.getElementById('mic-icon').textContent = '🎙️';
  };

  recognition.onerror = function(e) {
    recording = false;
    btn.classList.remove('recording');
    document.getElementById('mic-icon').textContent = '🎙️';
    console.error('Speech recognition error:', e.error);
  };

  recognition.onresult = function(e) {
    var transcript = e.results[0][0].transcript.trim();
    if (!transcript) return;

    // Send the voice transcription to Streamlit
    try {
      // 1. Try parent document textarea manipulation (fastest)
      var parentDoc = window.parent.document;
      var inputs = parentDoc.querySelectorAll('textarea[data-testid="stChatInput"]');
      if (inputs.length > 0) {
        var inputEl = inputs[0];
        
        // Use React setter wrapper to trigger input events correctly
        var valueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
        var prototypeSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLTextAreaElement.prototype, 'value').set;
        var setter = prototypeSetter || valueSetter;
        
        setter.call(inputEl, transcript);
        inputEl.dispatchEvent(new window.parent.Event('input', { bubbles: true }));
        inputEl.focus();
        
        // Automatically submit the message by simulating Enter key or clicking the submit button
        setTimeout(function() {
          var submitBtn = parentDoc.querySelector('button[data-testid="stChatInputSubmitButton"]');
          if (submitBtn) {
            submitBtn.click();
          } else {
            // Trigger Enter key event on the textarea
            var enterEvent = new window.parent.KeyboardEvent('keydown', {
              bubbles: true, cancelable: true, key: 'Enter', keyCode: 13
            });
            inputEl.dispatchEvent(enterEvent);
          }
        }, 100);
      } else {
        throw new Error("Textarea not found");
      }
    } catch(err) {
      // 2. Cross-origin / standard fallback: communicate using URL search params
      var parentWindow = window.parent;
      var url = new URL(parentWindow.location.href);
      url.searchParams.set('voice_input', transcript);
      parentWindow.location.href = url.toString();
    }
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
    # Render only the voice input component, removed the export buttons
    components.html(_VOICE_BUTTON_HTML, height=52, scrolling=False)

