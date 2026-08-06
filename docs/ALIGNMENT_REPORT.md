# Manuscript Alignment Report

Generated: 2026-08-07

## Result

- Catalog validation: **PASS**
- Active manuscript references: **549/549**
- Taxonomy-figure representatives: **137/137**
- Detailed catalog entries retained: **612/618** (6 entries excluded)
- Unresolved active BibTeX keys: **0**
- Active keys missing from the catalog: **0**

The repository therefore covers every active citation in the compiled manuscript, including references that were cited in TeX but absent from the 618-entry detailed catalog.

## Source-set reconciliation

- The detailed catalog contributes 618 curated entries.
- 6 curated entries were excluded for failing the inclusion criteria: a benchmark, position, or theory paper that implements no self-evolving system, or a subject outside an agent changing its own output, model, scaffold, updater, or criterion. Each exclusion is recorded with its evidence in `data/exclusions.json`.
- 95 active manuscript references were added because they were absent from that detailed catalog.
- 3 catalog-only works were added under the same taxonomy, including post-cutoff papers and one recovered identity split.
- 8 curated records had metadata reconciled against the manuscript, covering identifier collisions and preprint identities that a published record has since superseded.
- 7 published records merged into the curated preprint entry through a declared identity alias, so the manuscript's published citation and the catalog's preprint entry remain one work.
- 14 stale detailed-catalog placements were reconciled against the active chapter text and taxonomy figure.
- 1 work is cited under a BibTeX key that differs from the key matched by the detailed catalog; each is stored once under its canonical identifier, with 1 additional key folded in during import.
- 4 detailed-catalog works have no matching entry in the manuscript BibTeX library and remain cataloged from their verified paper records: `arxiv:2511.02805`, `arxiv:2512.17102`, `arxiv:2601.21464`, `arxiv:2603.28386`.

## Taxonomy lock

The machine-readable hierarchy mirrors the manuscript chapter structure:

- L0 (Output-Level Self-Evolution): task-local boundary and persistence, iterative revision, search, verification, and acceptance, reliability and the persistence limit.
- L1 (Model-Level Self-Evolution): definition and update boundary, single-model self-training, competitive self-play, cooperative co-evolution, reliability and the fixed-scaffold limit.
- L2 (Scaffold-Level Self-Evolution): definition and the scaffold boundary, prompts and programs, architecture and workflows, skills and experience, memory and retrieval, runtime harness, reliability and the fixed-improver limit.
- L3 (Improver-Level Self-Evolution): definition and the improver boundary, self-referential agents, learning better improvement strategies, reliability and the fixed-criterion limit.
- L4 (Criterion-Level Self-Evolution): definition and the criterion boundary, evolving evaluation mechanisms, evolving evaluation tasks and objectives, reliability with the criterion inside the loop.

The detailed catalog was curated under the manuscript's earlier L0-L4 numbering and its earlier subsection structure; the importer crosswalks those headings onto the taxonomy above rather than re-curating each entry.

Primary level follows the deepest demonstrated active rewrite. A citation in another level's discussion does not silently change its primary classification; such appearances are retained as manuscript memberships.

## Reconciled placements

- Agent0: Agent0: Unleashing Self-Evolving Agents from Zero Data via Tool-Integrated Reasoning — `L4` → `L1` (`facing`)
- CoEvolve: CoEvolve: Training LLM Agents via Agent-Data Mutual Evolution — `L2` → `L1` (`mixed`)
- DEI: Diversity in Evolutionary Inference for Quality-Diversity Search — `L3` → `L2` (`strict`)
- DataEvolver (T2I): Self-Evolving Multi-Agent Data Construction for Text-Rich Image Generation — `L4` → `L2` (`facing`)
- DataEvolver: Automatic Data Preparation for Large Language Models through Multi-Level Self-Evolving — `L1` → `L2` (`strict`)
- Eureka（Feature Engineering）: Eureka: Intelligent Feature Engineering for Enterprise AI Cloud Resource Demand Prediction — `L3` → `L2` (`boundary`)
- EvoTrainer: Co-Evolving LLM Policies and Training Harnesses for Autonomous Agentic Reinforcement Learning — `L2` → `L3` (`mixed`)
- Evolutionary Ensemble of Agents: Evolutionary Ensemble of Agents — `L3` → `L2` (`boundary`)
- Free Geometry: Refining 3D Reconstruction from Longer Versions of Itself — `L0` → `L1` (`boundary`)
- MetaEvo: A Meta-Optimization Framework for Experience-Driven Agent Evolution — `L3` → `L1` (`boundary`)
- MileStone: MileStone: A Multi-Objective Compiler Phase Ordering Framework for Graph-based IR-Level Optimization — `L3` → `L2` (`mixed`)
- ReGuide: From Test-Time Guidance to Self-Improving Diffusion Policies — `L0` → `L1` (`boundary`)
- STC: STC: Reversible Digit-Context Decomposition for BWT-Family Text Compression — `L3` → `L2` (`boundary`)
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

The manifest stores SHA-256 hashes for the source bibliography and every TeX section. Re-running the importer after a manuscript edit makes taxonomy or citation drift visible.

Validation command:

```bash
python scripts/validate_catalog.py --report data/validation_report.json
```
