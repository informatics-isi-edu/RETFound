from importlib import import_module as _imp

# Lazily import to avoid side effects at install time
datasets = _imp("..utils.datasets")
lr_decay = _imp("..utils.lr_decay")
lr_sched = _imp("..utils.lr_sched")
misc = _imp("..utils.misc")
pos_embed = _imp("..utils.pos_embed")

__all__ = ["datasets", "lr_decay", "lr_sched", "misc", "pos_embed",]
