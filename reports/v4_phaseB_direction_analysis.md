# RNAddress v4 Phase B direction analysis

## Within-source result

| Direction | Rank | Regret | Selected normalized utility | Good@1 | Good@3 | Good@5 |
|---|---:|---:|---:|---:|---:|---:|
| Decrease/disruption | 0.6565 | 0.3954 | 0.6046 | 0.0866 | 0.2740 | 0.3674 |
| Increase/enhancement | 0.5252 | 0.4576 | 0.5424 | 0.0910 | 0.1441 | 0.2228 |

## Transfer result

The decrease direction passes frozen Gate F: it passes within two sources and its equal-source leave-source-out aggregate is rank 0.5842 with random-regret gain 0.0505. Increase fails: only one within-source dataset passes, leave-source-out rank is 0.5139, and random-regret gain is 0.0309.

This asymmetry agrees with the development data's biological pattern that disrupting localization elements is easier than creating localization by motif insertion. It does not by itself authorize an asymmetric compiler because Gates A, B, C, E, and I independently fail. A future cycle should treat disruption as the leading hypothesis, not as a validated product scope.
