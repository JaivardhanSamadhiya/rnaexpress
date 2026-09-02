# RNAddress v4 Phase B2 direction results

Definitive run date: 2026-09-01

| Direction | Within-source rank CV | Within-source regret CV | Leave-source-out regret CV | 2–10-nt regret CV | Units improved | Gate H |
|---|---:|---:|---:|---:|---:|---|
| Increase/enhancement | +0.0605 | +0.0295 | -0.0122 | -0.0223 | 44.60% | fail |
| Decrease/disruption | -0.0223 | -0.0273 | +0.0174 | +0.0203 | 46.48% | fail |

Increase provides the strongest within-source evidence that context matters, including positive Moffatt and TDP rank ContextValue and both reporter transfers. It reverses under leave-source-out and small edits.

Decrease provides consistent positive leave-source-out regret ContextValue on all three held sources and positive 2–10-nt regret ContextValue. It is harmful within source on average, has negative rank ContextValue and improves fewer than half of units.

The two directions therefore exhibit complementary failure modes rather than one deployable direction. Neither passes Gate H, so Phase B2 does not justify RNAddress-Disrupt or a bidirectional compiler.
