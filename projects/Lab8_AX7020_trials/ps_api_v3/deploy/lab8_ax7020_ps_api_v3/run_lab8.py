"""Run on the AX7020: python3 run_lab8.py --features

The numerical classification rule is retained from the verified Lab7 model.
Default display names follow the Lab6 slide: label 0 abnormal, label 1 normal.
The PPT score-to-label direction conflicts with the supplied reference script;
changing a display name never changes the numerical predictions or accuracy.
"""
from pathlib import Path
import argparse,csv,json,statistics,sys
import numpy as np
from lab8_driver import Lab8NPU

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--bit',default=str(Path(__file__).parent/'lab8.bit'))
    parser.add_argument('--features',action='store_true',help='read/verify all layers after every sample')
    parser.add_argument('--label0-name',default='异常')
    parser.add_argument('--label1-name',default='正常')
    parser.add_argument('--output',default='board_results')
    parser.add_argument('--timeout',type=float,default=2.0)
    args=parser.parse_args()
    root=Path(__file__).parent;out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    names={0:args.label0_name,1:args.label1_name}
    xs=np.fromfile(root/'inputs.bin',dtype=np.int8).reshape(42,512)
    labels=np.fromfile(root/'labels.bin',dtype=np.uint8)
    expected=np.fromfile(root/'predictions.bin',dtype=np.uint8)
    gold=np.fromfile(root/'features.bin',dtype=np.int8).reshape(42,162)
    rows=[];features=[];correct=0;mismatches=0
    with Lab8NPU(args.bit,timeout=args.timeout) as npu:
        for i,x in enumerate(xs):
            r=npu.infer(x)
            row={'sample':i,'label':int(labels[i]),'classification_name':names[r['prediction']],**r}
            row['correct']=int(r['prediction']==labels[i]);correct+=row['correct']
            row['reference_match']=int(r['prediction']==expected[i])
            if not row['reference_match']:
                raise RuntimeError(f'Sample {i}: classification disagrees with integer reference')
            if args.features:
                f=npu.features();vals=np.concatenate([f['fc1'],f['fc2'],f['fc3']]);features.append(vals)
                mismatch=int(np.count_nonzero(vals!=gold[i]));mismatches+=mismatch
                row['feature_mismatches']=mismatch;row['ps_readback_us']=f['ps_readback_us']
                if mismatch:
                    raise RuntimeError(f'Sample {i}: {mismatch} feature values disagree with integer reference')
                if int(f['fc3'][0]<f['fc3'][1])!=r['prediction']:
                    raise RuntimeError('Returned signed scores disagree with the returned class')
            rows.append(row)
            print(f"样本 {i+1:02d}/42：分类={names[r['prediction']]}({r['prediction']}) 标签={labels[i]} "
                  f"核心={r['compute_us']:.3f}us PL事务={r['pl_transaction_us']:.3f}us "
                  f"主机DMA窗口={r['ps_end_to_end_us']:.3f}us")
        clock_evidence=npu.clock_evidence;buffer_evidence=getattr(npu,"buffer_evidence",None);clock_hz=npu.clock_hz
        jobs=npu.regs.read(0x10);errors=npu.regs.read(0x14)
        if jobs!=42 or errors:
            raise RuntimeError(f'Hardware totals incorrect: completed={jobs} errors={errors}')
    with (out/'samples.csv').open('w',newline='') as fd:
        writer=csv.DictWriter(fd,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    if features:np.save(out/'features.npy',np.stack(features))
    result={'scope':'AX7020 board run','label_display_names':names,'samples':42,'correct':correct,'accuracy':correct/42,
            'reference_classification_mismatches':sum(1-r['reference_match'] for r in rows),
            'feature_values_checked':42*162 if args.features else 0,'feature_mismatches':mismatches,
            'clock_hz':clock_hz,'clock_evidence':clock_evidence,'buffers':buffer_evidence,'hardware_completed_jobs':jobs,'hardware_errors':errors,
            'feature_readback_outside_inference_timing':True,
            'timing':{key:{'min':min(r[key] for r in rows),'median':statistics.median(r[key] for r in rows),
                           'mean':statistics.mean(r[key] for r in rows),'max':max(r[key] for r in rows)}
                      for key in ['compute_us','pl_transaction_us','ps_end_to_end_us']}}
    (out/'summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    print(f'准确率：{correct}/42 = {100*correct/42:.2f}%；特征检查：{result["feature_values_checked"]}项')
    print(f'结果保存到 {out.resolve()}')
if __name__=='__main__':main()
