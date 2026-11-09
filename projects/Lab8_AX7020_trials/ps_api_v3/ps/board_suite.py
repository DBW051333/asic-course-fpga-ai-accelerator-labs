"""Sequential board validation; stops at the first failed check."""
import subprocess,sys
for args in [['compare_api.py'],['acceptance.py'],['run_lab8.py','--bit','lab8.bit','--features','--output','board_scalar'],['run_batch.py','--bitfile','lab8.bit','--output','batch_board_results.json'],['stress_api.py'],['fault_dma.py']]:
 print('RUN',args,flush=True);subprocess.check_call([sys.executable]+args)
