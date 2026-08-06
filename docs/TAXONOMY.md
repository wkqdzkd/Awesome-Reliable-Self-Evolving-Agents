# L0-L4 Taxonomy

This repository follows the survey's **active semantic rewrite depth** taxonomy.
A level is determined by the deepest object whose changed state remains
causally active, not by an algorithm name, training stage, number of agents, or
runtime components.

## Classification rules

1. **Classify the transition, then the system.** A realized transition is
   assigned the deepest level it actually changes. System capability records
   the deepest reachable transition; a no-op round does not lower capability.
2. **Classify the rewritten object.** Using RL does not automatically imply
   L1, and using a meta-agent does not automatically imply L3. The retained
   object changed by the update is decisive.
3. **Separate training from judgment.** Data that train model parameters are
   L1. A promoted curriculum that governs later updates belongs to the updater
   side of the loop. Tasks, rewards, evaluators, or constraints that change
   future judgments reach L4.

Storage alone is not persistence. Logs, dead code, unused memory, or an
uncommitted candidate do not raise a system's level unless they change later
behavior or updating.

## L0 — Output-Level Self-Evolution

The system rewrites only the current task output. Its retained model, scaffold,
updater, and criterion remain semantically unchanged on later independent
tasks.

- Task-local boundary and persistence
- Iterative revision
- Search, verification, and acceptance
- Reliability and the persistence limit

Typical external evidence includes executable tests, formal checks, or human
review of the current answer. The characteristic failure is self-confirmation.

## L1 — Model-Level Self-Evolution

The system persistently changes trainable model state, a learned policy or
judge, or active data that later changes those parameters.

- Definition and update boundary
- Single-model self-training
- Competitive self-play
- Cooperative co-evolution
- Reliability and the fixed-scaffold limit

The scaffold, updater, and criterion remain fixed at this level. Characteristic
failures include collapse, drift, and forgetting.

## L2 — Scaffold-Level Self-Evolution

The system persistently changes the nonparametric harness around the model:
prompts, tools, memory operations, workflows, interfaces, permissions, runtime
control, executable code, reusable skills, or active runtime memory.

- Definition and the scaffold boundary
- Prompts and programs
- Architecture and workflows
- Skills and experience
- Memory and retrieval
- Runtime harness
- Reliability and the fixed-improver limit

The updater and criterion remain fixed. Characteristic failures include
adaptive overfitting, memory pollution, and development-set leakage.

## L3 — Improver-Level Self-Evolution

The system changes the updater that proposes, selects, commits, rejects, or
rolls back future changes. A one-off scaffold edit remains L2 unless the edited
procedure governs subsequent updates.

- Definition and the improver boundary
- Self-referential agents
- Learning better improvement strategies
- Reliability and the fixed-criterion limit

The criterion remains fixed. The characteristic failure is metric capture:
lineages become good at surviving the updater's selection process without
necessarily improving under an independent target.

## L4 — Criterion-Level Self-Evolution

The system changes what future judgments mean through tasks, curricula,
rewards, evaluators, aggregation rules, constraints, or value semantics.

- Definition and the criterion boundary
- Evolving evaluation mechanisms
- Evolving evaluation tasks and objectives
- Reliability with the criterion inside the loop

The characteristic failure is criterion drift, also called the moving-ruler
problem. Trusted claims require an audit charter outside the writable causal
closure of the same update.

## Multi-level and boundary labels

- `strict`: directly demonstrates the retained rewrite semantics of its level.
- `facing`: the core update is shallower but the work approaches a deeper
  frontier, such as an adaptive curriculum discussed at L4.
- `mixed`: demonstrates multiple active update paths; the deepest demonstrated
  rewrite is primary.
- `boundary`: retained because it clarifies an inclusion or level boundary.
- `supporting`: contributes to positioning, evaluation, safety, or open
  problems rather than instantiating an L0-L4 transition.

One work has one primary level but may have multiple manuscript memberships.
This avoids duplicating a paper while preserving where and why the survey
discusses it.

## Numbering history

The five level names and their rewrite semantics have never changed; only the
numbers attached to them have.

- Up to 0.2.0, and again from 0.5.0 onward: **L0-L4**, matching the manuscript.
- From 0.3.0 to 0.4.1: **L1-L5**, following a manuscript revision that has since
  been reverted.

Because the numbering has moved twice, the importer no longer infers a level
from a chapter's filename. It reads the number out of each level chapter's own
`\section{L<n>: <Target>-Level Self-Evolution}` heading and refuses to run when
that disagrees with `data/taxonomy.json`. Renumbering is a curated change: it
rewrites public README anchors and every override keyed by subcategory, so it
should never happen as a silent side effect of a resync.
