"""PhoWhisper (vinai, Vietnamese fine-tuned Whisper) on short source windows. Slow on CPU: run in background.
usage: python3 pho.py <model: medium|large> <src> t0-t1 [t0-t1 ...]"""
import sys, time, os; sys.path.insert(0, os.path.dirname(__file__)); import mms, torch
torch.set_num_threads(4)
from transformers import pipeline
p = pipeline('automatic-speech-recognition', model=f'vinai/PhoWhisper-{sys.argv[1]}', device='cpu')
for span in sys.argv[3:]:
    t0, t1 = map(float, span.split('-')); w = mms.load16k(sys.argv[2], t0, t1 - t0); s = time.time()
    r = p({'raw': w, 'sampling_rate': 16000}, generate_kwargs={'language': 'vi', 'task': 'transcribe', 'max_new_tokens': 100})['text']
    print(f'{os.path.basename(sys.argv[2])} {t0}-{t1}: {r} ({time.time() - s:.0f}s)', flush=True)
