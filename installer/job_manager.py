#!/usr/bin/env python3
import threading


class JobManagerError(RuntimeError):
    pass


class JobManager:
    def __init__(self, runner):
        self.runner = runner
        self._threads = {}
        self._lock = threading.Lock()

    def is_active(self, job_id):
        with self._lock:
            thread = self._threads.get(job_id)
            return bool(thread and thread.is_alive())

    def _finish(self, job_id):
        with self._lock:
            current = self._threads.get(job_id)
            if current is threading.current_thread():
                self._threads.pop(job_id, None)
    def _worker(self, job_id, mode, enabled):
        try:
            if mode == "run":
                self.runner.run(job_id, enabled=enabled)
            elif mode == "resume":
                self.runner.resume(job_id, enabled=enabled)
            elif mode == "retry":
                self.runner.retry(job_id, enabled=enabled)
            else:
                raise JobManagerError(
                    f"Nieznany tryb joba: {mode}"
                )
        except Exception:
            # JobRunner persists the failure state itself.
            pass
        finally:
            self._finish(job_id)

    def start(self, job_id, *, mode="run", enabled=True):
        with self._lock:
            current = self._threads.get(job_id)
            if current and current.is_alive():
                raise JobManagerError(
                    "To zadanie jest już wykonywane."
                )

            thread = threading.Thread(
                target=self._worker,
                args=(job_id, mode, enabled),
                name=f"lms-install-{job_id[:8]}",
                daemon=False,
            )
            self._threads[job_id] = thread
            thread.start()
        return True
