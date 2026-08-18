"""FlowTodo 外部插件入口 —— Class Widgets 2 插件包。

设计原则：
- 不改动 FlowTodo 任何逻辑与 UI，以独立进程后台拉起；
- 优先使用 FlowTodo 项目自带 .venv 的 pythonw 启动项目根 app.py，
  避免插件目录/系统 Python 缺依赖导致静默秒退；
- on_load 失败不影响 Class Widgets 2 正常运行（本模块异常全部吞掉）；
- 防重复启动：FlowTodo 已在运行时不再拉起（同时匹配项目目录与插件目录两种来源）。
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


# FlowTodo 项目根目录（自带完整 .venv，依赖齐全）
FLOWTODO_PROJECT_DIR = Path(r"D:\FlowTodo-FluentUI-version-master (1)\FlowTodo-FluentUI-version-master")
# 项目目录进程匹配标识（防重检测用）
_PROJECT_PROCESS_MARKER = "FlowTodo-FluentUI-version-master"


class Plugin(CW2Plugin):
    """FlowTodo 插件：on_load 时以独立进程拉起 FlowTodo（app.py）。"""

    def on_load(self) -> None:
        try:
            # 优先使用 FlowTodo 项目目录（依赖完整），找不到再回退插件目录
            root = FLOWTODO_PROJECT_DIR if (FLOWTODO_PROJECT_DIR / "app.py").is_file() else None
            if root is None:
                plugin_root = Path(self.PATH) if getattr(self, "PATH", None) else Path(__file__).resolve().parent
                if (plugin_root / "app.py").is_file():
                    root = plugin_root
            if root is not None:
                self._launch_flowtodo(root)
        except Exception:
            pass

    def on_unload(self) -> None:
        # 独立进程由系统回收，插件卸载不做额外处理
        pass

    @staticmethod
    def _flowtodo_already_running(root: Path) -> bool:
        """通过进程命令行匹配判断 FlowTodo 是否已在运行（python/pythonw 均可）。"""
        markers = [str(root / "app.py")]
        # 同时匹配项目目录启动的进程，避免防重误判
        proj_app = FLOWTODO_PROJECT_DIR / "app.py"
        if proj_app.is_file() and str(proj_app) not in markers:
            markers.append(str(proj_app))
        try:
            if platform.system() == "Windows":
                cond = " -or ".join(
                    "$_.CommandLine -like '*" + m.replace("'", "''") + "*'" for m in markers
                )
                ps = (
                    "Get-CimInstance Win32_Process | "
                    "Where-Object { $_.Name -match '^python(w)?\\.exe$' -and ("
                    + cond + ") } | "
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
    def _spawn(pythonw: Path, entry: Path, cwd: Path) -> bool:
        """以独立进程拉起 entry，返回是否启动成功。"""
        creationflags = (
            getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        )
        proc = subprocess.Popen(
            [str(pythonw), str(entry)],
            cwd=str(cwd),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        return proc.poll() is None

    @classmethod
    def _launch_flowtodo(cls, root: Path) -> bool:
        """后台启动 FlowTodo，返回是否启动成功。"""
        entry = root / "app.py"
        if not entry.is_file():
            return False
        if cls._flowtodo_already_running(root):
            return True

        # 优先使用 FlowTodo 自带 venv 的 pythonw.exe；找不到再降级系统 pythonw/python
        pythonw = root / ".venv" / "Scripts" / "pythonw.exe"
        if not pythonw.is_file():
            pythonw = Path(shutil.which("pythonw") or shutil.which("python") or "")
        if not pythonw.is_file():
            return False

        return cls._spawn(pythonw, entry, root)
