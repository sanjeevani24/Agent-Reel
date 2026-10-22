# Prompts (versioned)

File name = `<agent>.<version>.md`. The version used is logged in `logs/run_log.jsonl`
(`prompt_version`). Change behaviour by adding `v2` files, never by silently editing `v1`.

| Agent | Current | Uses LLM in Milestone B |
|---|---|---|
| planner | v1 | yes |
| researcher | v1 | yes (only when source documents exist) |
| scriptwriter | v1 | yes |
| storyboarder | v1 | yes |
| critic | v1 | yes (claim review; deterministic checks run first) |
| asset_generator | - | no (deterministic placeholders; image prompts come from the storyboard) |
| editor | - | no (deterministic edit plan) |
