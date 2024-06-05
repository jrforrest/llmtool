"""
Persistence of chat history
"""

import os, json

from llmtool.genai.message import (
    ContentMessage,
    FunctionMessage,
    SystemMessage,
    message_from_json,
)

import tiktoken

ENCODING_NAME = "cl100k_base"


def count_tokens(msg):
    if hasattr(msg, "content") and msg.content:
        encoding = tiktoken.get_encoding(ENCODING_NAME)
        tokens = encoding.encode(msg.content)
        return len(tokens)
    else:
        return 0


class ChatHistory:
    messages: list[ContentMessage]

    def __init__(self, conversation_name: str, prompt: str):
        self.conversation_name = conversation_name
        self.messages = []
        self.file_path = os.path.expanduser(
            f"~/tmp/chgpt_hist-{self.conversation_name}.json"
        )
        self.prompt_message = SystemMessage(prompt)

    def get_token_count(self) -> int:
        return sum(count_tokens(msg) for msg in self.messages)

    def truncate_by_token_count(self, max_tokens: int):
        token_count = self.get_token_count()
        if token_count > max_tokens:
            diff = token_count - max_tokens
            # Remove messages from the beginning of the history until token count is below threshold
            while diff > 0 and self.messages:
                msg = self.messages.pop(0)
                diff -= count_tokens(msg)

    def append(self, message):
        self.messages.append(message)

    def save(self):
        # Save updated chat history
        with open(self.file_path, "w") as f:
            json.dump([m.to_json() for m in self.messages], f)

    def load(self):
        if len(self.messages) > 0:
            return self.messages

        if os.path.isfile(self.file_path):
            with open(self.file_path, "r") as f:
                self.messages = list(message_from_json(m) for m in json.load(f))

        return self.messages

    def to_json(self):
        return [self.prompt_message.to_json()] + [m.to_json() for m in self.messages]
