
# RETFound/__init__.py
from importlib import import_module
import sys

import models_vit
import engine_finetune
import main_finetune

_modules = [
    "models_vit",
    "engine_finetune",
    "main_finetune",
    # add any other root-level .py you want to expose
]

for name in _modules:
    mod = import_module(name)                    # load the root-level module
    globals()[name] = mod                        # make it available as RETFound.<name>
    sys.modules[f"{__name__}.{name}"] = mod      # <-- critical: register as a submodule

__all__ = _modules
