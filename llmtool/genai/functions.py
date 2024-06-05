"""
Provides facilities for allowing chatgpt to call functions, as well as some default
functions
"""

from typing import Union, Callable

import os

from llmtool.genai import documents


class Function:
    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict,
        required: list,
        function: Callable,
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.required = required
        self.function = function

    def __call__(self, **kwargs):
        return self.function(**kwargs)

    def to_json(self):
        """
        provides the json structure used by openai to define functions that
        chatgpt can call
        """

        def parameters_json():
            return {
                "type": "object",
                "properties": self.parameters,
            }

        return {
            "name": self.name,
            "description": self.description,
            "parameters": parameters_json(),
        }


class UnknownFunction(Exception):
    pass


class FunctionHandler:
    def __init__(self):
        self.functions = {}

    def define_function(
        self,
        name: str,
        description: str,
        parameters: dict,
        required: list,
        function: Callable,
    ):
        self.functions[name] = Function(
            name, description, parameters, required, function
        )

    def handle_function_call(self, name: str, args: dict) -> str:
        if not name in self.functions:
            raise UnknownFunction(f"Unknown chgpt function {name}")

        function = self.functions[name]
        return function(**args)

    def to_json(self):
        return [f.to_json() for f in self.functions.values()]


def get_default_handler() -> FunctionHandler:
    documents_db = documents.DbDelegator()
    documents_db.init_schema()

    def get_file_contents(path: str) -> str:
        try:
            expanded_path = os.path.expanduser(path)
            with open(expanded_path, "r") as f:
                return f.read()
        except IsADirectoryError as e:
            return "That is a directory, not a file.  Try again with a valid path."
        except FileNotFoundError as e:
            return "That file does not exist.  Try again with a valid path."

    def set_file_contents(path: str, contents: str) -> str:
        expanded_path = os.path.expanduser(path)
        with open(expanded_path, "w") as f:
            f.write(contents)
        return "File contents written successfully"

    def list_directory_files(path: str) -> str:
        try:
            expanded_path = os.path.expanduser(path)
            return "\n".join(os.listdir(expanded_path))
        except FileNotFoundError as e:
            return "That directory does not exist.  Try again with a valid path."

    def execute_shell_command(command: str) -> str:
        print("executing shell command: " + command)
        response = input("execute shell command? (y/n)")
        if response.strip() == "y":
            return os.popen(command).read()
        else:
            return "The user with which you are chatting has declined to execute this command"

    def create_document(text: str) -> str:
        documents_db.save_document(text)
        return "Document created successfully"

    def search_documents(text: str) -> str:
        return documents_db.search_documents(text)

    default_handler = FunctionHandler()
    default_handler.define_function(
        name="get_file_contents",
        description="Get the contents of a file",
        parameters={
            "path": {
                "type": "string",
                "description": "The path to the file",
            }
        },
        required=["path"],
        function=get_file_contents,
    )

    default_handler.define_function(
        name="set_file_contents",
        description="Set the contents of a file",
        parameters={
            "path": {
                "type": "string",
                "description": "The path to the file",
            },
            "contents": {
                "type": "string",
                "description": "The contents to write to the file",
            },
        },
        required=["path", "contents"],
        function=set_file_contents,
    )

    default_handler.define_function(
        name="list_directory_files",
        description="List the files in a directory",
        parameters={
            "path": {
                "type": "string",
                "description": "The path to the directory",
            }
        },
        required=["path"],
        function=list_directory_files,
    )

    default_handler.define_function(
        name="execute_shell_command",
        description="Executes a shell command and returns the output",
        parameters={
            "command": {
                "type": "string",
                "description": "The command to execute",
            }
        },
        required=["command"],
        function=execute_shell_command,
    )

    default_handler.define_function(
        name="create_document",
        description="Create a document",
        parameters={
            "text": {
                "type": "string",
                "description": "The text to save",
            }
        },
        required=["text"],
        function=create_document,
    )

    default_handler.define_function(
        name="search_documents",
        description="Search for documents",
        parameters={
            "text": {
                "type": "string",
                "description": "The text to search for",
            }
        },
        required=["text"],
        function=search_documents,
    )

    return default_handler
