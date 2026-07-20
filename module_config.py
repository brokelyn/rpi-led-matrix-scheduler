"""Shared read/write access to modules.conf.

Used by the scheduler (reads the file and applies it) and by the web
interface (writes it). The file is the only communication channel
between the two processes, so writes are atomic: a reader can never
see a half-written file.

Format: the [modules] section holds one `Name = on/off` line per module;
every module that declares OPTIONS additionally gets its own [Name]
section with one `key = value` line per option. Unknown keys are dropped
the next time the scheduler rewrites the file.
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
    """-> (enabled: {name: bool}, options: {module: {key: float}})"""
    parser = _parser()
    with open(path) as f:
        parser.read_file(f)

    enabled = {}
    if parser.has_section(SECTION):
        enabled = {name: parser.getboolean(SECTION, name)
                   for name in parser.options(SECTION)}

    options = {}
    for section in parser.sections():
        if section == SECTION:
            continue
        options[section] = {key: parser.getfloat(section, key)
                            for key in parser.options(section)}
    return enabled, options


def write(path, enabled, options):
    parser = _parser()
    parser.add_section(SECTION)
    for name in sorted(enabled):
        parser.set(SECTION, name, 'on' if enabled[name] else 'off')

    for module in sorted(options):
        if not options[module]:
            continue
        parser.add_section(module)
        for key, value in options[module].items():
            parser.set(module, key, format_value(value))

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


def format_value(value):
    value = float(value)
    return '%g' % value


def merge_options(spec, values):
    """Clamp the given values against an OPTIONS spec, falling back to
    defaults for missing/invalid entries. Keeps the spec's key order."""
    merged = {}
    for key, meta in spec.items():
        try:
            value = float(values.get(key, meta['default']))
        except (TypeError, ValueError):
            value = meta['default']
        merged[key] = min(meta['max'], max(meta['min'], value))
    return merged


def ensure(path, specs):
    """Bring the file in line with the discovered modules and their OPTIONS
    specs ({name: spec-dict}): add missing modules as enabled, merge/clamp
    all option values. -> (enabled, options)"""
    try:
        enabled, options = read(path)
    except (OSError, ValueError, configparser.Error):
        enabled, options = {}, {}

    changed = False
    for name, spec in specs.items():
        if name not in enabled:
            enabled[name] = True
            changed = True
        merged = merge_options(spec, options.get(name, {}))
        if merged != options.get(name, {}):
            changed = True
        options[name] = merged

    if changed or not os.path.exists(path):
        write(path, enabled, options)
    return enabled, options
