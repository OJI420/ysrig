import importlib
import sys
import os
import types

def main(mod: types.ModuleType):
    mod_name = mod.__name__
    mod_path = os.path.dirname(mod.__file__)

    importlib.reload(mod)

    for file in os.listdir(mod_path):
        if file.endswith(".py") and not file.startswith("__"):
            submod_name = f"{mod_name}.{file[:-3]}"
            if submod_name in sys.modules:
                importlib.reload(sys.modules[submod_name])