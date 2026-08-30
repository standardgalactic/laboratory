# Flyxion headless repository experiments

Sixteen deterministic Blender scenes that turn repository concepts into inspectable
geometry. They target Blender 4.0+ and automatically select the installed Eevee
identifier. No external assets or add-ons are required.

```bash
bash render_all.sh output
```

Render one experiment with:

```bash
blender -b --python-exit-code 1 -P experiments/calculus_orthodromes.py -- --output output
```

Every script accepts `--output`, `--resolution WIDTHxHEIGHT`, `--samples`,
`--seed`, `--engine AUTO|BLENDER_EEVEE|BLENDER_EEVEE_NEXT|CYCLES`, and
`--no-render`. Each writes a PNG and a reusable `.blend` file.

The scenes are deliberately structural: geometry represents an operation,
constraint, trajectory, or measurable relation rather than serving as decoration.

The included experiments are:

| Repository | Script | Structural question |
| --- | --- | --- |
| calculus | `calculus_orthodromes.py` | How do orthodromic frames intersect a libration envelope? |
| TARTAN | `tartan_constraint_closure.py` | Can a locally plausible obstruction be reconciled into global closure? |
| HYDRA | `hydra_phase_locking.py` | Which trajectories converge within a persona and which couple across personas? |
| autogenerative-dynamics | `autogenerative_repair.py` | How does recursive growth route around a deleted region? |
| cliodynamics | `cliodynamics_aliasing.py` | When does one projection hide states requiring different continuations? |
| spherepop | `spherepop_logic.py` | How do Bind, Refuse, and Pop execute the four Boolean input cases? |
| Chloroplasts | `chloroplast_light_capture.py` | How do incidence angle and membrane stacking alter light paths? |
| alphabet | `alphabet_fibered_dsl.py` | Where can local DSL transport proceed, and where is it obstructed? |

## Volume II

| Repository | Script | Structural question |
| --- | --- | --- |
| calculus | `calculus_spherical_voronoi.py` | How do weighted service hubs induce a secondary spherical network? |
| TARTAN | `tartan_annotated_fracture.py` | How does trajectory-conditioned tiling respond to an annotated fracture? |
| HYDRA | `hydra_recursive_veiling.py` | Which parts of a signal remain recoverable through nested veils? |
| autogenerative-dynamics | `autogenerative_worldlines.py` | Which candidate histories survive spatial constraints? |
| cliodynamics | `cliodynamics_recoverability.py` | Which retained events remain recoverable to each participant? |
| spherepop | `spherepop_deferred_closure.py` | How does a pending token cross scopes before Collapse? |
| Chloroplasts | `chloroplast_proton_gradient.py` | How does a stored gradient route through rotary transport? |
| alphabet | `alphabet_semantic_holonomy.py` | What residual remains after semantic transport around a DSL loop? |
