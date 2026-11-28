"""Report build results, progress, and log notices to a Kael tmux pane."""

import argparse
import os
import re
import subprocess
import sys
import time


TASK = '@pane-task'
WARNING = '@pane-task-warning'
TOKEN_ENV = 'KAEL_PANE_TASK_ID'
LOG_WARNING = re.compile(
    rb'^(?:\[[^\]\r\n]{1,80}\]\s*){0,2}\[?(?:WARN(?:ING)?|ERROR|CRITICAL)\]?(?=[:\s]|$)',
    re.IGNORECASE,
)
SGR = re.compile(rb'\x1b\[[0-9;:]*m')


def monotonic_ms():
    return time.monotonic_ns() // 1_000_000


class Pane:
    def __init__(self, tmux, target):
        self.tmux = tmux
        args = ['-t', target] if target else []
        self.id = self.call('display-message', '-p', *args, '#{pane_id}')
        if not re.fullmatch(r'%[0-9]+', self.id):
            raise ValueError('No tmux pane was found')

    def call(self, *args):
        return subprocess.check_output([*self.tmux, *args], stdin=subprocess.DEVNULL,
                                       text=True).rstrip('\n')

    def set(self, option, value):
        self.call('set-option', '-p', '-t', self.id, option, value)

    def start(self):
        token = f'{os.getpid()}-{time.monotonic_ns()}'
        self.set(TASK, f'build:{token}:-1')
        return token

    def update(self, token, value):
        if not re.fullmatch(r'[0-9]+-[0-9]+', token):
            raise ValueError('Invalid task identifier')
        # Match and update in the server queue so an older job cannot overwrite a newer one.
        condition = f'#{{m:build:{token}:*,#{{{TASK}}}}}'
        self.call('if-shell', '-F', '-t', self.id, condition,
                  f'set-option -p -t {self.id} {TASK} {value}')

    def progress(self, percent):
        value = self.call('display-message', '-p', '-t', self.id, f'#{{{TASK}}}')
        kind, _, fields = value.partition(':')
        token = fields.partition(':')[0] if kind == 'build' else ''
        # An inherited identifier pins progress to the command that emitted it.
        token = os.environ.get(TOKEN_ENV) or token
        if not token:
            raise ValueError('Start a build task before reporting progress')
        self.update(token, f'build:{token}:{percent}')

    def finish(self, status, token=None):
        value = f'{status}:{monotonic_ms()}'
        if token:
            self.update(token, value)
        else:
            self.set(TASK, value)

    def warn(self):
        self.call('if-shell', '-F', '-t', self.id, '#{!:#{pane_active}}',
                  f'set-option -p -t {self.id} {WARNING} {monotonic_ms()}')

    def clear(self):
        self.call('set-option', '-pqu', '-t', self.id, TASK,
                  ';', 'set-option', '-pqu', '-t', self.id, WARNING)


def run_task(pane, command):
    token = pane.start()
    env = {**os.environ, TOKEN_ENV: token, 'TMUX_PANE': pane.id}
    try:
        status = subprocess.run(command, env=env, check=False).returncode
        if status < 0:
            status = 128 - status
    except KeyboardInterrupt:
        status = 130
    except OSError as error:
        print(f'kael-tmux task: {error}', file=sys.stderr)
        status = 127 if isinstance(error, FileNotFoundError) else 126

    try:
        pane.finish('done' if status == 0 else 'fail', token)
    except (OSError, subprocess.CalledProcessError):
        pass  # The child command's result survives loss of the tmux pane or server.
    return status


def watch_logs(pane):
    next_warning = 0
    for line in sys.stdin.buffer:
        sys.stdout.buffer.write(line)
        sys.stdout.buffer.flush()
        now = monotonic_ms()
        if now >= next_warning and LOG_WARNING.match(SGR.sub(b'', line)):
            pane.warn()
            next_warning = now + 200
    return 0


def main(argv):
    separator = argv.index('--')
    tmux, args = argv[:separator], argv[separator + 1:]
    parser = argparse.ArgumentParser(prog='kael-tmux task')
    parser.add_argument('--pane', default=os.environ.get('TMUX_PANE'))
    commands = parser.add_subparsers(dest='action', required=True)
    commands.add_parser('start', help='start a build or test')
    progress = commands.add_parser('progress', help='report a build percentage')
    progress.add_argument('percent', type=int, choices=range(101), metavar='0–100')
    commands.add_parser('done', help='report success')
    commands.add_parser('fail', help='report failure')
    commands.add_parser('warn', help='report an unread log warning')
    commands.add_parser('clear', help='clear task and warning states')
    commands.add_parser('watch', help='forward labelled log lines and flag warnings')
    runner = commands.add_parser('run', help='run a build or test and report its result')
    runner.add_argument('command', nargs=argparse.REMAINDER)
    options = parser.parse_args(args)
    command = getattr(options, 'command', [])
    if command and command[0] == '--':
        command = command[1:]
    if options.action == 'run' and not command:
        parser.error('run requires a command')

    try:
        pane = Pane(tmux, options.pane)
        if options.action == 'run':
            return run_task(pane, command)
        if options.action == 'watch':
            return watch_logs(pane)
        if options.action == 'start':
            pane.start()
        elif options.action == 'progress':
            pane.progress(options.percent)
        elif options.action in ('done', 'fail'):
            pane.finish(options.action, os.environ.get(TOKEN_ENV))
        elif options.action == 'warn':
            pane.warn()
        else:
            pane.clear()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'kael-tmux task: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
