from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lazybooks.config import DEFAULT_CONFIG, LibraryConfig, load_libraries

__all__ = ["DEFAULT_CONFIG", "LibraryConfig", "load_libraries"]
