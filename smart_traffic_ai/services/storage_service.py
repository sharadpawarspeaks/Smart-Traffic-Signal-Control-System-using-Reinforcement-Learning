from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_SETTINGS = {
    "arrival_rates": [0.22, 0.20, 0.18, 0.16],
    "traffic_preset": "Medium",
    "min_green": 5,
    "max_green": 35,
    "yellow_duration": 2,
    "learning_rate": 0.15,
    "discount_factor": 0.92,
    "initial_epsilon": 1.0,
    "epsilon_min": 0.05,
    "epsilon_decay": 0.995,
    "weight_pass": 3.0,
    "weight_wait": 0.20,
    "weight_queue": 0.05,
    "weight_switch": 0.40,
    "weight_starve": 0.10,
    "starvation_threshold": 40.0,
    "simulation_speed": 1.0,
    "random_seed": 42,
}


class StorageService:
    """Handles JSON persistence for settings, Q-tables, and experiment results."""

    def __init__(self, base_dir: str | Path = "data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.base_dir / "settings.json"
        self.q_table_file = self.base_dir / "q_table.json"
        self.experiments_file = self.base_dir / "experiments.json"

    def load_settings(self) -> Dict[str, Any]:
        if not self.settings_file.exists():
            self.save_settings(DEFAULT_SETTINGS)
            return dict(DEFAULT_SETTINGS)
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Merge with defaults in case of missing keys
                merged = dict(DEFAULT_SETTINGS)
                merged.update(data)
                return merged
        except Exception:
            return dict(DEFAULT_SETTINGS)

    def save_settings(self, settings: Dict[str, Any]) -> None:
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_q_table(self, custom_path: Path | str | None = None) -> Dict[str, List[float]]:
        path = Path(custom_path) if custom_path else self.q_table_file
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_q_table(self, q_table: Dict[str, List[float]], custom_path: Path | str | None = None) -> None:
        path = Path(custom_path) if custom_path else self.q_table_file
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(q_table, f, indent=2)
        except Exception as e:
            print(f"Error saving Q-table: {e}")

    def load_experiments(self) -> List[Dict[str, Any]]:
        if not self.experiments_file.exists():
            return []
        try:
            with open(self.experiments_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save_experiment(self, experiment_record: Dict[str, Any]) -> None:
        experiments = self.load_experiments()
        experiments.append(experiment_record)
        try:
            with open(self.experiments_file, "w", encoding="utf-8") as f:
                json.dump(experiments, f, indent=2)
        except Exception as e:
            print(f"Error saving experiment: {e}")

    def export_experiments_csv(self, records: List[Dict[str, Any]], export_path: str | Path) -> None:
        target = Path(export_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not records:
            return
        keys = list(records[0].keys())
        with open(target, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(records)
