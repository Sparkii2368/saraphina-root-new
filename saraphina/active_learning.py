#!/usr/bin/env python3
"""
Active Learning: generates clarifying questions when confidence is low.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
import re

class ActiveLearner:
    def __init__(self, conn):
        self.conn = conn

    @staticmethod
    def needs_clarification(response: str, confidence: float) -> bool:
        # Heuristics: low confidence or vague language
        if confidence < 0.5:
            return True
        vague = ['maybe', 'possibly', 'unclear', 'not sure', 'depends']
        return any(v in response.lower() for v in vague)

    @staticmethod
    def generate_question(user_query: str, response: str) -> str:
        # Extract key entities/concepts
        words = re.findall(r"[A-Z][a-z]+|[a-z]{4,}", user_query)
        key = words[0] if words else "that"
        templates = [
            f"Can you clarify what you mean by '{key}'?",
            f"Are you asking about {key} in a specific context?",
            "Could you provide more details or an example?",
            "Is this related to a particular use case?",
        ]
        import random
        return random.choice(templates)

    def record_qa(self, question: str, answer: str) -> None:
        # Store clarifying Q&A for future training
        try:
            from uuid import uuid4
            from datetime import datetime
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO learning_journal (id, timestamp, query, response, strategy, success, notes, metrics) VALUES (?,?,?,?,?,?,?,?)",
                (str(uuid4()), datetime.utcnow().isoformat(), question, answer, 'active_learning', 1.0, 'clarification', '{}')
            )
            self.conn.commit()
        except Exception:
            pass
