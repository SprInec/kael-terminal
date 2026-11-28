#!/usr/bin/env python3
"""Small Linux tmux status helper; standard library only, no background daemon."""
import colorsys
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import termios
import time
import unicodedata


def safe(text):
    # Shell arguments are quoted by tmux; output must not introduce tmux styles.
    return ''.join(c for c in str(text) if not unicodedata.category(c).startswith('C')).replace('#', '＃')


def width(text):
    return sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in text)


def trim(text, limit, tail=False):
    if width(text) <= limit:
        return text
    if limit <= 1:
        return '…'[:max(0, limit)]
    chars = reversed(text) if tail else iter(text)
    result = ''
    for char in chars:
        if width(result + char) > limit - 1:
            break
        result += char
    return '…' + result[::-1] if tail else result + '…'


def compact_path(directory, limit):
    """Shorten at directory boundaries before truncating the final component."""
    if width(directory) <= limit:
        return directory
    parts = directory.rstrip('/').split('/')
    tail = parts[-1] or '/'
    if width(tail) >= limit - 2:
        return trim(tail, limit)
    for parent in reversed(parts[:-1]):
        candidate = parent + '/' + tail
        if width('…/' + candidate) > limit:
            break
        tail = candidate
    return '…/' + tail


def sample_cpu():
    values = list(map(int, Path('/proc/stat').read_text().splitlines()[0].split()[1:9]))
    return sum(values), values[3] + values[4]


def cpu_usage():
    cache = Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache') / 'kael-terminal' / 'tmux'
    cache.mkdir(mode=0o700, parents=True, exist_ok=True)
    state = cache / 'cpu.json'
    try:
        previous = json.loads(state.read_text())
    except (ValueError, OSError):
        previous = None
    now = time.monotonic()
    if previous and 0 <= now - previous['time'] < 2:
        return previous['percent']
    total, idle = sample_cpu()
    if not previous or not 0 < now - previous['time'] < 120:
        previous = {'total': total, 'idle': idle}
        time.sleep(0.08)
        total, idle = sample_cpu()
    elapsed = total - previous['total']
    percent = max(0, min(100, round(100 * (1 - (idle - previous['idle']) / elapsed)))) if elapsed > 0 else 0
    # Atomic replacement tolerates concurrent clients without optional fcntl.
    temporary = cache / ('cpu-' + str(os.getpid()) + '.tmp')
    temporary.write_text(json.dumps({'time': now, 'total': total, 'idle': idle, 'percent': percent}))
    os.replace(temporary, state)
    return percent


def gpu_usage():
    """Return the highest reported NVIDIA GPU utilization, if available."""
    try:
        output = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
            text=True, encoding='utf-8', errors='replace', stderr=subprocess.DEVNULL, timeout=1,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    percentages = []
    for line in output.splitlines():
        try:
            percent = int(line)
        except ValueError:
            continue
        if 0 <= percent <= 100:
            percentages.append(percent)
    return max(percentages, default=None)


def memory_usage():
    info = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, value = line.split(':', 1)
        info[key] = int(value.split()[0])
    total = info['MemTotal']
    available = info.get('MemAvailable', info.get('MemFree', 0) + info.get('Buffers', 0) + info.get('Cached', 0))
    return max(0, min(100, round((total - available) * 100 / total)))


def git_metadata(path):
    for directory in (path, *path.parents):
        metadata = directory / '.git'
        if metadata.is_file():
            try:
                content = metadata.read_text().strip()
                if content.startswith('gitdir: '):
                    metadata = directory / content[8:]
            except OSError:
                continue
        if metadata.is_dir():
            return metadata
    return None


def git_status(path):
    metadata = git_metadata(path)
    if metadata is None:
        return '-', ''
    git = shutil.which('git')
    if git:
        try:
            proc = subprocess.run(
                [git, '--no-optional-locks', '-c', 'core.fsmonitor=false', '-C', str(path),
                 'status', '--porcelain=v2', '--branch', '--untracked-files=normal', '--ignore-submodules=dirty'],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                encoding='utf-8', errors='replace', timeout=1.2,
                env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
            if proc.returncode == 0:
                branch, oid, changes, ahead, behind = '', '', False, 0, 0
                for line in proc.stdout.splitlines():
                    if line.startswith('# branch.head '):
                        branch = line[14:]
                    elif line.startswith('# branch.oid '):
                        oid = line[13:8+13]
                    elif line.startswith('# branch.ab '):
                        a, b = line[12:].split()
                        ahead, behind = int(a), abs(int(b))
                    elif line.startswith(('1 ', '2 ', 'u ', '? ')):
                        changes = True
                if branch == '(detached)':
                    branch = '@' + oid
                suffix = '*' if changes else ''
                suffix += (' +' + str(ahead)) if ahead else ''
                suffix += (' -' + str(behind)) if behind else ''
                return safe(branch or '?'), suffix
        except (OSError, ValueError, subprocess.TimeoutExpired):
            pass
    # Firmware may lack git. Read HEAD, but mark working-tree state as unknown.
    try:
        head = (metadata / 'HEAD').read_text().strip()
        branch = head.removeprefix('ref: refs/heads/') if head.startswith('ref: refs/heads/') else '@' + head[:8]
        return safe(branch), '?'
    except OSError:
        return '?', ''


def cli_at_pid(pid):
    proc = Path('/proc') / str(pid)
    try:
        argv = (proc / 'cmdline').read_bytes().split(b'\0', 2)
        executable = Path(os.readlink(proc / 'exe')).name
    except OSError:
        return ''

    command = Path(os.fsdecode(argv[0])).name
    for name in ('codex', 'claude'):
        if executable in (name, name + '.exe') or command in (name, name + '.exe'):
            return name

    if executable in ('node', 'nodejs', 'bun') and len(argv) > 1:
        launcher = os.fsdecode(argv[1])
        for name, package in (('codex', '@openai/codex'), ('claude', '@anthropic-ai/claude-code')):
            if Path(launcher).name == name or f'/{package}/' in '/' + launcher:
                return name
    return ''


def pane_process_groups(pane_pid):
    # Skip the parenthesized command before reading the session ID and foreground PGID.
    fields = (Path('/proc') / str(pane_pid) / 'stat').read_bytes().rpartition(b')')[2].split()
    return int(fields[3]), int(fields[5])


def foreground_processes(pane_pid):
    session, foreground = pane_process_groups(pane_pid)
    if foreground <= 0:
        return
    yield foreground
    # Shell and package runners may lead the group while the application is a child.
    members = subprocess.check_output(
        ['/usr/bin/ps', '-s', str(session), '-o', 'pid=,pgid='],
        text=True, stderr=subprocess.DEVNULL, timeout=0.5,
    )
    for line in members.splitlines():
        pid, group = map(int, line.split())
        if group == foreground and pid != foreground:
            yield pid


def foreground_cli(pane_pid):
    try:
        for pid in foreground_processes(pane_pid):
            brand = cli_at_pid(pid)
            if brand:
                return brand
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        pass
    return ''


TRAINING_LAUNCHERS = {'torchrun', 'deepspeed'}
TRAINING_SCRIPTS = re.compile(r'(?:train(?:[_-].+)?|.+[_-]train|fine[_-]?tune(?:[_-].+)?)\.py')


def training_at_pid(pid):
    proc = Path('/proc') / str(pid)
    try:
        argv = [os.fsdecode(arg) for arg in (proc / 'cmdline').read_bytes().rstrip(b'\0').split(b'\0')]
        program = Path(argv[0]).name
        args = iter(argv[1:])
        if re.fullmatch(r'python(?:[0-9.]+)?', program):
            for arg in args:
                if arg == '-m':
                    return next(args, '') in ('torch.distributed.run', 'torch.distributed.launch', 'deepspeed.launcher.runner')
                if arg in ('-c', '-'):
                    return False
                if arg in ('-W', '-X'):
                    next(args, None)
                elif not arg.startswith('-'):
                    entry = Path(arg)
                    program = entry.name
                    if TRAINING_SCRIPTS.fullmatch(program):
                        return True
                    if program in ('evaluate.py', 'eval.py'):
                        return 'box_avoid' in (proc / 'cwd' / entry).resolve().parts
                    break
        if program in TRAINING_LAUNCHERS:
            return True
        if program == 'accelerate' and next(args, '') == 'launch':
            return any(TRAINING_SCRIPTS.fullmatch(Path(arg).name) for arg in args)
    except (OSError, ValueError, IndexError, RuntimeError):
        pass
    return False


def foreground_training(pane_pid):
    try:
        return any(training_at_pid(pid) for pid in foreground_processes(pane_pid))
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return False


def adb_shell_command(pid):
    argv = (Path('/proc') / str(pid) / 'cmdline').read_bytes().rstrip(b'\0').split(b'\0')
    args = iter(argv[1:])
    for arg in args:
        if arg in (b'-s', b'-t', b'-H', b'-P', b'-L'):
            next(args, None)
        elif arg in (b'-a', b'-d', b'-e', b'--exit-on-write-error') or arg.startswith(
            (b'-s', b'-t', b'-H', b'-P', b'wait-for-')
        ):
            continue
        else:
            return arg == b'shell'
    return False


def remote_terminal(pane_pid, tty, command):
    try:
        fd = os.open(tty, os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK)
        try:
            local_flags = termios.tcgetattr(fd)[3]
        finally:
            os.close(fd)
        # Interactive clients take over the local TTY in raw mode.
        if local_flags & (termios.ICANON | termios.ECHO | termios.ISIG):
            return False
        if command == 'adb':
            _, foreground = pane_process_groups(pane_pid)
            return foreground > 0 and adb_shell_command(foreground)
        return command in ('ssh', 'mosh-client', 'dbclient')
    except (OSError, termios.error, ValueError, IndexError):
        return False


def accent_palette(accent):
    rgb = bytes.fromhex(accent)
    backgrounds = []
    for tint in (0.09, 0.19, 0.28):
        background = bytes(round(19 + (channel - 19) * tint) for channel in rgb)
        backgrounds.append('#' + background.hex())
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
              for value in (channel / 255 for channel in rgb)]
    luminance = sum(weight * value for weight, value in zip((0.2126, 0.7152, 0.0722), linear))
    foreground = '#17210f' if luminance >= 0.22 else '#f4f4f4'
    return ' '.join([*backgrounds, foreground])


def right_colours(accent):
    # Icon labels, data, path and clock, clean Git, and separators.
    colours = ('#929e85', '#dce5d3', '#a5bb8b', '#b1e969', '#48533e')
    if not re.fullmatch(r'[0-9a-fA-F]{6}', accent) or accent.lower() == 'b1e969':
        return colours

    def to_hls(rgb):
        return colorsys.rgb_to_hls(*(channel / 255 for channel in bytes.fromhex(rgb)))

    local_hue, _, _ = to_hls('b1e969')
    focus_hue, _, focus_saturation = to_hls(accent)
    rotation = focus_hue - local_hue
    themed = []
    for colour in colours:
        hue, lightness, saturation = to_hls(colour[1:])
        rgb = colorsys.hls_to_rgb((hue + rotation) % 1, lightness, saturation if focus_saturation else 0)
        themed.append('#' + bytes(round(channel * 255) for channel in rgb).hex())
    return tuple(themed)


def render(path_string, columns, disk, session='', accent=''):
    path = Path(path_string).resolve()
    directory = str(path)
    home = str(Path.home())
    if directory == home or directory.startswith(home + '/'):
        directory = '~' + directory[len(home):]
    directory = safe(directory)
    branch, suffix = git_status(path)
    try:
        cpu = str(cpu_usage()) + '%'
    except (OSError, ValueError, KeyError):
        cpu = '?'
    try:
        memory = str(memory_usage()) + '%'
    except (OSError, ValueError, KeyError):
        memory = '?'
    try:
        usage = shutil.disk_usage(disk)
        disk_pct = str(round(usage.used * 100 / (usage.used + usage.free))) + '%'
    except (OSError, ZeroDivisionError):
        disk_pct = '?'
    # Budget for the session, an active prefix indicator and window list.
    session_limit = 6 if columns < 70 else 12
    budget = max(0, columns - min(session_limit, width(safe(session))) - 14 - max(12, columns // 5))
    muted, foreground, path_colour, clean, divider = right_colours(accent)
    amber, red = '#d7c183', '#e6a091'

    def segment(text, colour=foreground):
        return (text, f'#[fg={colour},nobold,noreverse]{text}#[default]')

    def resource(icon, label, value):
        colour = muted
        if value.endswith('%'):
            percent = int(value[:-1])
            colour = red if percent >= 90 else amber if percent >= 75 else foreground
        title = icon + ' ' + (label + ' ' if columns >= 160 else '')
        return (title + value,
                f'#[fg={muted},nobold]{title}#[fg={colour}]{value}#[default]')

    hostname = trim(safe(os.uname().nodename.split('.')[0]), 22)
    clock = time.strftime(' %m-%d   %H:%M' if columns >= 140 else ' %H:%M')
    clock_part = segment(clock + ' ', path_colour)
    optional = [('cpu', resource('', 'CPU', cpu)),
                ('memory', resource('', 'MEM', memory)),
                ('disk', resource('', 'DSK', disk_pct)),
                ('host', segment(' ' + hostname, muted))]
    gpu = gpu_usage()
    if gpu is not None:
        optional.insert(1, ('gpu', resource('󰢮', 'GPU', f'{gpu}%')))
    if columns >= 190:
        optional.insert(-1, ('load', segment(' ' + '%.2f' % os.getloadavg()[0], muted)))
    # Retain directory/Git first; progressively remove lower-priority telemetry.
    def ending_width():
        return sum(width(part[0]) + 3 for _, part in optional) + width(clock_part[0]) + 3

    for name in ('load', 'host', 'disk', 'memory', 'gpu', 'cpu'):
        if ending_width() + 32 <= budget:
            break
        optional = [(key, part) for key, part in optional if key != name]

    info_budget = max(0, budget - ending_width())
    parts = []
    git_part = None
    if branch != '-' and info_budget >= 14:
        state = suffix.replace('*', ' ●').replace(' +', ' ↑').replace(' -', ' ↓')
        if not suffix:
            state = ' ✓'
        branch_budget = min(28, max(8, (info_budget - 3) // 2))
        git_text = ' ' + trim(branch, max(1, branch_budget - 2 - width(state))) + state
        git_text = trim(git_text, branch_budget)
        git_part = segment(git_text, amber if suffix else clean)
        info_budget -= width(git_text) + 3
    if info_budget >= 4:
        parts.append(segment(' ' + compact_path(directory, info_budget - 2), path_colour))
    if git_part:
        parts.append(git_part)
    parts.extend(part for _, part in optional)
    parts.append(clock_part)
    separator = f'#[fg={divider},nobold] │ '
    result = separator.join(part[1] for part in parts)
    # Very small terminals still get a clock without stealing the window list.
    if budget < width(clock_part[0]):
        return segment(trim(time.strftime('%H:%M'), budget), path_colour)[1]
    return result + '#[default]'


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--accent-palette':
        if re.fullmatch(r'[0-9a-fA-F]{6}', sys.argv[2]):
            print(accent_palette(sys.argv[2]))
    elif len(sys.argv) == 3 and sys.argv[1] == '--training-terminal':
        pid = sys.argv[2]
        print(int(pid.isascii() and pid.isdecimal() and foreground_training(int(pid))))
    elif len(sys.argv) == 5 and sys.argv[1] == '--remote-terminal':
        pane_pid, tty, command = sys.argv[2:]
        print(int(remote_terminal(pane_pid, tty, command)))
    elif len(sys.argv) == 4 and sys.argv[1] == '--foreground-cli':
        pane_pid, command = sys.argv[2:]
        if pane_pid.isascii() and pane_pid.isdecimal() and re.fullmatch(r'[\w.-]+', command, re.ASCII):
            brand = foreground_cli(int(pane_pid))
            if brand:
                # tmux may briefly reuse a job's output after focus moves to another pane.
                print(f'{pane_pid}:{command}:{brand}')
    else:
        try:
            print(render(sys.argv[1], max(1, int(sys.argv[2] or '80')), *sys.argv[3:]))
        except Exception:
            print(' status unavailable ')
