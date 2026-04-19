"""Classe base para agentes de IA com System Instructions."""

from dataclasses import dataclass, field


@dataclass
class BaseAgent:
    """Agente base com nome, role e system instruction.

    Uso:
        class MigrationAgent(BaseAgent):
            def run(self, data: dict) -> dict:
                # lógica de decisão
                ...
    """

    name: str
    role: str
    system_instruction: str = ""
    temperature: float = 0.7
    metadata: dict = field(default_factory=dict)

    def prompt(self, user_message: str) -> list[dict[str, str]]:
        """Monta a lista de mensagens no formato OpenAI-compatible."""
        messages = []
        if self.system_instruction:
            messages.append({"role": "system", "content": self.system_instruction})
        messages.append({"role": "user", "content": user_message})
        return messages
