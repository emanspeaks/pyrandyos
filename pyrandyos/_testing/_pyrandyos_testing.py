from os import environ

# these constants are only relevant to testing, do not add to constants
ENV_CI_RUNNING = 'CI'
ENV_PYRANDYOS_UNITTEST_ACTIVE = 'PYRANDYOS_UNITTEST_ACTIVE'


def _is_pyrandyos_unittest():
    return bool(environ.get(ENV_PYRANDYOS_UNITTEST_ACTIVE))


def _is_running_in_ci():
    return bool(environ.get(ENV_CI_RUNNING))
