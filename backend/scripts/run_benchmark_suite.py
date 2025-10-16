import argparse
import subprocess
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=str, default='./data')
    p.add_argument('--n', type=int, default=5000)
    p.add_argument('--recipes', type=int, default=800)
    p.add_argument('--presentations', type=int, default=800)
    p.add_argument('--dogs', type=int, default=400)
    p.add_argument('--code', type=int, default=300)
    p.add_argument('--maps', type=int, default=300)
    p.add_argument('--chats', type=int, default=300)
    p.add_argument('--iters', type=int, default=100)
    args = p.parse_args()

    # 1) Generate synthetic corpus
    gen_cmd = [
        sys.executable,
        'backend/scripts/generate_synthetic.py',
        '--out', args.out,
        '--n', str(args.n),
        '--recipes', str(args.recipes),
        '--presentations', str(args.presentations),
        '--dogs', str(args.dogs),
        '--code', str(args.code),
        '--maps', str(args.maps),
        '--chats', str(args.chats),
    ]
    print('Running:', ' '.join(gen_cmd))
    subprocess.check_call(gen_cmd)

    # 2) Benchmarks
    queries = ['recipe', 'presentation advice', 'funny dog']
    for q in queries:
        bench_cmd = [
            sys.executable,
            'backend/scripts/benchmark_search.py',
            '--data', args.out,
            '--q', q,
            '--iters', str(args.iters),
        ]
        print('Running:', ' '.join(bench_cmd))
        subprocess.check_call(bench_cmd)


if __name__ == '__main__':
    main()


