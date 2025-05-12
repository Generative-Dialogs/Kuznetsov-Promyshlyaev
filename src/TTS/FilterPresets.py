from typing import Dict, Any
from pedalboard import LadderFilter
from src.TTS.FilterPresetsType import FilterPresetsType

class FilterPresets:
    """!
    @brief Класс для хранения пресетов фильтров
    """
    
    @staticmethod
    def get_presets() -> Dict[FilterPresetsType, Dict[str, Any]]:
        """!
        @brief Получение всех пресетов фильтров
        
        @return Dict[FilterPreset, Dict[str, Any]] Словарь пресетов
        """
        return {
            FilterPresetsType.REALISTIC: {
                'mode': LadderFilter.Mode.BPF24,
                'cutoff_hz': 300,
                'resonance': 0.0,
                'drive': 1
            }
        } 