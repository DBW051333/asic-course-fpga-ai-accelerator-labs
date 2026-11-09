"""Parent-path cProfile; attribution only, not performance acceptance."""
from pathlib import Path
import cProfile,pstats,json,time
import numpy as np
from parent_driver import Lab8NPU
R=Path(__file__).resolve().parent
xs=np.fromfile(R/'inputs.bin',np.int8).reshape(42,512)
with Lab8NPU(R/'lab8.bit') as n:
 n.prepare_batch(128)
 for mode,count in [('scalar',1),('batch',42),('batch',128)]:
  x=np.resize(xs,(count,512)).copy()
  call=(lambda:n.infer(x[0])) if mode=='scalar' else (lambda:n.infer_batch(x))
  for _ in range(10):call()
  profile=cProfile.Profile();profile.enable()
  for _ in range(100):call()
  profile.disable();profile.dump_stats(str(R/f'profile_{mode}_{count}.pstats'))
  with (R/f'profile_{mode}_{count}.txt').open('w') as f:
   pstats.Stats(profile,stream=f).strip_dirs().sort_stats('cumulative').print_stats(35)
print('Saved parent profiles')
