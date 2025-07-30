# Habit‑Motivation Chatbot

Welcome to the Habit Formation & Motivation Bot! This project was
created to help recent graduates (especially those in technical or
engineering fields) build and sustain healthy daily habits while they
search for full‑time opportunities. Whether you're trying to stay
active, read more, journal regularly or keep up with job
applications, this bot provides structure, encouragement and positive
reinforcement along the way.

## 🎯 Project Overview

The chatbot runs locally and guides users through selecting or defining
habits, logging daily progress and celebrating milestones. It uses a
lightweight SQLite database to persist user data and employs
OpenAI's language models (via the LangChain library) to generate
personalised motivational messages. If no API key is provided the bot
falls back to a small pool of hand‑curated quotes, ensuring you
always receive a boost of encouragement.

## ✨ Features

- **Choose & track custom habits:** Define your own habits (e.g. "apply to two jobs", "30‑minute jog", "daily journaling") and manage them through the bot.
- **Daily check‑ins:** Quickly record whether you completed a habit today. Streaks are automatically calculated.
- **Motivational responses:** Receive supportive, witty and human‑like encouragement tailored to your current streak and chosen habit. When an OpenAI API key is set, the bot uses GPT‑3.5 to craft bespoke messages.
- **Milestone celebrations:** Enjoy special recognition when you hit 3‑, 7‑ and 10‑day streaks (with room to extend further).
- **Persistent storage:** Data is stored in a local SQLite database so you can stop and restart the bot without losing progress.

## 🛠 Prerequisites

* Python **3.9** or higher
* An OpenAI API key (optional but recommended for AI‑generated messages)

## 🚀 Installation

Clone the repository and install dependencies using `pip`:

```bash
git clone https://github.com/aditya-sudo/habit-motivation-chatbot.git
cd habit‑motivation‑chatbot
pip install -r requirements.txt
```

## 🔑 Environment Setup

To enable AI‑generated motivational messages you must provide your
OpenAI API key as an environment variable. On most Unix shells you can
set it like this:

```bash
export OPENAI_API_KEY=your‑api‑key
```

If you don't set the key the bot will still run and will use
built‑in quotes for encouragement.

## ▶️ Running the Bot

Launch the chatbot from your terminal:

```bash
python chatbot.py
```

The bot will greet you, prompt for your name, and walk you through
selecting or creating habits. From there you can log daily progress,
check your current streaks or add new habits. Press `Ctrl+C` or
choose the exit option to quit.

## 🔧 Optional Enhancements

The current command‑line interface keeps dependencies minimal and
portable. If you'd like to extend the project consider:

- **Graphical user interface (GUI):** Use Tkinter or a lightweight web
  framework (like Flask) to build a user‑friendly dashboard.
- **Messaging platform integration:** Connect the bot to Telegram,
  Discord or Slack using their respective APIs so reminders and
  check‑ins happen in your chat app of choice.
- **Scheduled notifications:** Incorporate the provided
  `scheduler.py` module to send daily reminders at specific times.
- **Sentiment analysis:** Integrate NLTK or Hugging Face transformers
  to detect the user's mood and adjust motivational tone accordingly.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file
for details.