import sys
from pathlib import Path
from re import compile, match, MULTILINE

from pyrandyos.utils.json import parse_jsonc


DECORATOR = '@log_func_call'

DECORATOR_RE = compile(r'^[ \t]*@[_]?log_func_call(\s*\(.*\))?\s*$',
                       flags=MULTILINE)
CONFIG_FILENAME = ".log_func_call_exclude.jsonc"


def load_exclude_config(config_path):
    config_path = Path(config_path)
    if not config_path.exists():
        return {
            "exclude_files": [],
            "exclude_classes": [],
            "exclude_methods": {},
            "exclude_dirs": [],
            "base_dir": None
        }
    with open(config_path, "r", encoding="utf-8") as f:
        return parse_jsonc(f.read())


def should_skip_dir(path: Path, exclude_dirs, base_path: Path) -> bool:
    """
    Check if a directory should be skipped based on exclude patterns.

    Patterns starting with '/' are treated as explicit paths from base_path.
    Patterns without '/' match any directory with that name.

    Examples:
        'cache' -> matches any directory named 'cache' at any level
        '/cache' -> matches only base_path/cache
        '/pyrandyos/utils/time' -> matches only base_path/pyrandyos/utils/time
    """
    try:
        rel_path = path.resolve().relative_to(base_path.resolve())
        rel_path_str = str(rel_path).replace('\\', '/')
    except ValueError:
        # path is not relative to base_path
        return False

    for pattern in exclude_dirs:
        if pattern.startswith('/'):
            # Explicit path pattern - match from base_path
            explicit_pattern = pattern[1:]  # Remove leading /
            if (rel_path_str == explicit_pattern
                    or rel_path_str.startswith(explicit_pattern + '/')):
                return True
        else:
            # Simple name pattern - match any directory with this name
            if pattern in path.parts:
                return True

    return False


def is_property_decorator(line):
    stripped = line.strip()
    return (
        stripped == '@property'
        or stripped.endswith('.setter')
        or stripped.endswith('.deleter')
    )


def file_needs_decorator_legacy(filepath: Path, exclude_file_paths,
                                exclude_classes, exclude_methods, exclude_dirs,
                                should_skip_dir):
    """Legacy version - not used anymore"""
    content = filepath.read_text(encoding='utf-8')
    lines = content.splitlines()
    new_lines = []
    i = 0
    changed = False
    scope_stack = []
    while i < len(lines):
        line = lines[i]
        indent = len(line) - len(line.lstrip())

        # Pop scopes if indentation decreases (ignore blank lines)
        while scope_stack and line.strip() and indent <= scope_stack[-1][2]:
            scope_stack.pop()

        # Enter TYPE_CHECKING block
        type_checking_match = match(r'^([ \t]*)if TYPE_CHECKING:', line)
        if type_checking_match:
            scope_stack.append(('type_checking', None, indent))

        # Enter class
        class_match = match(r'^([ \t]*)class ([a-zA-Z0-9_]+)', line)
        if class_match:
            class_name = class_match.group(2)
            scope_stack.append(('class', class_name, indent))

        # Check if inside TYPE_CHECKING
        inside_type_checking = any(
            s[0] == 'type_checking' for s in scope_stack
        )

        # Check if inside excluded class
        inside_excluded_class = False
        current_class = None
        for s in reversed(scope_stack):
            if s[0] == 'class':
                current_class = s[1]
                if current_class in exclude_classes:
                    inside_excluded_class = True
                break

        # Exclude specific methods
        func_match = match(r'^[ \t]*def ([a-zA-Z0-9_]+)', line)
        if func_match:
            method_name = func_match.group(1)
            if (current_class and current_class in exclude_methods and
                    method_name in exclude_methods[current_class]):
                new_lines.append(line)
                i += 1
                new_lines.append("")
                continue

        # Exclude functions in excluded classes or TYPE_CHECKING
        if match(r'^[ \t]*def [a-zA-Z0-9_]+', line):
            if inside_excluded_class or inside_type_checking:
                new_lines.append(line)
                i += 1
                new_lines.append("")
                continue

            # Scan upwards for decorators
            j = len(new_lines) - 1
            has_decorator = False
            is_property = False
            while j >= 0 and (new_lines[j].strip() == ''
                              or new_lines[j].lstrip().startswith('@')):
                if DECORATOR_RE.match(new_lines[j]):
                    has_decorator = True
                if is_property_decorator(new_lines[j]):
                    is_property = True
                j -= 1

            if not has_decorator and not is_property:
                indent_str = match(r'^([ \t]*)', line).group(1)
                new_lines.append(f'{indent_str}{DECORATOR}')
                changed = True

        new_lines.append(line)
        i += 1

    if changed:
        filepath.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
        print(f'Updated: {filepath}')


def main(root_dirs, config_path=None):
    script_path = Path(__file__).resolve()

    if config_path:
        config = load_exclude_config(config_path)
        base_path = config.get("base_dir")
        if base_path:
            base_path = Path(base_path).resolve()
            root_dirs = [str(base_path)]  # Use base_dir as only search root
        else:
            base_path = Path.cwd().resolve()
        configs = [config]
    else:
        configs = []
        base_path = Path.cwd().resolve()
        for root_dir in root_dirs:
            config = load_exclude_config(Path(root_dir) / CONFIG_FILENAME)
            configs.append(config)

    exclude_files = set()
    exclude_classes = set()
    exclude_methods = dict()
    exclude_dirs = set()
    exclude_functions_by_file = dict()

    for config in configs:
        exclude_files.update(config.get("exclude_files", []))
        exclude_classes.update(config.get("exclude_classes", []))
        exclude_dirs.update(config.get("exclude_dirs", []))
        # exclude_functions is now a dict: {filename: [func1, func2, ...]}
        ef = config.get("exclude_functions", {})
        for fname, funclist in ef.items():
            if fname not in exclude_functions_by_file:
                exclude_functions_by_file[fname] = set()
            exclude_functions_by_file[fname].update(funclist)

        for cls, methods in config.get("exclude_methods", {}).items():
            if cls not in exclude_methods:
                exclude_methods[cls] = set()
            exclude_methods[cls].update(methods)

    exclude_file_paths = set()
    for p in exclude_files:
        path_obj = Path(p)
        if not path_obj.is_absolute():
            path_obj = (base_path / path_obj).resolve()
        exclude_file_paths.add(str(path_obj))

    def should_skip_dir_closure(path: Path) -> bool:
        return should_skip_dir(path, exclude_dirs, base_path)

    def file_needs_decorator(filepath: Path):
        content = filepath.read_text(encoding='utf-8')
        lines = content.splitlines()
        new_lines = []
        i = 0
        changed = False
        scope_stack = []
        # Compute relative path from base_dir for this file
        rel_path = str(filepath.resolve().relative_to(base_path))
        rel_path = rel_path.replace('\\', '/').replace('\\', '/')
        exclude_funcs_for_file = exclude_functions_by_file.get(rel_path, set())

        while i < len(lines):
            line = lines[i]
            indent = len(line) - len(line.lstrip())

            # Pop scopes if indentation decreases (ignore blank lines)
            while (scope_stack and line.strip()
                   and indent <= scope_stack[-1][2]):
                scope_stack.pop()

            # Enter TYPE_CHECKING block
            type_checking_match = match(r'^([ \t]*)if TYPE_CHECKING:', line)
            if type_checking_match:
                scope_stack.append(('type_checking', None, indent))

            # Enter class
            class_match = match(r'^([ \t]*)class ([a-zA-Z0-9_]+)', line)
            if class_match:
                class_name = class_match.group(2)
                scope_stack.append(('class', class_name, indent))

            # Check if inside TYPE_CHECKING
            inside_type_checking = any(
                s[0] == 'type_checking' for s in scope_stack
            )

            # Check if inside excluded class
            inside_excluded_class = False
            current_class = None
            for s in reversed(scope_stack):
                if s[0] == 'class':
                    current_class = s[1]
                    if current_class in exclude_classes:
                        inside_excluded_class = True
                    break

            # Exclude specific methods or module-level functions
            func_match = match(r'^[ \t]*def ([a-zA-Z0-9_]+)', line)
            if func_match:
                method_name = func_match.group(1)
                if current_class:
                    if (current_class in exclude_methods and
                            method_name in exclude_methods[current_class]):
                        new_lines.append(line)
                        i += 1
                        new_lines.append("")
                        continue
                else:
                    # module-level function
                    if method_name in exclude_funcs_for_file:
                        new_lines.append(line)
                        i += 1
                        new_lines.append("")
                        continue

            # Exclude functions in excluded classes or TYPE_CHECKING
            if match(r'^[ \t]*def [a-zA-Z0-9_]+', line):
                if inside_excluded_class or inside_type_checking:
                    new_lines.append(line)
                    i += 1
                    new_lines.append("")
                    continue

                # Scan upwards for decorators
                j = len(new_lines) - 1
                has_decorator = False
                is_property = False
                while j >= 0 and (new_lines[j].strip() == ''
                                  or new_lines[j].lstrip().startswith('@')):
                    if DECORATOR_RE.match(new_lines[j]):
                        has_decorator = True
                    if is_property_decorator(new_lines[j]):
                        is_property = True
                    j -= 1
                if not has_decorator and not is_property:
                    indent_str = match(r'^([ \t]*)', line).group(1)
                    new_lines.append(f'{indent_str}{DECORATOR}')
                    changed = True
            new_lines.append(line)
            i += 1
        if changed:
            filepath.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
            print(f'Updated: {filepath}')

    for root_dir in root_dirs:
        for pyfile in Path(root_dir).rglob('*.py'):
            resolved_pyfile = pyfile.resolve()

            if resolved_pyfile == script_path:
                continue

            if (
                pyfile.name in exclude_files
                or str(resolved_pyfile) in exclude_file_paths
            ):
                continue

            if should_skip_dir_closure(pyfile):
                continue

            file_needs_decorator(pyfile)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        main(['.'], config_path=config_path)
    else:
        main(['.'])
