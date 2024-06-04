import openai
import tiktoken

from typing import Sequence

VECTOR_SIZE = 1536
MAX_TOKENS = 8191
MODEL = "text-embedding-ada-002"
TOKENIZER = "cl100k_base"


def generate(text: str) -> Sequence[float]:
    """
    generates openai embeddings from text
    """

    def truncate(text: str) -> str:
        encoding = tiktoken.get_encoding(TOKENIZER)
        tokens = encoding.encode(text)
        truncated_tokens = tokens[:MAX_TOKENS]
        return encoding.decode(truncated_tokens)

    response = openai.Embedding.create(
        model=MODEL,
        input=truncate(text),
    )

    return response["data"][0]["embedding"]
