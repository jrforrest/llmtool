"""
genai chat message structures and serialization
"""

from dataclasses import dataclass


@dataclass
class BaseMessage:
    pass


@dataclass
class ContentMessage(BaseMessage):
    content: str

    def to_json(self):
        return {
            "role": self.role,
            "content": self.content,
        }


@dataclass
class UserMessage(ContentMessage):
    role: str = "user"
    pass


@dataclass
class AssistantMessage(ContentMessage):
    role: str = "assistant"
    pass


@dataclass
class SystemMessage(ContentMessage):
    role: str = "system"
    pass


@dataclass
class FunctionMessage(BaseMessage):
    function_call: dict
    role: str = "function"


@dataclass
class FunctionCallResultMessage(ContentMessage):
    name: str
    content: str
    role: str = "function"

    def to_json(self):
        return {
            "role": self.role,
            "name": self.name,
            "content": self.content,
        }


def message_from_json(message_json: dict) -> BaseMessage:
    if message_json["role"] == "user":
        return UserMessage(content=message_json["content"])
    elif message_json["role"] == "assistant":
        return AssistantMessage(content=message_json["content"])
    elif message_json["role"] == "system":
        return SystemMessage(content=message_json["content"])
    elif message_json["role"] == "function":
        if "content" in message_json:
            return FunctionCallResultMessage(
                name=message_json["name"],
                content=message_json["content"],
            )
        else:
            return FunctionMessage(
                function_call=message_json["function_call"],
            )
    else:
        raise Exception(f"Unknown message role {message_json['role']}")
