"""Small reproducible throughput benchmark for the simulated pipeline."""
from pathlib import Path
import sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from drone_agent.models import load_frames, Frame
from drone_agent.agent import SecurityAnalystAgent

frames = load_frames(Path(__file__).resolve().parents[1] / 'data' / 'frames.json')
print('frames,seconds,frames_per_second')
for factor in (1, 10, 50):
    workload = [Frame(i + 1, f.telemetry, f.description) for i, f in enumerate(frames * factor)]
    agent = SecurityAnalystAgent()
    start = time.perf_counter()
    agent.run(workload)
    elapsed = time.perf_counter() - start
    print(f'{len(workload)},{elapsed:.4f},{len(workload)/elapsed:.1f}')
