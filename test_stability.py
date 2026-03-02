import os
import json
import time
from pathlib import Path
from parser.pipeline import run_pipeline

def test_determinism():
    project_root = Path('samples')
    start_node = 'python::my_app::MyApp::run_field()'
    
    # 1. LIVE RUN
    if os.path.exists('impact_cache.json'):
        os.remove('impact_cache.json')
    
    print('--- RUN 1: Live Analysis (Cache Miss) ---')
    t1_start = time.time()
    res1, _ = run_pipeline(project_root, start_node)
    t1_end = time.time()
    run1_time = t1_end - t1_start
    
    # 2. CACHED RUN
    print('--- RUN 2: Cached Analysis (Cache Hit) ---')
    t2_start = time.time()
    res2, _ = run_pipeline(project_root, start_node)
    t2_end = time.time()
    run2_time = t2_end - t2_start
    
    print(f'Run 1: {run1_time:.2f}s | Run 2: {run2_time:.2f}s')

    # VERIFICATION
    summary1 = res1['data']['summary']
    summary2 = res2['data']['summary']
    
    if summary1 == summary2:
        print('✅ SUCCESS: Summaries are IDENTICAL (Determinism).')
    else:
        print('❌ FAILURE: Summaries differ!')
        
    if run2_time < run1_time / 2: # Should be at least 2x faster
        print(f'✅ SUCCESS: Cache hit was {(run1_time/run2_time):.1f}x faster.')
    
    if summary1['total_affected'] >= 3:
        print(f'✅ SUCCESS: Found structural impacts ({summary1["total_affected"]}).')

if __name__ == '__main__':
    test_determinism()
