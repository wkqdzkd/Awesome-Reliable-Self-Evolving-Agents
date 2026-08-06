## Summary

<!-- Briefly describe the catalog, data, or generator change. -->

## Pull-request checks

`README.md` is a generated file. Do **not** edit it directly. Update
`data/` (and overrides as needed) or `scripts/generate_docs.py`, then run:

```bash
python scripts/validate_catalog.py --report data/validation_report.json
python scripts/generate_docs.py
```

Confirm every item before requesting review:

- [ ] Identifiers are unique.
- [ ] Paper URLs are canonical and reachable.
- [ ] Code/project URLs are official or explicitly marked third-party.
- [ ] Classification rationale names the evolution target.
- [ ] Primary level and subcategory agree.
- [ ] Existing source counts and manuscript coverage do not regress.
- [ ] Generated documentation is up to date.
- [ ] No local file paths, private hosts, credentials, or unpublished identity-bearing metadata are introduced.

## Test plan

<!-- How did you validate the change locally? -->
