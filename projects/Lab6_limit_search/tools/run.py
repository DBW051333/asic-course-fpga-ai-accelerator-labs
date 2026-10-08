import sys
from pathlib import Path
sys.path.insert(0,'/home/ding/vivado_project/Lab6_bottleneck_optimization/tools')
import run as runner
runner.ROOT=Path('/home/ding/vivado_project/Lab6_limit_search')
for arg in sys.argv[1:]:
 name,stage=arg.split(':')
 if not runner.run(name,stage):raise SystemExit(1)
