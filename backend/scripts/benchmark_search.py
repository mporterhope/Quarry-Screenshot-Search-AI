import argparse
import time
from pathlib import Path
from app.indexer import ScreenshotIndexer


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', type=str, default='./data')
    p.add_argument('--q', type=str, default='booking')
    p.add_argument('--iters', type=int, default=50)
    args = p.parse_args()

    idx = ScreenshotIndexer(data_dir=Path(args.data))
    # Warmup
    idx.search(args.q, k=20)
    latencies = []
    for _ in range(args.iters):
        t0 = time.perf_counter()
        idx.search(args.q, k=20)
        latencies.append((time.perf_counter() - t0) * 1000)
    latencies.sort()
    p50 = latencies[len(latencies)//2]
    p95 = latencies[int(len(latencies)*0.95)-1]
    print(f"N={len(idx.metas)} iters={args.iters} q='{args.q}' p50={p50:.1f}ms p95={p95:.1f}ms")


if __name__ == '__main__':
    main()


