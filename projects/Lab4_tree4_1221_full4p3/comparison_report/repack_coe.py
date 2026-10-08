from pathlib import Path
import re

root = Path('/home/ding/vivado_project/Lab4_parallel64_packed')
for old_name, new_name, expected_rows in (
    ('sel_data_128.coe', 'sel_data_64.coe', 4),
    ('fc1.0.weight_128.coe', 'fc1.0.weight_64.coe', 512),
):
    source = (root / old_name).read_text()
    body = source.split('memory_initialization_vector', 1)[1].split('=', 1)[1].split(';', 1)[0]
    rows = [item.strip() for item in body.split(',')]
    assert len(rows) == expected_rows
    assert all(re.fullmatch(r'[01]{1024}', row) for row in rows)
    split_rows = [half for row in rows for half in (row[:512], row[512:])]
    assert all(split_rows[2*i] + split_rows[2*i+1] == rows[i] for i in range(len(rows)))
    (root / new_name).write_text('memory_initialization_radix = 2;\nmemory_initialization_vector =\n' + ',\n'.join(split_rows) + ';\n')
    print(f'{old_name}: {len(rows)} x 1024 -> {new_name}: {len(split_rows)} x 512; bit-exact')
