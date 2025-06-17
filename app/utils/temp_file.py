from tempfile import NamedTemporaryFile

def save_audio_tempfile(audio_data: bytes, temp_dir: str) -> str:
    with NamedTemporaryFile(delete=False, suffix=".wav", dir=temp_dir) as f:
        f.write(audio_data)
        return f.name
