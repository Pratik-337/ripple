import os
import json
import time
from pathlib import Path
from parser.pipeline import run_pipeline

def measure_explosion(node_id):
    project_root = Path("/home/emma_carstairs/geminicli/samples_large")
    print(f'--- [EXPLOSION TEST]: {node_id} ---')
    
    for hops in [1, 2, 3, 4]:
        if os.path.exists("impact_cache.json"): os.remove("impact_cache.json")
        t_start = time.time()
        res, _ = run_pipeline(project_root, node_id, max_hops=hops)
        t_end = time.time()
        
        # We need to extract neighborhood size from the logs or pass it back. 
        # For now, we will observe the log output manually.
        summary = res["data"]["summary"]
        print(f"Hops: {hops} | Time: {t_end - t_start:.2f}s | Total Affected: {summary['total_affected']}")

if __name__ == "__main__":
    # Center node in module_0
    measure_explosion("python::module_0::func_5()")
