
# RETFound/__init__.py
from importlib import import_module as _imp

import models_vit
import engine_finetune
import main_finetune

_modules = [
    "models_vit",
    "engine_finetune",
    "main_finetune",
    # add any other root-level .py you want to expose
]
for _m in _modules:
    globals()[_m] = _imp(_m)

__all__ = _modules
