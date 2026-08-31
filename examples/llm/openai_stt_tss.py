from enum import Enum
from typing import Optional, Dict, Any
from pm4py.util import exec_utils, constants
from tempfile import NamedTemporaryFile
import pm4py
import os
import sys
import subprocess
import importlib.util


class Parameters(Enum):
    API_KEY = "api_key"
    MODEL = "openai_model"
    RECORDING_DURATION = "recording_duration"
    VOICE = "voice"
    PLAY_SOUND = "play_sound"
    MAX_LEN = "max_len"


def check_ffmpeg_installed():
    try:
        # Try to execute "ffmpeg -version" command and capture its output
        result = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        # If the command was executed successfully, ffmpeg is installed
        return True
    except:
        # If the command execution leads to an error, ffmpeg is not installed
        return False


def speech_to_text(sound_file_path: Optional[str] = None, parameters: Optional[Dict[Any, Any]] = None) -> str:
    """
    Uses an OpenAI speech-to-text model

    Parameters
    ------------------
    sound_file_path
        If provided, path to a .mp3 file containing the voice to be transcribed as text. If not, a recording of the specified duration is started, and provided to the model.
    parameters
        Parameters of the method, including:
        - Parameters.API_KEY => the API key to be used
        - Parameters.MODEL => the speech-to-text model to be used (default: whisper-1)
        - Parameters.RECORDING_DURATION => the duration of the voice recording

    Returns
    -------------------
    text
        Transcription as text of the sound
    """
    if parameters is None:
        parameters = {}

    api_key = exec_utils.get_param_value(Parameters.API_KEY, parameters, constants.OPENAI_API_KEY)
    model = exec_utils.get_param_value(Parameters.MODEL, parameters, constants.OPENAI_DEFAULT_STT_MODEL)
    recording_duration = exec_utils.get_param_value(Parameters.RECORDING_DURATION, parameters, 10)

    if sound_file_path is None:
        import pyaudio
        from pydub import AudioSegment
        import wave

        # Audio recording parameters
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        CHUNK = 1024
        RECORD_SECONDS = recording_duration

        F = NamedTemporaryFile(suffix=".wav")
        WAVE_OUTPUT_FILENAME = F.name
        F.close()

        F = NamedTemporaryFile(suffix=".mp3")
        sound_file_path = F.name
        F.close()

        audio = pyaudio.PyAudio()

        # Start recording
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)
        print("Recording...")

        frames = []

        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)

        print("Finished recording.")

        # Stop recording
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Save the recorded data as a WAV file
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        sound = AudioSegment.from_wav(WAVE_OUTPUT_FILENAME)
        sound.export(sound_file_path, format="mp3")

    if sound_file_path is not None:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        transcript = client.audio.transcriptions.create(
            model=model,
            file=open(sound_file_path, "rb")
        )

        return transcript.text


def text_to_speech(stri: str, parameters: Optional[Dict[Any, Any]] = None) -> str:
    """
    Uses an OpenAI text-to-speech model

    Parameters
    ---------------
    stri
        String that needs to be translated to voice
    parameters
        Parameters of the algorithm, including:
        - Parameters.API_KEY => the API key of OpenAI to be used
        - Parameters.MODEL => the TTS model of OpenAI to be used (default: tts-1)
        - Parameters.VOICE => the voice of the TTS model to be used (default: alloy)
        - Parameters.PLAY_SOUND => boolean that determines if the voice should be played

    Returns
    ---------------
    stru
        Path to the .mp3 file obtained after the transcription
    """
    if parameters is None:
        parameters = {}

    api_key = exec_utils.get_param_value(Parameters.API_KEY, parameters, constants.OPENAI_API_KEY)
    model = exec_utils.get_param_value(Parameters.MODEL, parameters, constants.OPENAI_DEFAULT_TTS_MODEL)
    voice = exec_utils.get_param_value(Parameters.VOICE, parameters, constants.OPENAI_DEFAULT_TTS_VOICE)
    max_len = exec_utils.get_param_value(Parameters.MAX_LEN, parameters, 4096)
    play_sound = exec_utils.get_param_value(Parameters.PLAY_SOUND, parameters, True)

    F = NamedTemporaryFile(suffix=".mp3")
    speech_file_path = F.name
    F.close()

    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    if len(stri) > max_len:
        # TTS limit
        stri = stri[:max_len]

    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=stri
    )

    response.stream_to_file(speech_file_path)

    if play_sound:
        if importlib.util.find_spec("pygame"):
            # if the user installed pygame, use that to seamlessy play the .mp3 file
            import pygame

            pygame.mixer.init()
            pygame.mixer.music.load(speech_file_path)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        else:
            # calls the system .mp3 opener
            if sys.platform.startswith('darwin'):
                subprocess.call(('open', speech_file_path))
            elif os.name == 'nt':  # For Windows
                os.startfile(speech_file_path)
            elif os.name == 'posix':  # For Linux, Mac, etc.
                subprocess.call(('xdg-open', speech_file_path))

    return speech_file_path


if __name__ == "__main__":
    if not check_ffmpeg_installed():
        raise Exception("install ffmpeg and add it to the environment variables!")

    if not importlib.util.find_spec("pydub") or not importlib.util.find_spec("pyaudio"):
        raise Exception("install pydub and pyaudio using pip!")

    api_key = "sk-"

    log = pm4py.read_xes("../../tests/compressed_input_data/15_bpic2020_permit_log_1t_per_variant.xes.gz")
    var_abstr = pm4py.llm.abstract_variants(log)

    parameters = {}

    parameters["api_key"] = api_key # OpenAI key
    parameters["recording_duration"] = 6  # 6 seconds recording duration

    print("Please insert your inquiry:")
    user_inquiry = speech_to_text(None, parameters=parameters)
    print("This is your inquiry:", user_inquiry)

    print("Now your inquiry is vocalized before execution:")
    text_to_speech(user_inquiry, parameters=parameters)

    prompt = var_abstr + "\n\n" + user_inquiry

    response = pm4py.llm.openai_query(prompt, api_key=api_key)
    print("This is the response of the OpenAI model:", response)

    print("Now the response is vocalized:")
    text_to_speech(response, parameters=parameters)
