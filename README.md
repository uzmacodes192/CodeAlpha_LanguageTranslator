# CodeAlpha_LanguageTranslator

A web-based language translation tool. Built for the **CodeAlpha AI Internship – Task 1**.

## Features
- Enter text and choose **source** (or auto-detect) and **target** language
- Uses the **Google Translate** service via the `deep-translator` library (no API key needed)
- Translated text shown clearly, with a **copy button**
- **Text-to-speech** (🔊 Listen) using gTTS
- Supports 100+ languages
- Character counter (5000 limit), **download** translation as .txt, and **recent translations** history in the sidebar

## Project structure
```
CodeAlpha_LanguageTranslator/
├── app.py
├── requirements.txt
└── README.md
```

## Setup & run
```bash
pip install -r requirements.txt
streamlit run app.py
```
An internet connection is required (translation and speech are online services).

## Tech stack
Python, Streamlit, deep-translator (Google Translate), gTTS
