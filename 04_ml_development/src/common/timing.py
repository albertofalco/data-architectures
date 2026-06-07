"""Performance timing utilities for training and production scoring."""

from __future__ import annotations

import json
import resource
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


@dataclass
class PerformanceLogger:
    """Collect elapsed-time metrics and persist them as JSON."""

    metrics: dict[str, float | int | str] = field(default_factory=dict)

    @contextmanager
    def timed(self, metric_name: str) -> Iterator[None]:
        """Measure a named phase using a monotonic performance counter."""
        start = time.perf_counter()
        try:
            yield
        finally:
            self.metrics[metric_name] = round(time.perf_counter() - start, 6)

    def add(self, metric_name: str, value: float | int | str) -> None:
        """Store an externally computed metric."""
        self.metrics[metric_name] = value

    def snapshot_memory(self, label: str) -> None:
        """Store process and system memory metrics for a named pipeline stage."""
        process_rss_mb: float | None = None
        process_tree_rss_mb: float | None = None
        process_child_count: int | None = None
        system_mem_available_mb: float | None = None
        system_mem_used_percent: float | None = None

        try:
            import psutil

            process = psutil.Process()
            process_rss_mb = process.memory_info().rss / 1024**2
            child_processes = process.children(recursive=True)
            process_child_count = len(child_processes)
            process_tree_rss_mb = process_rss_mb + sum(
                child.memory_info().rss / 1024**2
                for child in child_processes
                if child.is_running()
            )
            system_memory = psutil.virtual_memory()
            system_mem_available_mb = system_memory.available / 1024**2
            system_mem_used_percent = system_memory.percent
        except ImportError:
            pass

        peak_rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            peak_rss_mb = peak_rss_mb / 1024**2
        else:
            peak_rss_mb = peak_rss_mb / 1024

        if process_rss_mb is not None:
            self.metrics[f"{label}_process_rss_mb"] = round(process_rss_mb, 3)
        if process_tree_rss_mb is not None:
            self.metrics[f"{label}_process_tree_rss_mb"] = round(process_tree_rss_mb, 3)
        if process_child_count is not None:
            self.metrics[f"{label}_process_child_count"] = process_child_count
        self.metrics[f"{label}_process_peak_rss_mb"] = round(peak_rss_mb, 3)
        cgroup_memory = self._cgroup_memory()
        if cgroup_memory:
            for metric_name, value in cgroup_memory.items():
                self.metrics[f"{label}_{metric_name}"] = value
        if system_mem_available_mb is not None:
            self.metrics[f"{label}_system_mem_available_mb"] = round(
                system_mem_available_mb, 3
            )
        if system_mem_used_percent is not None:
            self.metrics[f"{label}_system_mem_used_percent"] = round(
                system_mem_used_percent, 3
            )

    def _cgroup_memory(self) -> dict[str, float | str]:
        """Return Docker/container memory metrics when cgroup files are available."""
        current_path = Path("/sys/fs/cgroup/memory.current")
        max_path = Path("/sys/fs/cgroup/memory.max")
        if current_path.exists():
            current_mb = int(current_path.read_text(encoding="utf-8").strip()) / 1024**2
            metrics: dict[str, float | str] = {
                "cgroup_mem_current_mb": round(current_mb, 3)
            }
            if max_path.exists():
                raw_limit = max_path.read_text(encoding="utf-8").strip()
                if raw_limit == "max":
                    metrics["cgroup_mem_limit_mb"] = "max"
                else:
                    limit_mb = int(raw_limit) / 1024**2
                    metrics["cgroup_mem_limit_mb"] = round(limit_mb, 3)
                    metrics["cgroup_mem_used_percent"] = round(
                        current_mb * 100 / limit_mb, 3
                    )
            return metrics

        current_path = Path("/sys/fs/cgroup/memory/memory.usage_in_bytes")
        limit_path = Path("/sys/fs/cgroup/memory/memory.limit_in_bytes")
        if not current_path.exists():
            return {}

        current_mb = int(current_path.read_text(encoding="utf-8").strip()) / 1024**2
        limit_mb = int(limit_path.read_text(encoding="utf-8").strip()) / 1024**2
        return {
            "cgroup_mem_current_mb": round(current_mb, 3),
            "cgroup_mem_limit_mb": round(limit_mb, 3),
            "cgroup_mem_used_percent": round(current_mb * 100 / limit_mb, 3),
        }

    def add_throughput(self, rows: int, total_seconds_metric: str) -> None:
        """Add rows-per-second and average latency metrics."""
        seconds = float(self.metrics.get(total_seconds_metric, 0.0) or 0.0)
        self.metrics["rows_scored"] = rows
        self.metrics["rows_per_second"] = round(rows / seconds, 6) if seconds else 0.0
        self.metrics["avg_latency_ms_per_row"] = (
            round(seconds * 1000 / rows, 6) if rows else 0.0
        )

    def write_json(self, path: Path) -> Path:
        """Write collected metrics to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.metrics, indent=2, sort_keys=True), encoding="utf-8")
        return path
