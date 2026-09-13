"""RNAddress-Mechanism-v5.

Two previously untried arms, chosen from measured evidence rather than guessed:

  A  cross-gene edit-direction transfer on the broad source (166 genes), using
     deliberately LOW-capacity delta features because v4 measured that high
     capacity transferred 0.055 auROC worse than plain composition.

  B  cross-source finite difference: train an absolute-localization model where
     reliability is 0.88, then score f(mutant) - f(parent) in a different
     assay and cell type. This is the RNAddress construction itself.

Astrocyte remains sealed. No loader exists here.
"""
