# Contributing

Thank you for helping maintain Awesome Reliable Self-Evolving Agents.

## Suggest a paper

Open the paper-suggestion issue form or submit a pull request. Include:

- canonical title;
- arXiv, DOI, OpenReview, or proceedings URL;
- first public date and venue, if known;
- official code and project URLs, with evidence;
- proposed L0-L4 level and subcategory;
- one sentence identifying the deepest active evolution target;
- whether the update persists across independent tasks.

Do not infer an official repository from a matching name alone.

Rendered catalog entries use:

```text
- **`Venue Year`** Title. [[paper](URL)] [[code](URL)]
```

## Classification checklist

Before assigning a level, answer in order:

1. Does anything change? If no, it is supporting or out of scope.
2. Is the change limited to the current task output? If yes, L0.
3. Does it persist in trainable model state or L1 training data? If deepest,
   L1.
4. Does it persist in prompts, code, tools, workflows, skills, memory, or the
   runtime harness? If deepest, L2.
5. Does it change the procedure governing future updates? If yes, L3.
6. Does it change future tasks, rewards, evaluators, constraints, or value
   semantics? If yes, L4.

Use `facing`, `mixed`, or `boundary` when a single strict label would hide an
important distinction. See `docs/TAXONOMY.md`.

## Data changes

`README.md` is generated as a whole and must not be edited directly. Update the
canonical data for catalog changes or `scripts/generate_docs.py` for layout and
static content, then run:

```bash
python scripts/validate_catalog.py --report data/validation_report.json
python scripts/generate_docs.py
```

## Pull-request checks

- Identifiers are unique.
- Paper URLs are canonical and reachable.
- Code/project URLs are official or explicitly marked third-party.
- Classification rationale names the evolution target.
- Primary level and subcategory agree.
- Existing source counts and manuscript coverage do not regress.
- Generated documentation is up to date.
- No local file paths, private hosts, credentials, or unpublished
  identity-bearing metadata are introduced.

## Licensing

By contributing catalog data or documentation, you agree to license that
contribution under CC BY 4.0. By contributing scripts or workflow code, you
agree to license that contribution under MIT.
