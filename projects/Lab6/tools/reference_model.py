#!/usr/bin/env python3
"""Generate all 42 Lab6 stimuli and bit-exact integer reference results."""
from pathlib import Path
import re
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def read_coe(path):
    body = path.read_text().split('memory_initialization_vector', 1)[1].split('=', 1)[1]
    words = [v.strip() for v in re.split(r'[,;]', body) if v.strip()]
    return [int(v, 2) - (1 << len(v) if v[0] == '1' else 0) for v in words]

X = np.asarray(read_coe(ROOT / 'data/sel_data.coe'), dtype=np.int64).reshape(42, 512)
W = [np.asarray(read_coe(ROOT / 'data/params' / name), dtype=np.int64).reshape(n, m).T
     for name, n, m in [('fc1.0.weight.coe', 128, 512),
                        ('fc2.0.weight.coe', 32, 128),
                        ('fc3.weight.coe', 2, 32)]]
B = [np.asarray(read_coe(ROOT / 'data/params' / name), dtype=np.int64)
     for name in ['fc1.0.bias.coe', 'fc2.0.bias.coe', 'fc3.bias.coe']]
labels = [int(s) for s in re.findall(r'[01]', (ROOT/'data/sel_labels.txt').read_text())]
assert len(labels) == 42

def predict(scores):
    return (scores[:, 0] < scores[:, 1]).astype(np.int64)

def write_mem(path, array, width):
    mask = (1 << width) - 1
    path.write_text(''.join(f'{int(v)&mask:0{(width+3)//4}x}\n' for v in array.flat))

# Four 1024-bit BRAM words per sample, with the same lane order as Lab5.
with (ROOT/'data/samples_128.mem').open('w') as f:
    for row in X:
        for j in range(0, 512, 128):
            f.write(''.join(f'{int(v)&255:08b}' for v in row[j:j+128])+'\n')

baseline1 = np.maximum(0, X@W[0]+B[0])
baseline2 = np.maximum(0, baseline1@W[1]+B[1])
baseline3 = baseline2@W[2]+B[2]
assert np.array_equal(baseline3[0], np.asarray([int(v) for v in (ROOT.parent/'Lab5/data/reference/fc3.txt').read_text().split()]))
print(f'baseline: {sum(predict(baseline3)==labels)}/42')
for width, shifts in [(8, (10,9,8)), (4, (14,8,9))]:
    a = baseline1 >> shifts[0]
    b = np.maximum(0, a@W[1]+B[1]) >> shifts[1]
    c = (b@W[2]+B[2]) >> shifts[2]
    limit = 1 << (width-1)
    for name, vals in [('fc1',a),('fc2',b),('fc3',c)]:
        assert vals.min() >= -limit and vals.max() < limit, (width,name,vals.min(),vals.max())
        write_mem(ROOT/'data'/f'{name}_expected_{width}.mem', vals, width)
    pred = predict(c)
    with (ROOT/'results'/f'reference_{width}.csv').open('w') as f:
        f.write('sample,score0,score1,prediction,label,correct\n')
        for i in range(42):
            f.write(f'{i},{c[i,0]},{c[i,1]},{pred[i]},{labels[i]},{int(pred[i]==labels[i])}\n')
    print(f'{width}-bit: shifts={shifts}, accuracy={sum(pred==labels)}/42')
