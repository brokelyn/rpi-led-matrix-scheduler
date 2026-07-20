"""Shared read/write access to modules.conf.

Used by the scheduler (reads the file and applies it) and by the web
interface (writes it). The file is the only communication channel
between the two processes, so writes are atomic: a reader can never
see a half-written file.
"""
import configparser
import os
import tempfile

SECTION = 'modules'


def _parser():
    parser = configparser.ConfigParser()
    parser.optionxform = str  # keep CamelCase module names as-is
    return parser


def read(path):
    parser = _parser()
    with open(path) as f:
        parser.read_file(f)
    if not parser.has_section(SECTION):
        return {}
    return {name: parser.getboolean(SECTION, name)
            for name in parser.options(SECTION)}


def write(path, modules):
    parser = _parser()
    parser.add_section(SECTION)
    for name in sorted(modules):
        parser.set(SECTION, name, 'on' if modules[name] else 'off')

    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, prefix='.modules.conf.')
    try:
        with os.fdopen(fd, 'w') as f:
            parser.write(f)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def ensure(path, names):
    """Return the config with every given module present, defaulting new
    (or all, if the file is missing/corrupt) modules to enabled."""
    try:
        modules = read(path)
    except (OSError, ValueError, configparser.Error):
        modules = {}

    missing = [name for name in names if name not in modules]
    for name in missing:
        modules[name] = True
    if missing or not os.path.exists(path):
        write(path, modules)
    return modules
