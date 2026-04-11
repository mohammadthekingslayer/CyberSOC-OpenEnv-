"""Task definitions for CyberSOC OpenEnv."""

from .registry import TaskRegistry
from .task1_brute_force import BruteForceTask
from .task2_malware import MalwareTask
from .task3_apt import APTTask

__all__ = ["TaskRegistry", "BruteForceTask", "MalwareTask", "APTTask"]
