import os
import sys
import json
import logging

from openai import OpenAI

from typing import Union

from llmtool.genai.functions import get_default_handler
from llmtool.genai.history import ChatHistory
from llmtool.genai.message import (
    FunctionMessage,
    FunctionCallResultMessage,
    AssistantMessage,
    BaseMessage,
    UserMessage,
)
from llmtool.genai.prompts import DEFAULT as DEFAULT_PROMPT

class Agent:
    def __init__(
        self,
        model: str,
        conversation_name: str,
        max_token_count: int,
        disable_functions: bool,
        logger: logging.Logger,
    ):
        self.model = model
        self.conversation_name = conversation_name
        self.max_token_count = max_token_count
        self.chat_history = ChatHistory(conversation_name, DEFAULT_PROMPT)
        self.function_handler = get_default_handler()
        self.disable_functions = disable_functions
        self.logger = logger
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    def load_chat_history(self):
        self.chat_history.load()

    def save_chat_history(self):
        self.chat_history.truncate_by_token_count(self.max_token_count)
        self.chat_history.save()

    def handle_function_calls(
        self, message: FunctionMessage
    ) -> Union[AssistantMessage, FunctionMessage]:
        """
        Given a message from chatgpt, returns either a message with the result of
        the function call if a function call was made, or None if not
        """

        self.logger.debug(f"handling function call: {message.function_call}")
        function_call_result = str(
            self.function_handler.handle_function_call(
                name=message.function_call["name"],
                args=json.loads(message.function_call["arguments"]),
            )
        )

        function_call_result_message = FunctionCallResultMessage(
            name=message.function_call["name"],
            content=function_call_result,
        )

        actual_response = self.send_message(function_call_result_message)
        return actual_response

    def build_message_from_response(self, message) -> Union[FunctionMessage, AssistantMessage]:
        if message.function_call: 
            function_call = message.function_call
            return FunctionMessage(
                function_call=function_call,
            )
        else:
            return AssistantMessage(
                content=message.content,
            )

    def send_user_message(
        self, message_text: str
    ) -> Union[AssistantMessage, FunctionMessage]:
        user_message = UserMessage(content=message_text)
        return self.send_message(user_message)

    def send_message(
        self, message: Union[UserMessage, FunctionCallResultMessage]
    ) -> Union[AssistantMessage, FunctionMessage]:
        # Load chat history
        previous_messages = self.chat_history.load()

        self.chat_history.append(message)
        self.chat_history.truncate_by_token_count(self.max_token_count)
        self.logger.debug(f"chat history: {self.chat_history.to_json()}")

        if self.disable_functions:
            response = self.client.chat.completions.create(
                model=self.model, messages=self.chat_history.to_json()
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.chat_history.to_json(),
                functions=self.function_handler.to_json(),
            )

        response_message = self.build_message_from_response(
            response.choices[0].message
        )
        if type(response_message) == FunctionMessage:
            response_message = self.handle_function_calls(response_message.to_hash())

        # Append new messages to the chat history
        self.chat_history.append(response_message)
        self.chat_history.save()

        return response_message
