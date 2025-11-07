#!/usr/bin/env python3
"""
SystemAdapter - abstract interface for system operations + NoOpAdapter example
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class SystemAdapter(ABC):
    @abstractmethod
    def discover(self) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    def dryrun(self, action_descriptor: Dict[str, Any]) -> List[str]:
        ...

    @abstractmethod
    def execute(self, action_descriptor: Dict[str, Any]) -> Dict[str, Any]:
        ...

    @abstractmethod
    def revert(self, action_id: str) -> Dict[str, Any]:
        ...

class NoOpAdapter(SystemAdapter):
    def discover(self) -> List[Dict[str, Any]]:
        return [{"id": "noop:local", "capabilities": ["dryrun", "execute", "revert"]}]

    def dryrun(self, action_descriptor: Dict[str, Any]) -> List[str]:
        return [f"NOOP would perform: {action_descriptor.get('action','unknown')}"]

    def execute(self, action_descriptor: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ok", "action_id": "noop-1", "details": action_descriptor}

    def revert(self, action_id: str) -> Dict[str, Any]:
        return {"status": "reverted", "action_id": action_id}
