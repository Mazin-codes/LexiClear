import os
import numpy as np
import soundfile as sf
import torch

from kokoro import KPipeline
from transformers import VitsModel, AutoTokenizer


# ============================================================
# MODEL CONFIGURATION
# ============================================================

KOKORO_REPO = "hexgrad/Kokoro-82M"
KANNADA_MODEL = "facebook/mms-tts-kan"


# ============================================================
# KOKORO CONFIGURATION
# ============================================================

LANGUAGE_CONFIG = {
    "English": {
        "code": "a",
        "voice": "af_heart",
    },
    "Hindi": {
        "code": "h",
        "voice": "hf_alpha",
    },
}


# Cache Kokoro pipelines so models are not loaded
# for every request.
_PIPELINES = {}


# ============================================================
# KANNADA MODEL CACHE
# ============================================================

_kannada_tokenizer = None
_kannada_model = None


# ============================================================
# KOKORO PIPELINE
# ============================================================

def get_pipeline(language: str):
    """Load and cache the Kokoro pipeline for English or Hindi."""

    if language not in LANGUAGE_CONFIG:
        raise ValueError(
            f"Kokoro does not support {language} "
            "in this LexiClear configuration."
        )

    if language not in _PIPELINES:

        language_code = LANGUAGE_CONFIG[language]["code"]

        print(f"Loading Kokoro TTS for {language}...")

        _PIPELINES[language] = KPipeline(
            lang_code=language_code,
            repo_id=KOKORO_REPO,
        )

    return _PIPELINES[language]


# ============================================================
# KANNADA MODEL LOADER
# ============================================================

def load_kannada_tts():
    """
    Load and cache the Facebook MMS Kannada TTS model.

    The model is loaded only when Kannada speech is requested.
    """

    global _kannada_tokenizer
    global _kannada_model

    if _kannada_model is not None:
        return _kannada_tokenizer, _kannada_model

    print("Loading Kannada TTS...")

    # Apple Silicon GPU if available.
    if torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    print(f"Using Kannada TTS device: {device}")

    _kannada_tokenizer = AutoTokenizer.from_pretrained(
        KANNADA_MODEL
    )

    _kannada_model = VitsModel.from_pretrained(
        KANNADA_MODEL
    ).to(device)

    _kannada_model.eval()

    return _kannada_tokenizer, _kannada_model


# ============================================================
# KANNADA SPEECH GENERATION
# ============================================================

def generate_kannada_speech(
    text: str,
    output_path: str,
):
    """Generate Kannada speech using Facebook MMS TTS."""

    tokenizer, model = load_kannada_tts()

    device = next(model.parameters()).device

    inputs = tokenizer(
        text,
        return_tensors="pt",
    )

    inputs = {
        key: value.to(device)
        for key, value in inputs.items()
    }

    print("Generating Kannada speech...")

    with torch.no_grad():

        output = model(
            **inputs
        ).waveform

    audio = output.squeeze().cpu().numpy()

    sf.write(
        output_path,
        audio,
        model.config.sampling_rate,
    )

    print(f"Kannada TTS FILE: {output_path}")

    return output_path


# ============================================================
# KOKORO SPEECH GENERATION
# ============================================================

def generate_kokoro_speech(
    text: str,
    language: str,
    output_path: str,
):
    """Generate English or Hindi speech using Kokoro."""

    pipeline = get_pipeline(language)

    voice = LANGUAGE_CONFIG[language]["voice"]

    generator = pipeline(
        text,
        voice=voice,
    )

    audio_chunks = []

    for _, _, audio in generator:

        if audio is not None:
            audio_chunks.append(audio)

    if not audio_chunks:
        raise RuntimeError(
            "Kokoro did not generate any audio."
        )

    audio = np.concatenate(audio_chunks)

    sf.write(
        output_path,
        audio,
        24000,
    )

    print(f"Kokoro TTS FILE: {output_path}")

    return output_path


# ============================================================
# MAIN TTS FUNCTION
# ============================================================

def generate_speech(
    text: str,
    language: str,
    output_path: str = "answer.wav",
):
    """
    Generate speech for LexiClear.

    English -> Kokoro
    Hindi   -> Kokoro
    Kannada -> Facebook MMS TTS
    """

    if not text or not text.strip():
        raise ValueError(
            "Text cannot be empty."
        )

    language = language.strip()

    print()
    print("========================================")
    print("LEXICLEAR TEXT-TO-SPEECH")
    print("========================================")
    print("TTS LANGUAGE:", language)
    print("TTS TEXT:", text[:200])
    print("========================================")

    # --------------------------------------------------------
    # KANNADA
    # --------------------------------------------------------

    if language == "Kannada":

        return generate_kannada_speech(
            text=text,
            output_path=output_path,
        )

    # --------------------------------------------------------
    # ENGLISH / HINDI
    # --------------------------------------------------------

    if language in ("English", "Hindi"):

        return generate_kokoro_speech(
            text=text,
            language=language,
            output_path=output_path,
        )

    # --------------------------------------------------------
    # UNSUPPORTED LANGUAGE
    # --------------------------------------------------------

    raise ValueError(
        "Supported TTS languages are English, Hindi, and Kannada."
    )