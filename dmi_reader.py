import json
import os
import sys
import platform
import logging
import multiprocessing
import threading
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

def _is_container() -> bool:
    """Детекция контейнера через cgroup и env."""
    # Файлы-маркеры
    if Path("/.dockerenv").exists():
        return True
    if Path("/run/.containerenv").exists():
        return True
    
    # Проверка cgroup
    try:
        cgroup = Path("/proc/self/cgroup").read_text()
        if any(x in cgroup for x in ["docker", "containerd", "kubepods", "lxc", "podman"]):
            return True
    except (OSError, UnicodeDecodeError):
        pass
    
    return False

# === Linux: чтение из /sys/class/dmi/id/ ===
def _read_dmi_linux() -> Optional[Dict[str, str]]:
    if _is_container():
        return None

    dmi_path = Path("/sys/class/dmi/id")
    if not dmi_path.is_dir():
        return None

    fields = {
        "system_uuid": "product_uuid",
        "board_serial": "board_serial",
        "chassis_serial": "chassis_serial",
        "product_name": "product_name",
        "manufacturer": "sys_vendor",
    }

    result: Dict[str, str] = {}
    for key, filename in fields.items():
        try:
            value = (dmi_path / filename).read_text(encoding="utf-8").strip()
            if value and value not in ("", "None", "To be filled by O.E.M."):
                result[key] = value
        except (OSError, UnicodeDecodeError) as e:
            logger.debug(f"Failed to read {filename}: {e}")
            continue
    return result or None

# === Windows: WMI с таймаутом через multiprocessing ===
def _wmi_worker(queue):
    try:
        import wmi
        import pythoncom
        pythoncom.CoInitialize()
        try:
            c = wmi.WMI()
            cs_list = c.Win32_ComputerSystemProduct()
            bios_list = c.Win32_BIOS()
            
            if not cs_list or not bios_list:
                queue.put(None)
                return
            
            cs = cs_list[0]
            bios = bios_list[0]
            result: Dict[str, str] = {}
            
            if getattr(cs, "UUID", None):
                result["system_uuid"] = cs.UUID.strip()
            if getattr(cs, "IdentifyingNumber", None):
                sn = cs.IdentifyingNumber.strip()
                if sn and sn not in ("", "None", "To be filled by O.E.M."):
                    result["chassis_serial"] = sn
            if getattr(bios, "SerialNumber", None):
                sn = bios.SerialNumber.strip()
                if sn and sn not in ("", "None", "To be filled by O.E.M."):
                    result["bios_serial"] = sn
            
            queue.put(result or None)
        finally:
            pythoncom.CoUninitialize()
    except Exception as e:
        logger.debug(f"WMI worker error: {e}")
        queue.put(None)

def _read_dmi_windows_with_timeout(timeout_sec: int = 5) -> Optional[Dict[str, str]]:
    """Выполняет WMI-запрос в отдельном процессе с таймаутом."""
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=_wmi_worker, args=(queue,))
    process.start()
    process.join(timeout=timeout_sec)
    
    if process.is_alive():
        process.terminate()
        process.join(timeout=1)
        if process.is_alive():
            process.kill()
            process.join()
        logger.warning("WMI query timed out and was terminated")
        return None
    
    try:
        return queue.get(timeout=0.5)
    finally:
        queue.close()
        queue.join_thread()

# === macOS: system_profiler ===
def _read_dmi_macos() -> Optional[Dict[str, str]]:
    """Читает UUID через system_profiler (требует subprocess, но безопасно)."""
    try:
        import subprocess
        result = subprocess.run(
            ["system_profiler", "SPHardwareDataType", "-json"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if result.returncode != 0:
            logger.debug(f"system_profiler failed: {result.stderr}")
            return None
        if not result.stdout:
            return None
        
        data = json.loads(result.stdout)
        hw_list = data.get("SPHardwareDataType")
        if not hw_list or not isinstance(hw_list, list):
            return None
        hw = hw_list[0]
        if not isinstance(hw, dict):
            return None
        uuid = hw.get("platform_UUID")
        if uuid:
            return {"system_uuid": uuid}
        return None
    except (json.JSONDecodeError, AttributeError, OSError) as e:
        logger.debug(f"macOS DMI parse error: {e}")
        return None

# === Fallback: machine-id, hostname ===
def _get_fallback_identifiers() -> Dict[str, str]:
    fallbacks: Dict[str, str] = {}

    # systemd machine-id (Linux)
    try:
        machine_id = Path("/etc/machine-id").read_text().strip()
        if machine_id and machine_id != "unavailable":
            fallbacks["machine_id"] = machine_id
    except (OSError, UnicodeDecodeError):
        pass

    # hostname
    hostname = platform.node()
    if hostname and isinstance(hostname, str) and hostname not in ("localhost", "", "None"):
        fallbacks["hostname"] = hostname

    return fallbacks

# === Thread-safe кеширование на уровне модуля ===
_dmi_cache: Optional[Dict[str, str]] = None
_cache_initialized = False
_cache_lock = threading.Lock()

def _get_cached_dmi() -> Optional[Dict[str, str]]:
    global _dmi_cache, _cache_initialized
    if not _cache_initialized:
        with _cache_lock:
            if not _cache_initialized:  # double-check
                _dmi_cache = _get_raw_dmi()
                _cache_initialized = True
    return _dmi_cache

def _get_raw_dmi() -> Optional[Dict[str, str]]:
    """Внутренняя функция без кеширования."""
    dmi_data: Optional[Dict[str, str]] = None
    
    if sys.platform.startswith("linux"):
        dmi_data = _read_dmi_linux()
    elif sys.platform == "win32":
        dmi_data = _read_dmi_windows_with_timeout(timeout_sec=5)
    elif sys.platform == "darwin":
        dmi_data = _read_dmi_macos()
    else:
        dmi_data = None
    
    return dmi_data

def get_dmi_info(include_fallback: bool = False) -> Optional[Dict[str, str]]:
    """
    Возвращает DMI-информацию или None.
    Если include_fallback=True — добавляет machine-id/hostname при отсутствии DMI.
    """
    dmi_data = _get_cached_dmi()
    if dmi_data is not None:
        return dmi_data
    if include_fallback:
        fallback = _get_fallback_identifiers()
        return fallback or None
    return None