"""FlowTodo 外部插件入口 —— Class Widgets 2 插件包。

设计原则：
- 不改动 FlowTodo 任何逻辑与 UI，以独立进程后台拉起；
- on_load 失败不影响 Class Widgets 2 正常运行（本模块异常全部吞掉）；
- 防重复启动：FlowTodo 已在运行时不再拉起。
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path

try:
    from ClassWidgets.SDK import CW2Plugin
except Exception:  # 兜底：SDK 未注入时退化为普通类，避免导入即崩溃
    class CW2Plugin:  # type: ignore[no-redef]
        def __init__(self, api=None):
            self.PATH = Path()
            self.meta = {}

        def on_load(self) -> None:  # pragma: no cover
            pass

        def on_unload(self) -> None:  # pragma: no cover
            pass


class Plugin(CW2Plugin):
    """FlowTodo 插件：on_load 时以独立进程拉起 FlowTodo（app.py）。"""

    def on_load(self) -> None:
        try:
            root = Path(self.PATH) if getattr(self, "PATH", None) else Path(__file__).resolve().parent
            if (root / "app.py").is_file():
                self._launch_flowtodo(root)
        except Exception:
            pass

    def on_unload(self) -> None:
        # 独立进程由系统回收，插件卸载不做额外处理
        pass

    @staticmethod
    def _flowtodo_already_running(root: Path) -> bool:
        """通过进程命令行匹配判断 FlowTodo 是否已在运行（python/pythonw 均可）。"""
        marker = str(root / "app.py")
        try:
            if platform.system() == "Windows":
                ps = (
                    "Get-CimInstance Win32_Process | "
                    "Where-Object { $_.Name -match '^python(w)?\\.exe$' -and "
                    "$_.CommandLine -like '*" + marker.replace("'", "''") + "*' } | "
                    "Measure-Object | Select-Object -ExpandProperty Count"
                )
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                count = result.stdout.strip()
                return count.isdigit() and int(count) > 0
            result = subprocess.run(
                ["pgrep", "-f", str(root / "app.py")],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def _launch_flowtodo(root: Path) -> bool:
        """后台启动 FlowTodo，返回是否启动成功。"""
        entry = root / "app.py"
        if not entry.is_file():
            return False

        # 优先使用 FlowTodo 自带 venv 的 pythonw.exe；找不到再降级系统 pythonw/python
        pythonw = root / ".venv" / "Scripts" / "pythonw.exe"
        if not pythonw.is_file():
            pythonw = Path(shutil.which("pythonw") or shutil.which("python") or "")
        if not pythonw.is_file():
            return False

        creationflags = (
            getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        )
        proc = subprocess.Popen(
            [str(pythonw), str(entry)],
            cwd=str(root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        return proc.poll() is None
