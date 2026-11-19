import os
import uuid
from typing import Tuple
from app.services.gemini_service import gemini_service
from app.services.session_store import session_store


class AudioService:
    """
    Manages private audio storage and speech-to-text transcription.
    """

    SUPPORTED_MIME_TYPES = {
        "audio/webm": ".webm",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mp3": ".mp3",
        "audio/mpeg": ".mp3",
        "audio/ogg": ".ogg",
        "audio/m4a": ".m4a",
        "audio/mp4": ".mp4",
    }

    def save_recording(self, session_id: str, audio_bytes: bytes, mime_type: str = "audio/webm") -> Tuple[str, str]:
        """
        Save audio bytes into the session's private storage directory.
        Returns: (filename, full_path)
        """
        clean_mime = mime_type.split(";")[0].strip().lower()
        ext = self.SUPPORTED_MIME_TYPES.get(clean_mime, ".webm")
        rec_id = f"rec_{uuid.uuid4().hex[:12]}"
        filename = f"{rec_id}{ext}"
        filepath = session_store.get_recording_path(session_id, filename)

        with open(filepath, "wb") as f:
            f.write(audio_bytes)

        return filename, filepath

    def transcribe(self, session_id: str, audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
        """
        Transcribe audio using Gemini multimodal audio capabilities.
        """
        clean_mime = mime_type.split(";")[0].strip().lower()
        if not audio_bytes or len(audio_bytes) < 100:
            return "[Empty recording received]"

        try:
            transcript = gemini_service.transcribe_audio(audio_bytes, mime_type=clean_mime)
            return transcript.strip()
        except Exception as exc:
            print(f"Transcription error: {exc}")
            return f"[Transcription unavailable: {exc}]"


audio_service = AudioService()
