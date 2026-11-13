// script.js - frontend logic for the College FAQ Assistant

const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const clearBtn = document.getElementById("clear-btn");
const loadingEl = document.getElementById("loading");

const WELCOME_MESSAGE =
  "Hello! 👋 I'm the College FAQ Assistant. Ask me about admissions, courses, " +
  "fees, exams, attendance, placements, scholarships or the library.";

// Quick questions shown as clickable buttons under the welcome message
const STARTER_QUESTIONS = [
  "How can I apply for admission?",
  "What is the fee structure for B.Tech?",
  "What is the minimum attendance required?",
  "What scholarships are available for students?",
];

// Current time like "10:42 AM"
function currentTime() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// Create a row of clickable question buttons; clicking one sends that question
function createChips(questions) {
  const row = document.createElement("div");
  row.className = "chips";
  questions.forEach((question) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.textContent = question;
    chip.addEventListener("click", () => {
      if (!sendBtn.disabled) sendMessage(question);
    });
    row.appendChild(chip);
  });
  return row;
}

// Add a message bubble to the chat window
function addMessage(text, sender, options = {}) {
  const { matchedQuestion = null, suggestions = [], isError = false } = options;

  const bubble = document.createElement("div");
  bubble.className = `message ${sender}` + (isError ? " error" : "");

  const textEl = document.createElement("span");
  textEl.textContent = text; // textContent prevents HTML injection
  bubble.appendChild(textEl);

  if (matchedQuestion) {
    const note = document.createElement("span");
    note.className = "matched";
    note.textContent = `Matched FAQ: ${matchedQuestion}`;
    bubble.appendChild(note);
  }

  if (suggestions.length > 0) {
    bubble.appendChild(createChips(suggestions));
  }

  const time = document.createElement("span");
  time.className = "time";
  time.textContent = currentTime();
  bubble.appendChild(time);

  messagesEl.appendChild(bubble);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// Welcome message + quick question buttons
function showWelcome() {
  addMessage(WELCOME_MESSAGE, "bot");
  messagesEl.appendChild(createChips(STARTER_QUESTIONS));
}

// Show / hide the loading dots and lock the input while waiting
function setLoading(isLoading) {
  loadingEl.classList.toggle("hidden", !isLoading);
  sendBtn.disabled = isLoading;
  inputEl.disabled = isLoading;
  if (!isLoading) inputEl.focus();
}

// Send the question to the Flask backend
async function sendMessage(text) {
  stopSpeaking();
  addMessage(text, "user");
  setLoading(true);

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await response.json();
    addMessage(data.answer || "No response received.", "bot", {
      matchedQuestion: data.matched_question,
      suggestions: data.suggestions || [],
      isError: data.status === "error",
    });
    speak(data.answer); // read the answer aloud (if Voice reply is On)
  } catch (error) {
    addMessage("Could not reach the server. Please check that the app is running.", "bot", {
      isError: true,
    });
  } finally {
    setLoading(false);
  }
}

// Form submit handles both the Send button and the Enter key
formEl.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = inputEl.value.trim();
  if (!text) {
    addMessage("Please type a question first.", "bot", { isError: true });
    return;
  }
  inputEl.value = "";
  sendMessage(text);
});

// Clear chat and show the welcome message again
clearBtn.addEventListener("click", () => {
  stopSpeaking();
  messagesEl.innerHTML = "";
  showWelcome();
  inputEl.focus();
});

// Initial welcome message
showWelcome();
inputEl.focus();

// ===================================================================
// Voice features: speak your question (microphone) + spoken replies
// Uses the browser's built-in Web Speech API. Works in Chrome and Edge.
// ===================================================================
const micBtn = document.getElementById("mic-btn");
const speakToggle = document.getElementById("speak-toggle");
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

let voiceReplyOn = true;
let listening = false;
let recognition = null;

// ---- Spoken replies (text -> speech) ----
function stopSpeaking() {
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
}

function speak(text) {
  if (!voiceReplyOn || !text || !("speechSynthesis" in window)) return;
  // remove emojis so they are not read out loud
  const clean = text.replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, "").trim();
  if (!clean) return;
  stopSpeaking();
  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.lang = "en-IN";
  utterance.rate = 1;
  window.speechSynthesis.speak(utterance);
}

speakToggle.addEventListener("click", () => {
  voiceReplyOn = !voiceReplyOn;
  speakToggle.textContent = voiceReplyOn ? "🔊 Voice reply: On" : "🔇 Voice reply: Off";
  if (!voiceReplyOn) stopSpeaking();
});

// ---- Voice input (speech -> text) ----
function setListening(isListening) {
  listening = isListening;
  micBtn.classList.toggle("listening", isListening);
  micBtn.title = isListening ? "Listening... click to stop" : "Click and speak your question";
  inputEl.placeholder = isListening ? "Listening... speak now" : "Type or click 🎤 and speak...";
}

if (!SpeechRecognition) {
  // Browser has no speech recognition (e.g. Firefox)
  micBtn.disabled = true;
  micBtn.title = "Voice input is not supported in this browser. Please use Chrome or Edge.";
} else {
  recognition = new SpeechRecognition();
  recognition.lang = "en-IN";        // change to "en-US" if you prefer
  recognition.interimResults = true; // show words while you are speaking
  recognition.continuous = false;    // stop after one sentence

  recognition.onstart = () => setListening(true);
  recognition.onend = () => setListening(false);

  recognition.onresult = (event) => {
    const result = event.results[event.results.length - 1];
    const transcript = result[0].transcript.trim();
    inputEl.value = transcript;      // live preview in the text box
    if (result.isFinal && transcript) {
      inputEl.value = "";
      sendMessage(transcript);       // same flow as typing a question
    }
  };

  recognition.onerror = (event) => {
    const messages = {
      "not-allowed": "Microphone access is blocked. Click the lock icon in the address bar and allow the microphone.",
      "service-not-allowed": "Microphone access is blocked. Click the lock icon in the address bar and allow the microphone.",
      "no-speech": "I didn't hear anything. Please click 🎤 and try again.",
      "audio-capture": "No microphone was found. Please connect one and try again.",
      "network": "Voice recognition needs an internet connection.",
    };
    if (event.error === "aborted") return;
    addMessage(messages[event.error] || "Voice input failed. Please try again or type your question.",
               "bot", { isError: true });
  };

  micBtn.addEventListener("click", () => {
    if (sendBtn.disabled) return;    // wait while a reply is loading
    if (listening) {
      recognition.stop();
      return;
    }
    stopSpeaking();                  // stop the bot talking so it doesn't hear itself
    try {
      recognition.start();
    } catch (error) {
      setListening(false);
    }
  });
}