#!/usr/bin/env python3
"""
PluginManager: dynamic loading of plugins/adapters from plugins/ directory.
"""
from __future__ import annotations
import os
import sys
import importlib.util
from typing import Dict, Any, List, Optional
from pathlib import Path

class PluginManager:
    def __init__(self, plugins_dir: str = "plugins"):
        self.dir = Path(plugins_dir)
        self.dir.mkdir(exist_ok=True)
        self.loaded: Dict[str, Any] = {}

    def discover(self) -> List[str]:
        if not self.dir.exists():
            return []
        return [p.stem for p in self.dir.glob("*.py") if p.stem != '__init__']

    def load(self, name: str) -> Optional[Any]:
        if name in self.loaded:
            return self.loaded[name]
        path = self.dir / f"{name}.py"
        if not path.exists():
            return None
        try:
            spec = importlib.util.spec_from_file_location(name, str(path))
            if not spec or not spec.loader:
                return None
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            self.loaded[name] = module
            return module
        except Exception:
            return None

    def call(self, name: str, func: str, *args, **kwargs) -> Any:
        mod = self.load(name)
        if not mod:
            raise ValueError(f"Plugin {name} not found")
        fn = getattr(mod, func, None)
        if not fn:
            raise ValueError(f"Function {func} not found in {name}")
        return fn(*args, **kwargs)
