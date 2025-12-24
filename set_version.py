import re
import os

NEW_VERSION = "2.4.0"

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

def set_version_in_file(file_path, new_version):
    pattern = re.compile(
        r"^(\s*VERSION\s*=\s*)[\"'](.*?)[\"']",
        re.MULTILINE
    )
    replacement_line = rf'\g<1>"{new_version}"'

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content, count = pattern.subn(replacement_line, content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def set_version_in_mod_file(file_path, module_name, new_version):
    pattern_str = r"^(\+\s+{}\s+)([\d\w\.-]+)(\s+.*)".format(re.escape(module_name))
    pattern = re.compile(
        pattern_str,
        re.MULTILINE | re.IGNORECASE
    )
    replacement_line = rf"\g<1>{new_version}\g<3>"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content, count = pattern.subn(replacement_line, content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

if __name__ == "__main__":
    FILES_TO_UPDATE = [
        os.path.join(THIS_DIR, "drag_and_drop.py"),
        os.path.join(THIS_DIR, "modules", "YSRig", "plug-ins", "ysrig_plugin.py"),
        os.path.join(THIS_DIR, "modules", "YSRig", "scripts", "ysrig", "core.py"),
    ]

    MOD_FILES_TO_UPDATE = "modules/YSRig.mod"

    for py_file in FILES_TO_UPDATE:
        set_version_in_file(py_file, NEW_VERSION)

    set_version_in_mod_file(MOD_FILES_TO_UPDATE, "ysrig", NEW_VERSION)