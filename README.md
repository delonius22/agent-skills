# Agent Skills

My personal collection of agent skills. Each skill follows the open [Agent Skills](https://agentskills.io) format: a folder with a `SKILL.md` (YAML frontmatter plus Markdown instructions) and optional `references/`, `scripts/`, and `assets/` folders. Any agent that supports the format can load them, and any agent that can read files can follow them.

## Skills

| Skill | What it does |
|---|---|
| [first-principles-tutor](skills/first-principles-tutor/SKILL.md) | Turns any codebase, system, paper, equation, or idea into a Socratic course built on first principles. It measures what you already know, teaches one checked step at a time, runs separate practice sessions for cold recall, and has `/exam`, `/check`, `/listen`, and `/diagnose` modes. It can use sub-agents for research, problem-setting, blind grading, critique, and fact-checking, and works without them. |

## Layout

```
skills/
└── <skill-name>/          folder name must equal the `name` field in SKILL.md
    ├── SKILL.md           entry point the agent reads first
    └── references/        loaded only when SKILL.md points to them
```

## Installing a skill

Copy (or symlink) the skill folder into the directory your agent scans. Symlinking means a `git pull` updates every agent at once.

| Agent | Project-level | User-level (all projects) |
|---|---|---|
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| OpenAI Codex CLI | `.agents/skills/` | `~/.agents/skills/` |
| Cursor | `.agents/skills/`, `.cursor/skills/`, or `.claude/skills/` | see Cursor's docs |
| Gemini CLI, VS Code Copilot, others | `.agents/skills/` is the shared convention | see the tool's docs |
| Claude apps (web, desktop) | Zip the skill folder and upload it in the skills settings | |

Example (Linux or macOS, user-level, symlinked):

```bash
git clone https://github.com/<you>/agent-skills.git ~/agent-skills
mkdir -p ~/.claude/skills ~/.agents/skills
ln -s ~/agent-skills/skills/first-principles-tutor ~/.claude/skills/first-principles-tutor
ln -s ~/agent-skills/skills/first-principles-tutor ~/.agents/skills/first-principles-tutor
```

**Agents without skill support.** Point the agent at the file ("Read `skills/first-principles-tutor/SKILL.md` and follow it"), or paste `SKILL.md` into the system prompt. The `references/` files only load if the agent can read files; otherwise paste the ones a session needs.

## Adding a new skill

1. Create `skills/<skill-name>/SKILL.md`. Use lowercase letters, numbers, and single hyphens for the name, and make it match the folder name.
2. Write a `description` (1,024 characters or fewer) that says what the skill does *and* the phrases that should trigger it. Agents decide whether to load a skill from this field alone.
3. Keep `SKILL.md` under about 500 lines. Move detail into `references/`.
4. Validate: `npx skills-ref validate ./skills/<skill-name>`
5. Add a row to the table above.

## License

No license is set yet. Until one is added, the default is all rights reserved. Add a `LICENSE` file if you want others to reuse these.
