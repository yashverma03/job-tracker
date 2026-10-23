import logging
import os
import subprocess

logger = logging.getLogger(__name__)

_RUNTIME_DIR = f'/run/user/{os.getuid()}'


class NotificationManager:
    """Manages OS notifications using zenity."""

    @staticmethod
    def show(title: str, message: str, width: int | None = None, height: int | None = None) -> None:
        logger.info('Notification: %s - %s', title, message)
        NotificationManager._run(['zenity', '--info', '--title', title, '--text', message], width, height)

    @staticmethod
    def show_table(
        title: str,
        columns: list[str],
        rows: list[list[str]],
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        """Displays a read-only table dialog - one row per entry in `rows`, each a list of
        cell values matching `columns` in order."""
        logger.info('Notification: %s - columns=%s rows=%s', title, columns, rows)
        command = ['zenity', '--list', '--title', title]
        for column in columns:
            command += ['--column', column]
        for row in rows:
            command += [str(cell) for cell in row]
        NotificationManager._run(command, width, height)

    @staticmethod
    def _run(command: list[str], width: int | None, height: int | None) -> None:
        if width is not None:
            command += ['--width', str(width)]
        if height is not None:
            command += ['--height', str(height)]

        # Cron/@reboot processes have no desktop session variables, so zenity can't find the display.
        env = os.environ.copy()
        env.setdefault('XDG_RUNTIME_DIR', _RUNTIME_DIR)
        env.setdefault('WAYLAND_DISPLAY', 'wayland-0')
        env.setdefault('DBUS_SESSION_BUS_ADDRESS', f'unix:path={_RUNTIME_DIR}/bus')

        # Detached and non-blocking: the dialog stays open until dismissed.
        subprocess.Popen(command, env=env, start_new_session=True, stdin=subprocess.DEVNULL)
