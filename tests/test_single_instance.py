import os
import subprocess

import claude_usage_tray.single_instance as single_instance


def test_second_acquire_in_same_process_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(single_instance, "_LOCK_PATH", tmp_path / "test.lock")

    assert single_instance.acquire_lock() is True
    assert single_instance.acquire_lock() is False

    single_instance.release_lock()
    assert single_instance.acquire_lock() is True
    single_instance.release_lock()


def test_stale_lock_from_dead_pid_is_reclaimed(tmp_path, monkeypatch):
    lock_path = tmp_path / "test.lock"
    monkeypatch.setattr(single_instance, "_LOCK_PATH", lock_path)

    # A PID essentially guaranteed not to correspond to a running process.
    lock_path.write_text("999999", encoding="ascii")

    assert single_instance.acquire_lock() is True
    assert int(lock_path.read_text(encoding="ascii").strip()) == os.getpid()

    single_instance.release_lock()


def test_lock_pointing_at_unrelated_non_python_pid_is_reclaimed(tmp_path, monkeypatch):
    """A stale lock's PID can be recycled by Windows onto an unrelated process
    (e.g. explorer.exe). That must still be treated as reclaimable, not as a
    real running instance."""
    lock_path = tmp_path / "test.lock"
    monkeypatch.setattr(single_instance, "_LOCK_PATH", lock_path)

    non_python_process = subprocess.Popen(
        ["cmd.exe", "/c", "timeout", "/t", "10", "/nobreak"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        lock_path.write_text(str(non_python_process.pid), encoding="ascii")

        assert single_instance.acquire_lock() is True
        assert int(lock_path.read_text(encoding="ascii").strip()) == os.getpid()
    finally:
        non_python_process.terminate()
        non_python_process.wait(timeout=5)

    single_instance.release_lock()


def test_pid_is_running_recognizes_current_python_process():
    assert single_instance._pid_is_running(os.getpid()) is True
