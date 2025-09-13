import sys


args = sys.argv[1:]
if args[0] == 'log_func_call':
    from .tools.add_log_func_call_decorators import main as main_log_func_call
    if len(args) > 1:
        config_path = args[1]
        main_log_func_call(['.'], config_path=config_path)
    else:
        main_log_func_call(['.'])

else:
    raise ValueError(f"Unknown command: {args[0]}")
