"""
Provides postgres vector-db based document persistence and search
"""

import os
import sys

import psycopg2

import llmtool.genai.embedding as embedding

class DbDelegator:
    def __init__(self):
        try:
            self.db = DB()
        except psycopg2.OperationalError:
            print("Failed to connect to database, documents disabled.", file=sys.stderr)
            self.db = DBStub()

    def init_schema(self):
        self.db.init_schema()

    def save_document(self, text: str):
        self.db.save_document(text)

    def search_documents(self, search_str: str) -> str:
        return self.db.search_documents(search_str)

class DBStub:
    def __init__(self):
        pass

    def init_schema(self):
        pass

    def save_document(self, text: str):
        pass

    def search_documents(self, search_str: str) -> str:
        return ""

class DB:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname="genai_documents",
            user="genai",
        )

    def init_schema(self):
        cur = self.conn.cursor()
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                text TEXT,
                embedding VECTOR({embedding.VECTOR_SIZE})
            );

            CREATE INDEX IF NOT EXISTS documents_embedding_idx ON documents
            USING ivfflat(embedding vector_l2_ops);
        """
        )
        self.conn.commit()
        cur.close()

    def save_document(self, text: str):
        cur = self.conn.cursor()
        cur.execute(
            """
        INSERT INTO documents (text, embedding)
        VALUES (%s, %s)
        """,
            (text, embedding.generate(text)),
        )
        self.conn.commit()
        cur.close()

    def search_documents(self, search_str: str) -> str:
        cur = self.conn.cursor()

        query_embedding = embedding.generate(search_str)

        query = """
        SELECT id, text
        FROM documents
        ORDER BY embedding <-> %s::vector
        LIMIT 10
        """
        cur.execute(query, (query_embedding,))
        rows = cur.fetchall()
        return "\n".join([f"Document ID: {row[0]}\n{row[1]}\n\n" for row in rows])
