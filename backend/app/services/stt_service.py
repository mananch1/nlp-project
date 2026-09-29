import logging
import os
import requests
from pathlib import Path
from typing import Tuple
from ..config import settings

logger = logging.getLogger(__name__)

def convert_to_pcm_wav(input_path: str, output_path: str) -> bool:
    """Converts input audio file to 16kHz mono standard PCM WAV using soundfile/torchaudio"""
    try:
        import soundfile as sf
        data, samplerate = sf.read(input_path)
        # Convert stereo to mono if needed
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        sf.write(output_path, data, samplerate, subtype='PCM_16')
        return True
    except Exception as e:
        logger.debug(f"Soundfile conversion failed ({e}), checking torchaudio...")
        try:
            import torchaudio
            waveform, sample_rate = torchaudio.load(input_path)
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
            torchaudio.save(output_path, waveform, sample_rate)
            return True
        except Exception as e2:
            logger.warning(f"Audio conversion failed: {e2}")
            return False

def transcribe_audio_file(audio_path: str, language_code: str = "hi-IN") -> Tuple[str, str]:
    """
    Transcribes spoken voice query from an audio recording.
    Multi-tier:
    1. Sarvam AI Saarika v2 Indic STT API if API key is provided.
    2. Google Speech Recognition via speech_recognition (free, multilingual Indic + English).
    3. Graceful fallback if speech is inaudible.
    """
    # 1. Sarvam AI Saarika STT
    if settings.SARVAM_API_KEY:
        try:
            logger.info(f"Calling Sarvam Saarika STT API for audio: {audio_path}")
            url = f"{settings.SARVAM_BASE_URL}/speech-to-text"
            headers = {"api-subscription-key": settings.SARVAM_API_KEY}
            
            with open(audio_path, "rb") as f:
                files = {"file": (Path(audio_path).name, f, "audio/wav")}
                data = {
                    "model": settings.SARVAM_STT_MODEL,
                    "language_code": language_code
                }
                resp = requests.post(url, headers=headers, files=files, data=data, timeout=20)
                resp.raise_for_status()
                res_data = resp.json()
                transcript = res_data.get("transcript", "").strip()
                detected_lang = res_data.get("language_code", language_code)
                if transcript:
                    return transcript, detected_lang
        except Exception as e:
            logger.warning(f"Sarvam STT failed: {e}. Falling back to SpeechRecognition.")

    # 2. SpeechRecognition Google API
    try:
        import speech_recognition as sr

        # Ensure standard PCM wav
        pcm_wav_path = str(audio_path).replace(".wav", "_pcm.wav")
        if not convert_to_pcm_wav(audio_path, pcm_wav_path):
            pcm_wav_path = audio_path

        recognizer = sr.Recognizer()
        with sr.AudioFile(pcm_wav_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio_data = recognizer.record(source)

        # Recognize using Google Speech
        # Try requested language first, fallback to en-IN or hi-IN
        transcript = ""
        try:
            transcript = recognizer.recognize_google(audio_data, language=language_code)
        except sr.UnknownValueError:
            alt_lang = "en-IN" if "hi" in language_code.lower() else "hi-IN"
            try:
                transcript = recognizer.recognize_google(audio_data, language=alt_lang)
            except Exception:
                pass

        if Path(pcm_wav_path).exists() and pcm_wav_path != audio_path:
            try:
                Path(pcm_wav_path).unlink()
            except Exception:
                pass

        if transcript and transcript.strip():
            # Check script of transcript
            has_devanagari = any(0x0900 <= ord(c) <= 0x097F for c in transcript)
            lang = "hi" if has_devanagari or "hi" in language_code.lower() else "en"
            logger.info(f"Speech successfully transcribed: '{transcript}' (lang={lang})")
            return transcript.strip(), lang

    except Exception as e:
        logger.warning(f"Local speech recognition failed: {e}")

    # Fallback if audio could not be deciphered
    if "hi" in language_code.lower():
        return "ऑडियो पहचान में नहीं आया, क्या आप कृपया अपना सवाल टेक्स्ट में लिख सकते हैं?", "hi"
    return "Speech could not be recognized clearly. Could you please rephrase or type your query?", "en"
