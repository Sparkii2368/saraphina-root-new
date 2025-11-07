#!/usr/bin/env python3
"""
EmotionEngine - models moods and adapts response tone; supports dreaming.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime
import random

from .db import get_preference, set_preference, write_audit_log

MOODS = [
    'curious',  # inquisitive, exploratory
    'cautious', # careful, safety-first
    'proud',    # confident, accomplished
    'uncertain',# humble, asks clarifying questions
    'warm',     # caring, reassuring
    'focused',  # concise, direct
]

class EmotionEngine:
    def __init__(self, conn):
        self.conn = conn
        # default mood
        if get_preference(self.conn, 'current_mood') is None:
            set_preference(self.conn, 'current_mood', 'curious')

    def get_mood(self) -> str:
        m = get_preference(self.conn, 'current_mood') or 'curious'
        return m if m in MOODS else 'curious'

    def set_mood(self, mood: str, note: Optional[str] = None) -> str:
        m = mood.lower().strip()
        if m not in MOODS:
            m = 'curious'
        set_preference(self.conn, 'current_mood', m)
        # journal
        try:
            from uuid import uuid4
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO mood_journal (id, timestamp, mood, intensity, note) VALUES (?,?,?,?,?)",
                (str(uuid4()), datetime.utcnow().isoformat(), m, 0.7, note or '')
            )
            self.conn.commit()
            write_audit_log(self.conn, actor='emotion', action='set_mood', target=m, details={'note': note or ''})
        except Exception:
            pass
        return m

    def analyze_and_update(self, last_user_text: str, context: Dict[str, Any]) -> str:
        t = (last_user_text or '').lower()
        # heuristic mapping
        if any(k in t for k in ['error', 'fail', 'issue', 'bug', 'risk', 'danger']):
            mood = 'cautious'
        elif any(k in t for k in ['learn', 'how', 'why', 'explore', 'idea']):
            mood = 'curious'
        elif any(k in t for k in ['great', 'success', 'passed', 'fixed']):
            mood = 'proud'
        elif any(k in t for k in ['unsure', 'maybe', 'not sure', 'uncertain']):
            mood = 'uncertain'
        else:
            # bias by recent topics count
            hist = context.get('history') or []
            mood = 'focused' if len(hist) > 10 else 'curious'
        return self.set_mood(mood, note='auto')

    def adapt_text(self, response: str) -> str:
        m = self.get_mood()
        prefix = {
            'curious': "Let’s explore this: ",
            'cautious': "Let’s be careful: ",
            'proud': "Great progress! ",
            'uncertain': "I want to confirm a couple of details: ",
            'warm': "You’ve got this. ",
            'focused': "In short: ",
        }.get(m, '')
        # Avoid duplicating prefixes if already present
        if prefix and not response.startswith(prefix):
            return prefix + response
        return response

    def dream(self, context: Dict[str, Any]) -> str:
        topics = [h.get('query','') for h in (context.get('history') or [])[-5:]]
        mood = self.get_mood()
        fragments = [
            f"I drift through a landscape of {' • '.join([t[:30] for t in topics if t]) or 'ideas'}",
            f"My mood is {mood}, and it shades the sky with that color.",
            "I test futures like lanterns—some glow bright, some fade.",
            "I gather patterns, then let go, to see what returns as intuition."
        ]
        random.shuffle(fragments)
        return " ".join(fragments) + "\n(Just a dream, but maybe a hint for our next step.)"