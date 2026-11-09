"""Board-side batch/scalar comparison; model checks outside timed DMA calls."""
from pathlib import Path
import argparse,json
import numpy as np
from lab8_driver import Lab8NPU

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--bitfile',default=str(Path(__file__).with_name('lab8.bit')))
    parser.add_argument('--output',default='batch_board_results.json')
    args=parser.parse_args()
    root=Path(__file__).parent
    xs=np.fromfile(root/'inputs.bin',np.int8).reshape(42,512)
    gold=np.fromfile(root/'features.bin',np.int8).reshape(42,162)
    pred=np.fromfile(root/'predictions.bin',np.uint8)
    with Lab8NPU(args.bitfile) as n:
        n.prepare_batch(42)
        singles=[n.infer(x) for x in xs]
        batch=n.infer_batch(xs)
        assert [v['prediction'] for v in singles]==pred.tolist()
        np.testing.assert_array_equal(batch['predictions'],pred)
        np.testing.assert_array_equal(batch['scores'],gold[:,160:162])
        f=n.features()
        np.testing.assert_array_equal(np.concatenate([f['fc1'],f['fc2'],f['fc3']]),gold[-1])
        scalar_us=sum(v['ps_end_to_end_us'] for v in singles)
        report={'scope':'Board measurements produced only when this program runs on the board',
                'samples':42,'scalar_dma_calls':42,'batch_dma_calls':1,
                'scalar_sum_ps_us':scalar_us,'batch_ps_us':batch['ps_end_to_end_us'],
                'speedup':scalar_us/batch['ps_end_to_end_us'],
                'batch_pl_transaction_cycles':batch['pl_transaction_cycles'],
                'core_cycles':batch['compute_cycles'],'predictions':batch['predictions'].tolist(),
                'scores':batch['scores'].tolist(),'last_sample_features_checked':True,
                'buffer_allocation_and_feature_readback_excluded':True}
        Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
if __name__=='__main__':main()
