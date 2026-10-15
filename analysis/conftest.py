# Makes `import analysis...` work when pytest is run from the project root or analysis/.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
