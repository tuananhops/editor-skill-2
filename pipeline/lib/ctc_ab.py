"""A/B test candidate transcripts on a source-audio window with MMS CTC (higher = better).
usage: python3 ctc_ab.py <audio> <t0> <t1> "cand a" "cand b" ..."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__)); import mms
a = sys.argv[1]; t0, t1 = float(sys.argv[2]), float(sys.argv[3]); w = mms.load16k(a, t0, t1 - t0)
for c in sys.argv[4:]: print(f'  {mms.ctc_score(w, c):7.3f}  {c}')
