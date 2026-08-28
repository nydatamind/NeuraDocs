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
# Voice Input Component (Web Speech API - injects button into parent DOM)
# ---------------------------------------------------------------------------

_VOICE_BUTTON_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:transparent; width:0; height:0; overflow:hidden; }
</style>
</head>
<body>
<script>
(function() {
  var recording = false;
  var recognition = null;
  var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  function injectButton() {
    var parentDoc = window.parent.document;
    if (!parentDoc) return;
    if (parentDoc.getElementById('nd-mic-btn')) return;

    if (!parentDoc.getElementById('nd-mic-style')) {
      var style = parentDoc.createElement('style');
      style.id = 'nd-mic-style';
      style.textContent = [
        '#nd-mic-btn {',
        '  position: fixed; bottom: 14px; right: 66px;',
        '  z-index: 2147483647;',
        '  width: 42px; height: 42px;',
        '  border-radius: 10px; border: none;',
        '  background: linear-gradient(135deg,#7c5cff,#a05cff);',
        '  cursor: pointer; font-size: 19px;',
        '  display: flex; align-items: center; justify-content: center;',
        '  box-shadow: 0 4px 16px rgba(124,92,255,0.45);',
        '  transition: transform .2s, box-shadow .2s;',
        '  outline: none;',
        '}',
        '#nd-mic-btn:hover { transform:scale(1.08); box-shadow:0 6px 22px rgba(124,92,255,0.6); }',
        '#nd-mic-btn.nd-recording {',
        '  background: linear-gradient(135deg,#ff4d6d,#ff6b35) !important;',
        '  animation: ndPulse 1.2s infinite;',
        '}',
        '@keyframes ndPulse {',
        '  0%   { box-shadow: 0 0 0 0 rgba(255,77,109,0.55); }',
        '  70%  { box-shadow: 0 0 0 10px rgba(255,77,109,0); }',
        '  100% { box-shadow: 0 0 0 0 rgba(255,77,109,0); }',
        '}'
      ].join('');
      parentDoc.head.appendChild(style);
    }

    var btn = parentDoc.createElement('button');
    btn.id = 'nd-mic-btn';
    btn.title = 'Voice Input';
    btn.innerHTML = String.fromCodePoint(0x1F399);

    btn.addEventListener('click', function() {
      window.postMessage({ type: 'nd-toggle' }, '*');
    });

    parentDoc.body.appendChild(btn);
  }

  function setupRecognition() {
    if (!SpeechRecognition) return;

    recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.continuous = false;

    recognition.onstart = function() {
      recording = true;
      var btn = window.parent.document.getElementById('nd-mic-btn');
      if (btn) { btn.classList.add('nd-recording'); btn.innerHTML = String.fromCodePoint(0x23F9); }
    };

    recognition.onend = function() {
      recording = false;
      var btn = window.parent.document.getElementById('nd-mic-btn');
      if (btn) { btn.classList.remove('nd-recording'); btn.innerHTML = String.fromCodePoint(0x1F399); }
    };

    recognition.onerror = function() {
      recording = false;
      var btn = window.parent.document.getElementById('nd-mic-btn');
      if (btn) { btn.classList.remove('nd-recording'); btn.innerHTML = String.fromCodePoint(0x1F399); }
    };

    recognition.onresult = function(e) {
      var transcript = e.results[0][0].transcript.trim();
      if (!transcript) return;

      try {
        var parentDoc = window.parent.document;
        var textarea = parentDoc.querySelector('textarea[data-testid="stChatInput"]');
        if (!textarea) throw new Error('no textarea');

        var setter = Object.getOwnPropertyDescriptor(
          window.parent.HTMLTextAreaElement.prototype, 'value'
        ).set;
        setter.call(textarea, transcript);
        textarea.dispatchEvent(new window.parent.Event('input', { bubbles: true }));
        textarea.focus();

        setTimeout(function() {
          var submitBtn = parentDoc.querySelector(
            'button[data-testid="stChatInputSubmitButton"]'
          );
          if (submitBtn && !submitBtn.disabled) {
            submitBtn.click();
          } else {
            textarea.dispatchEvent(new window.parent.KeyboardEvent('keydown', {
              bubbles: true, cancelable: true, key: 'Enter', keyCode: 13
            }));
          }
        }, 250);
      } catch(err) {
        var url = new URL(window.parent.location.href);
        url.searchParams.set('voice_input', transcript);
        window.parent.location.href = url.toString();
      }
    };
  }

  window.addEventListener('message', function(e) {
    if (!e.data || e.data.type !== 'nd-toggle') return;
    if (!recognition) return;
    if (recording) { recognition.stop(); }
    else { try { recognition.start(); } catch(ex) {} }
  });

  setupRecognition();
  setTimeout(injectButton, 600);

  setInterval(function() {
    var parentDoc = window.parent.document;
    if (parentDoc && !parentDoc.getElementById('nd-mic-btn')) { injectButton(); }
  }, 2000);
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


# ---------------------------------------------------------------------------
# Voice Controls
# ---------------------------------------------------------------------------

def render_voice_and_export_controls(
    on_export_markdown=None,
    on_export_text=None,
    on_export_json=None,
):
    # Invisible 0-height iframe; mic button is injected into parent DOM
    components.html(_VOICE_BUTTON_HTML, height=0, scrolling=False)
