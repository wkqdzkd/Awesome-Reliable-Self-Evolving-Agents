# Manuscript Alignment Report

Generated: 2026-08-07

## Result

- Catalog validation: **PASS**
- Active manuscript references: **549/549**
- Taxonomy-figure representatives: **137/137**
- Repository paper records: **549**
- Unresolved active BibTeX keys: **0**
- Active keys missing from the catalog: **0**

The repository contains exactly the papers used by the compiled manuscript: one canonical record for each active BibTeX key and no catalog-only papers.

## Membership policy

- `data/manuscript_manifest.json` declares 549 active BibTeX keys.
- `data/papers.json` stores 549 active manuscript records.
- Validation rejects any record whose `manuscript.active` flag is false.
- A paper must first become an active manuscript citation before it can enter the repository catalog.
- 4 source placements were reconciled against the active chapter text and taxonomy figure.
- 1 work is stored under a canonical identifier while preserving a legacy BibTeX alias.

## Taxonomy lock

The machine-readable hierarchy mirrors the manuscript chapter structure:

- L0 (Output-Level Self-Evolution): task-local boundary and persistence, iterative revision, search, verification, and acceptance, reliability and the persistence limit.
- L1 (Model-Level Self-Evolution): definition and update boundary, single-model self-training, competitive self-play, cooperative co-evolution, reliability and the fixed-scaffold limit.
- L2 (Scaffold-Level Self-Evolution): definition and the scaffold boundary, prompts and programs, architecture and workflows, skills and experience, memory and retrieval, runtime harness, reliability and the fixed-improver limit.
- L3 (Improver-Level Self-Evolution): definition and the improver boundary, self-referential agents, learning better improvement strategies, reliability and the fixed-criterion limit.
- L4 (Criterion-Level Self-Evolution): definition and the criterion boundary, evolving evaluation mechanisms, evolving evaluation tasks and objectives, reliability with the criterion inside the loop.

Primary level follows the deepest demonstrated active rewrite. A citation in another level's discussion does not silently change its primary classification; such appearances are retained as manuscript memberships.

## Reconciled placements

- CoEvolve: CoEvolve: Training LLM Agents via Agent-Data Mutual Evolution — `L2` → `L1` (`mixed`)
- DataEvolver: Automatic Data Preparation for Large Language Models through Multi-Level Self-Evolving — `L1` → `L2` (`strict`)
- EvoTrainer: Co-Evolving LLM Policies and Training Harnesses for Autonomous Agentic Reinforcement Learning — `L2` → `L3` (`mixed`)
- SePO: SePO: Self-Evolving Prompt Agent for System Prompt Optimization — `L2` → `L3` (`mixed`)

A `mixed` record preserves every update path the manuscript attributes to a system instead of silently choosing one and discarding the others.

## Cross-level discussion memberships

13 works are intentionally discussed in a core level other than their primary level. These are not alignment errors; they include criterion-facing curricula, mixed update paths, and explicit boundary cases.

- `chenEvoTrainerCoEvolvingLLM2026` — EvoTrainer: Co-Evolving LLM Policies and Training Harnesses for Autonomous Agentic Reinforcement Learning — primary `L3`, discussed in `L2`, `L3`
- `dengDataEvolverAutomaticData2026` — DataEvolver: Automatic Data Preparation for Large Language Models through Multi-Level Self-Evolving — primary `L2`, discussed in `L1`
- `guanEvoRubricSelfEvolvingRubricDriven2026` — EvoRubric: EvoRubric: Self-Evolving Rubric-Driven RL for Open-Ended Generation — primary `L4`, discussed in `L3`, `L4`
- `heLearningEvolveSelfImproving2026` — Learning to Evolve: A Self-Improving Framework for Multi-Agent Systems via Textual Parameter Graph Optimization — primary `L2`, discussed in `L2`, `L3`
- `huangBootstrappingPosttrainingSignals2026` — Rubric-based Self-play: Bootstrapping Post-training Signals for Open-ended Tasks via Rubric-based Self-play on Pre-training Text — primary `L1`, discussed in `L3`
- `liCPMobiusIterativeCoachPlayer2026` — CPMobius: CPMöbius: Iterative Coach–Player Reasoning for Data-Free Reinforcement Learning — primary `L1`, discussed in `L3`
- `lingPACETwoTimescaleSelfEvolution2026` — PACE: Two-Timescale Self-Evolution for Small Language Model Agents — primary `L2`, discussed in `L2`, `L3`
- `taoSePOSelfEvolvingPrompt2026` — SePO: SePO: Self-Evolving Prompt Agent for System Prompt Optimization — primary `L3`, discussed in `L2`, `L3`
- `yangCoEvolveTrainingLLM2026` — CoEvolve: CoEvolve: Training LLM Agents via Agent-Data Mutual Evolution — primary `L1`, discussed in `L2`
- `yeMetaContextEngineering2026` — MCE (Meta Context Engineering): Meta Context Engineering via Agentic Skill Evolution — primary `L2`, discussed in `L2`, `L3`
- `zhangCoEvoSkillsSelfEvolvingAgent2026` — CoEvoSkills: Self-Evolving Agent Skills via Co-Evolutionary Verification — primary `L2`, discussed in `L2`, `L4`
- `zhangSeirenesAdversarialSelfPlay2026` — Seirênes: Seirênes: Adversarial Self-Play with Evolving Distractions for LLM Reasoning — primary `L1`, discussed in `L3`
- `zhaoMAESTROMetalearningAdaptive2026` — MAESTRO: Meta-learning Adaptive Estimation of Scalarization Trade-offs for Reward Optimization — primary `L1`, discussed in `L1`, `L4`

## Reproducibility

The manifest stores SHA-256 hashes for the source bibliography and every TeX section. Validation also requires the catalog to match the active citation set exactly, making additions, removals, taxonomy changes, or citation drift visible.

Validation command:

```bash
python scripts/validate_catalog.py --report data/validation_report.json
```
