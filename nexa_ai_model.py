from flask import Flask, request, render_template_string
import requests
import re

app = Flask(__name__)

NEXA_URL = "http://127.0.0.1:18181/v1/chat/completions"
MODEL = "NexaAI/Qwen3-0.6B-GGUF"

HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexa Local Chat</title>
    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Inter, Segoe UI, Arial, sans-serif;
            background: linear-gradient(135deg, #0f172a, #1e293b, #334155);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }

        .app {
            width: 100%;
            max-width: 980px;
            height: 90vh;
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(14px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 24px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
            display: flex;
            flex-direction: column;
        }

        .topbar {
            padding: 20px 24px;
            background: rgba(255, 255, 255, 0.08);
            border-bottom: 1px solid rgba(255, 255, 255, 0.12);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .title-wrap h1 {
            margin: 0;
            font-size: 24px;
            color: #f8fafc;
            font-weight: 700;
        }

        .title-wrap p {
            margin: 6px 0 0;
            color: #cbd5e1;
            font-size: 14px;
        }

        .status {
            padding: 8px 14px;
            border-radius: 999px;
            background: rgba(34, 197, 94, 0.16);
            color: #bbf7d0;
            font-size: 13px;
            font-weight: 600;
            border: 1px solid rgba(34, 197, 94, 0.28);
        }

        .chat-area {
            flex: 1;
            overflow-y: auto;
            padding: 28px 22px;
            background: linear-gradient(to bottom, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
            scroll-behavior: smooth;
        }

        .empty-state {
            color: #cbd5e1;
            text-align: center;
            margin-top: 100px;
            opacity: 0.85;
        }

        .message-row {
            display: flex;
            margin-bottom: 18px;
        }

        .message-row.user {
            justify-content: flex-end;
        }

        .message-row.assistant {
            justify-content: flex-start;
        }

        .bubble {
            max-width: 100vh;
            padding: 14px 16px;
            border-radius: 18px;
            line-height: 1;
            font-size: 15px;
            white-space: pre-wrap;
            word-wrap: break-word;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        }

        .user .bubble {
            background: linear-gradient(135deg, #2563eb, #3b82f6);
            color: white;
            border-bottom-right-radius: 6px;
        }

        .assistant .bubble {
            background: rgba(255, 255, 255, 0.92);
            color: #0f172a;
            border-bottom-left-radius: 6px;
        }

        .meta {
            font-size: 12px;
            margin-bottom: 6px;
            opacity: 0.8;
            font-weight: 600;
        }

        .input-wrap {
            padding: 18px;
            background: rgba(15, 23, 42, 0.65);
            border-top: 1px solid rgba(255, 255, 255, 0.10);
        }

        .input-card {
            display: flex;
            gap: 12px;
            align-items: flex-end;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 18px;
            padding: 12px;
        }

        textarea {
            flex: 1;
            resize: none;
            border: none;
            outline: none;
            background: transparent;
            color: #f8fafc;
            font-size: 15px;
            min-height: 54px;
            max-height: 160px;
            font-family: inherit;
        }

        textarea::placeholder {
            color: #94a3b8;
        }

        button {
            border: none;
            outline: none;
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: white;
            padding: 14px 18px;
            border-radius: 14px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            min-width: 90px;
            transition: transform 0.15s ease, opacity 0.15s ease;
        }

        button:hover {
            transform: translateY(-1px);
            opacity: 0.95;
        }

        button:active {
            transform: translateY(0);
        }

        @media (max-width: 768px) {
            .app {
                height: 95vh;
                border-radius: 18px;
            }

            .bubble {
                max-width:100%;
            }

            .topbar {
                padding: 16px;
            }

            .title-wrap h1 {
                font-size: 20px;
            }

            .status {
                display: none;
            }
        }
    </style>
</head>
<body>
    <div class="app">
        <div class="topbar">
            <div class="title-wrap">
                <h1>Nexa Local Chat</h1>
                <p>Your private AI assistant running on your machine</p>
            </div>
            <div class="status">Local Model Online</div>
        </div>

        <div class="chat-area" id="chatArea">
            {% if messages %}
                {% for role, content in messages %}
                    <div class="message-row {{ role }}">
                        <div class="bubble">
                            <div class="meta">{{ "You" if role == "user" else "Assistant" }}</div>
                            <div>{{ content }}</div>
                        </div>
                    </div>
                {% endfor %}
            {% else %}
                <div class="empty-state">
                    <h2>Start the conversation</h2>
                    <p>Ask anything and chat with your local Nexa model.</p>
                </div>
            {% endif %}
        </div>

        <div class="input-wrap">
            <form method="post" class="input-card">
                <textarea name="message" id="messageBox" placeholder="Type your message..." required></textarea>
                <button type="submit">Send</button>
            </form>
        </div>
    </div>

    <script>
        const chatArea = document.getElementById("chatArea");
        chatArea.scrollTop = chatArea.scrollHeight;

        const textarea = document.getElementById("messageBox");
        textarea.addEventListener("input", function () {
            this.style.height = "auto";
            this.style.height = Math.min(this.scrollHeight, 160) + "px";
        });
    </script>
</body>
</html>
"""

messages = []

def clean_bot_response(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()

@app.route("/", methods=["GET", "POST"])
def chat():
    global messages

    if request.method == "POST":
        user_msg = request.form.get("message", "").strip()
        if user_msg:
            messages.append(("user", user_msg))

            api_messages = [{"role": role, "content": content} for role, content in messages]

            payload = {
                "model": MODEL,
                "messages": api_messages,
                "max_tokens": 256
            }

            try:
                r = requests.post(NEXA_URL, json=payload, timeout=120)
                r.raise_for_status()
                data = r.json()
                answer = data["choices"][0]["message"]["content"]
                answer = clean_bot_response(answer)
            except requests.exceptions.ConnectionError:
                answer = "Nexa server is not running. Start it first using: nexa serve"
            except requests.exceptions.Timeout:
                answer = "Nexa server timed out."
            except requests.exceptions.RequestException as e:
                answer = f"Nexa API request failed: {e}"
            except Exception as e:
                answer = f"Unexpected error: {e}"

            messages.append(("assistant", answer))

    return render_template_string(HTML, messages=messages)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)