import sys
from pathlib import Path
from shutil import copy2
from stat import S_IXUSR, S_IXGRP, S_IXOTH

repo_root = Path(__file__).parent
hooks_dir = repo_root/'.git/hooks'

# Check if we're in a git repository
if not hooks_dir.exists():
    print("Error: .git/hooks directory not found.")
    sys.exit(1)

# Hook mappings: (source_file, target_hook_name)
hooks = {
    hooks_dir/'pre-commit': repo_root/'update_version.sh',
}

print("Setting up git hooks...")

for hook, script in hooks.items():
    if not script.exists():
        print(f"Source hook not found: {script}")
        continue

    # Copy the hook
    copy2(script, hook)
    current_mode = hook.stat().st_mode
    hook.chmod(current_mode | S_IXUSR | S_IXGRP | S_IXOTH)
    print(f"Installed: {hook.name}")

print("\nGit hooks setup complete!")
