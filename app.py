"""Language Translation Tool (no-limit edition). Run: streamlit run app.py

Engines (tried in this order in "Auto" mode):
  1. Google Translate  (deep-translator, free, can rate-limit)
  2. MyMemory          (free backup)
  3. Offline (Argos)   (runs on your PC, never rate-limited; optional install)
Results are cached, so translating the same text again sends no request.
"""
import io
import time

import streamlit as st
from deep_translator import GoogleTranslator

st.set_page_config(page_title="Language Translator", page_icon="🌐")
st.title("🌐 Language Translation Tool")

FALLBACK_LANGS = {
    "english": "en", "hindi": "hi", "french": "fr", "german": "de", "spanish": "es",
    "japanese": "ja", "korean": "ko", "chinese (simplified)": "zh-CN", "arabic": "ar",
    "russian": "ru", "portuguese": "pt", "italian": "it", "tamil": "ta", "telugu": "te",
    "bengali": "bn", "marathi": "mr", "gujarati": "gu", "urdu": "ur", "punjabi": "pa",
}


@st.cache_data
def get_languages():
    try:
        return GoogleTranslator().get_supported_languages(as_dict=True)
    except Exception:
        return FALLBACK_LANGS


LANGS = get_languages()
names = sorted(LANGS.keys())


# ---------------------------------------------------------------- engines
def google_translate(text, src_code, tgt_code, **_):
    return GoogleTranslator(source=src_code, target=tgt_code).translate(text)


def mymemory_translate(text, src_code, tgt_code, src_name="", tgt_name="", **_):
    from deep_translator import MyMemoryTranslator

    # MyMemory has no auto-detect: assume English when auto-detect is chosen
    source = "english" if src_code == "auto" else src_name
    return MyMemoryTranslator(source=source, target=tgt_name).translate(text)


def _ensure_argos_pair(src, tgt):
    """Download an offline language pair once (needs internet only the first time)."""
    import argostranslate.package as pkg

    installed = {(p.from_code, p.to_code) for p in pkg.get_installed_packages()}
    if (src, tgt) in installed:
        return
    pkg.update_package_index()
    for p in pkg.get_available_packages():
        if p.from_code == src and p.to_code == tgt:
            pkg.install_from_path(p.download())
            return
    raise RuntimeError(f"No offline model for {src} -> {tgt}")


def argos_translate(text, src_code, tgt_code, **_):
    import argostranslate.translate as tr

    src = "en" if src_code == "auto" else src_code.split("-")[0]
    if src_code == "auto":
        try:  # optional auto-detect
            from langdetect import detect

            src = detect(text).split("-")[0]
        except Exception:
            pass
    tgt = tgt_code.split("-")[0]
    if src == tgt:
        return text
    # Argos pivots through English, so make sure the needed pairs exist
    if src == "en" or tgt == "en":
        _ensure_argos_pair(src, tgt)
    else:
        _ensure_argos_pair(src, "en")
        _ensure_argos_pair("en", tgt)
    return tr.translate(text, src, tgt)


ENGINES = {
    "Google": google_translate,
    "MyMemory": mymemory_translate,
    "Offline (Argos)": argos_translate,
}


@st.cache_data(show_spinner=False, max_entries=200)
def translate_cached(text, src_code, tgt_code, src_name, tgt_name, mode):
    """Returns (translation, engine_used). Cached: same input = no new request."""
    if mode == "Offline only":
        order = ["Offline (Argos)"]
    elif mode == "Google only":
        order = ["Google"]
    else:
        order = ["Google", "MyMemory", "Offline (Argos)"]

    errors = []
    for name in order:
        try:
            result = ENGINES[name](text, src_code, tgt_code, src_name=src_name, tgt_name=tgt_name)
            if result and result.strip():
                return result, name
        except ModuleNotFoundError:
            errors.append(f"{name}: not installed (see README: offline mode)")
        except Exception as e:
            errors.append(f"{name}: {str(e)[:120]}")
            time.sleep(0.5)
    raise RuntimeError(" | ".join(errors))


# --------------------------------------------------------------------- UI
with st.sidebar:
    st.header("Settings")
    mode = st.radio(
        "Translation engine",
        ["Auto (recommended)", "Google only", "Offline only"],
        help="Auto tries Google, then MyMemory, then the offline translator. "
             "Offline never hits any limit but needs `pip install argostranslate`.",
    )

col1, col2 = st.columns(2)
with col1:
    src = st.selectbox("From", ["auto-detect"] + names, index=0)
with col2:
    tgt = st.selectbox("To", names, index=names.index("hindi") if "hindi" in names else 0)

text = st.text_area("Enter text", height=150, max_chars=5000,
                    placeholder="Type or paste text here...")
st.caption(f"{len(text)} / 5000 characters")

if "history" not in st.session_state:
    st.session_state.history = []

if st.button("Translate", type="primary"):
    if not text.strip():
        st.warning("Please enter some text first.")
    else:
        try:
            src_code = "auto" if src == "auto-detect" else LANGS[src]
            with st.spinner("Translating..."):
                result, engine = translate_cached(
                    text.strip(), src_code, LANGS[tgt], src, tgt, mode.split(" (")[0])
            st.session_state.result = result
            st.session_state.engine = engine
            st.session_state.tgt_code = LANGS[tgt]
            st.session_state.history.insert(0, (text, tgt, result))
            st.session_state.history = st.session_state.history[:5]
        except Exception as e:
            st.error(f"Translation failed. {e}")
            st.info("Tip: choose **Offline only** in the sidebar (after installing "
                    "`argostranslate`) to avoid all online limits.")

with st.sidebar:
    st.header("Recent translations")
    if not st.session_state.history:
        st.caption("Nothing yet.")
    for src_text, lang, out in st.session_state.history:
        st.markdown(f"**{src_text[:40]}{'…' if len(src_text) > 40 else ''}** → *{lang}*")
        st.caption(out[:80] + ("…" if len(out) > 80 else ""))

if st.session_state.get("result"):
    st.subheader("Translation")
    # st.code shows a built-in copy button at the top-right of the box
    st.code(st.session_state.result, language=None, wrap_lines=True)
    st.caption(f"Engine used: {st.session_state.get('engine', '-')}  •  "
               "Use the copy icon on the top-right of the box to copy.")

    st.download_button("⬇ Download as .txt", st.session_state.result,
                       file_name="translation.txt")

    if st.button("🔊 Listen"):
        try:
            from gtts import gTTS

            audio = io.BytesIO()
            gTTS(st.session_state.result, lang=st.session_state.tgt_code.split("-")[0]).write_to_fp(audio)
            st.audio(audio.getvalue(), format="audio/mp3")
        except Exception as e:
            st.error(f"Text-to-speech not available for this language: {e}")