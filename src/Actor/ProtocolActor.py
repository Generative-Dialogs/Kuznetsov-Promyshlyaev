from typing import Protocol
from src.GameMaster.ProtocolGameMaster import ProtocolGameMaster
from src.MessageGenerator.ProtocolMessageGenerator import ProtocolMessageGenerator


class ProtocolActor(Protocol):
    """!
    @brief Протокол для актора в игровой системе
    
    @details
    Определяет интерфейс для актора, который отвечает за
    генерацию детализированных действий и описаний в игре.
    Актор преобразует команды мастера игры в нарративные описания.
    """
    __name: str
    __description: str
    __game_master: ProtocolGameMaster
    __messageGenerator: ProtocolMessageGenerator

    def get_detailed_action(self, game_master_output: str) -> str:
        """!
        @brief Получение детализированного описания действия
        
        @param game_master_output Выходные данные мастера игры
        @return str Детализированное описание действия
        
        @details
        Преобразует команды мастера игры в подробное
        нарративное описание действий и событий.
        """
        ...