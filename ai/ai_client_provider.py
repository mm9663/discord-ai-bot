from .ai_client import AIClient
from .kurobara_ai import KurobaraAI
from .ikeda_ai import IkedaAI
from .meu_ai import MeuAI
from .shapa_ai import ShapaAI
from .himari_ai import HimariAI
from .shiroko_ai import ShirokoAI


def get_ai_client(client_name) -> AIClient:
    if client_name == "kurobara":
        return KurobaraAI()
    elif client_name == "ikeda":
        return IkedaAI()
    elif client_name == "shapa":
        return ShapaAI()
    elif client_name == "meu":
        return MeuAI()
    elif client_name == "himari":
        return HimariAI()
    elif client_name == "shiroko":
        return ShirokoAI()
    else:
        raise ValueError(f"Invalid client name: {client_name}")
