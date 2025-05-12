
        
from pedalboard import Pedalboard,  PitchShift, Distortion, Clipping, LadderFilter
from pedalboard.io import AudioFile
from pedalboard import LadderFilter
import numpy as np

def modify_voice_pedalboard(input_path, output_path):
    # Загрузка аудио (MP3 через AudioFile)
    with AudioFile(input_path, 'r') as f:
        audio = f.read(f.frames)
        sr = f.samplerate
    
    # Создание цепочки эффектов
    board = Pedalboard([
        PitchShift(semitones= -3),
        LadderFilter( mode = LadderFilter.Mode.BPF24, cutoff_hz = 300, resonance = 0.0, drive = 1.0),
    ])
    
    # Применение эффектов
    processed = board.process(audio, sr)
    
    # Сохранение результата
    with AudioFile(output_path, 'w', sr, processed.shape[0]) as f:
        f.write(processed)

# Использование:
modify_voice_pedalboard("test.mp3", "output_pedalboard.mp3")