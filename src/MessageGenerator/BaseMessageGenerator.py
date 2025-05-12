from src.MessageGenerator.MessageGeneratorTransformers import MessageGeneratorTransformers
from src.MessageGenerator.MessageGeneratorOpenRouter import MessageGeneratorOpenRouter
from enum import Enum, auto

class RequesterClass(Enum):
    Base = auto()
    GameMaster = auto()
    Actor = auto()
    ImagePromter = auto()
    DialogProcessor = auto()
    Tester = auto()



def get_base_message_generator(requester: RequesterClass = RequesterClass.Base):
    
    if requester == RequesterClass.Base:
        return MessageGeneratorOpenRouter()
    if requester == RequesterClass.GameMaster:
        return MessageGeneratorOpenRouter()
    if requester == RequesterClass.Actor:
        return MessageGeneratorOpenRouter()
    if requester == RequesterClass.ImagePromter:
        return MessageGeneratorOpenRouter()
    if requester == RequesterClass.DialogProcessor:
        return MessageGeneratorOpenRouter()
    if requester == RequesterClass.Tester:
        return MessageGeneratorOpenRouter()
    
    return MessageGeneratorOpenRouter()
