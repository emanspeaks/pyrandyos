from pathlib import Path
from re import compile, match, MULTILINE

DECORATOR = '@log_func_call'

DECORATOR_RE = compile(r'^[ \t]*@[_]?log_func_call(\s*\(.*\))?\s*$',
                       flags=MULTILINE)
EXCLUDE_DIRS = {'__pycache__', '_testing', '.git', '.venv', 'venv', 'env',
                '.conda', 'tests'}

EXCLUDE_FILES = {
    'add_log_func_call_decorators.py',
    'pyapp/config/defaults.py',
    'pyapp/config/keys.py',
    'pyapp/qt_gui/icons/qiconfont/update_from_spec.py',
    'pyapp/qt_gui/notify.py',
    'pyapp/utils/classproperty.py',
    'pyapp/utils/stack.py',
    'pyapp/logging.py',
}

EXCLUDE_CLASSES = {
    # Add class names (as strings) to exclude from decoration
    'MillisecondFormatter',
    'LevelFilter',
}

EXCLUDE_METHODS = {
    # Example:
    # 'ClassName': {'method_name1', 'method_name2'},
    'FileSetTqdm': {'__iter__'},
}

# Pre-resolve all exclude files to absolute paths
EXCLUDE_FILE_PATHS = set()
for p in EXCLUDE_FILES:
    path_obj = Path(p)
    if not path_obj.is_absolute():
        path_obj = (Path.cwd() / path_obj).resolve()
    EXCLUDE_FILE_PATHS.add(str(path_obj))


def should_skip_dir(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def is_property_decorator(line):
    stripped = line.strip()
    return (
        stripped == '@property'
        or stripped.endswith('.setter')
        or stripped.endswith('.deleter')
    )


def file_needs_decorator(filepath: Path):
    content = filepath.read_text(encoding='utf-8')
    lines = content.splitlines()
    new_lines = []
    i = 0
    changed = False
    inside_excluded_class = False
    excluded_class_indent = None
    inside_type_checking = False
    type_checking_indent = None
    current_class = None
    class_indent = None
    while i < len(lines):
        line = lines[i]
        # Detect entering TYPE_CHECKING block
        type_checking_match = match(r'^([ \t]*)if TYPE_CHECKING:', line)
        if type_checking_match:
            inside_type_checking = True
            type_checking_indent = len(
                type_checking_match.group(1).replace('\t', '    ')
            )
        # Detect leaving TYPE_CHECKING block
        if (inside_type_checking and line.strip()
                and not line.lstrip().startswith('#')):
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= (type_checking_indent or 0):
                inside_type_checking = False
                type_checking_indent = None
        # Detect class definition
        class_match = match(r'^([ \t]*)class ([a-zA-Z0-9_]+)', line)
        if class_match:
            class_indent = len(class_match.group(1).replace('\t', '    '))
            current_class = class_match.group(2)
            if current_class in EXCLUDE_CLASSES:
                inside_excluded_class = True
                excluded_class_indent = class_indent
            else:
                inside_excluded_class = False
                excluded_class_indent = None
        # Detect leaving class by indentation
        if (current_class and line.strip()
                and not line.lstrip().startswith('@')):
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= (class_indent or 0):
                current_class = None
                class_indent = None
        # Detect leaving excluded class by indentation
        if (inside_excluded_class and line.strip()
                and not line.lstrip().startswith('@')):
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= (excluded_class_indent or 0):
                inside_excluded_class = False
                excluded_class_indent = None
        func_match = match(r'^[ \t]*def ([a-zA-Z0-9_]+)', line)
        if func_match:
            method_name = func_match.group(1)
            if (current_class and current_class in EXCLUDE_METHODS and
                    method_name in EXCLUDE_METHODS[current_class]):
                new_lines.append(line)
                i += 1
                continue
        if match(r'^[ \t]*def [a-zA-Z0-9_]+', line):
            if inside_excluded_class or inside_type_checking:
                new_lines.append(line)
                i += 1
                continue
            j = i - 1
            has_decorator = False
            is_property = False
            # Scan upwards for decorators
            while (j >= 0 and (lines[j].strip() == ''
                               or lines[j].lstrip().startswith('@'))):
                if DECORATOR_RE.match(lines[j]):
                    has_decorator = True
                if is_property_decorator(lines[j]):
                    is_property = True
                j -= 1
            if not has_decorator and not is_property:
                indent = match(r'^([ \t]*)', line).group(1)
                new_lines.append(f'{indent}{DECORATOR}')
                changed = True
        new_lines.append(line)
        i += 1
    if changed:
        filepath.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
        print(f'Updated: {filepath}')


def main(root_dirs):
    script_path = Path(__file__).resolve()
    for root_dir in root_dirs:
        for pyfile in Path(root_dir).rglob('*.py'):
            resolved_pyfile = pyfile.resolve()
            if resolved_pyfile == script_path:
                continue
            if (
                pyfile.name in EXCLUDE_FILES
                or str(resolved_pyfile) in EXCLUDE_FILE_PATHS
            ):
                continue
            if any(part in EXCLUDE_DIRS for part in pyfile.parts):
                continue
            file_needs_decorator(pyfile)


if __name__ == '__main__':
    # Edit these paths as needed
    main(['.', '../pyrig'])
