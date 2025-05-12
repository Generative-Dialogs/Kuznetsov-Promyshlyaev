from typing import Protocol, Optional, List


class ImageGeneratorProtocol(Protocol):
    """!
    @brief Протокол для генерации изображений
    
    @details
    Определяет интерфейс для классов, реализующих генерацию изображений.
    Используется как контракт для различных реализаций генераторов изображений.
    """
    def generate_image_response(self, prompt: str, target_path: str, character_images: Optional[List[str]] = None) -> Optional[str]:
        """!
        @brief Генерация изображения на основе промпта и опциональных изображений персонажей
        
        @param prompt Текстовый промпт для генерации изображения
        @param target_path Полный путь для сохранения изображения
        @param character_images Опциональный список путей к изображениям персонажей
        
        @return Optional[str] Путь к сохраненному изображению или None в случае ошибки
        """
        ... 