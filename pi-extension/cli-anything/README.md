# CLI-Anything Extension for Pi Coding Agent

This directory contains the Pi Coding Agent extension for CLI-Anything, enabling AI agents to build powerful, stateful CLI interfaces for any GUI application.

## Overview

The CLI-Anything Pi extension provides 5 slash commands that inject the HARNESS.md methodology and command specifications into the agent session. This enables the agent to build CLI harnesses for any software with a codebase.

## Installation

### Option 1: Global Install (Recommended)

Install the extension globally so `/cli-anything` commands are available in **all** Pi projects:

```bash
cd CLI-Anything/.pi-extension/extensions/cli-anything
bash install.sh
```

To uninstall:

```bash
bash install.sh --uninstall
```

### Option 2: Project-Local

Pi auto-discovers extensions in `.pi-extension/extensions/` within a project. If you're working inside the CLI-Anything repo, the extension is already active — no installation needed.

### Verify

After installing, run `/reload` in Pi or restart Pi. Then type `/cli-anything` to verify the command is available.

## Commands

| Command | Description |
|---------|-------------|
| `/cli-anything <path-or-repo>` | Build a complete CLI harness for any GUI application |
| `/cli-anything:refine <path> [focus]` | Refine an existing CLI harness to improve coverage |
| `/cli-anything:test <path-or-repo>` | Run tests for a CLI harness and update TEST.md |
| `/cli-anything:validate <path-or-repo>` | Validate a CLI harness against HARNESS.md standards |
| `/cli-anything:list [options]` | List all CLI-Anything tools (installed and generated) |

## Usage Examples

### Build a CLI for GIMP

```
/cli-anything ./gimp
```

### Build from a GitHub repository

```
/cli-anything https://github.com/blender/blender
```

### Refine an existing harness

```
/cli-anything:refine ./gimp "batch processing and filters"
```

### List all installed CLIs

```
/cli-anything:list
```

## Extension Structure

```
.pi-extension/extensions/cli-anything/
├── index.ts                    # Main extension entry point
├── README.md                   # This file
├── commands/                   # Command specifications
│   ├── cli-anything.md         # Main build command
│   ├── refine.md               # Refinement command
│   ├── test.md                 # Test runner command
│   ├── validate.md             # Validation command
│   └── list.md                 # List tools command
├── guides/                     # Detailed implementation guides
│   ├── filter-translation.md
│   ├── mcp-backend.md
│   ├── pypi-publishing.md
│   ├── session-locking.md
│   ├── skill-generation.md
│   └── timecode-precision.md
├── scripts/                    # Utility scripts
│   └── skill_generator.py      # SKILL.md generator
├── templates/                  # Templates
│   └── SKILL.md.template       # Skill definition template
└── tests/                      # Test suite
    ├── test_extension.test.ts  # Command registration tests
    └── test_skill_generator.py # Skill generator tests
```

> **Note:** HARNESS.md is NOT duplicated here. The extension reads it directly
> from `cli-anything-plugin/HARNESS.md` (canonical source) using a relative path.
> When installed globally via `install.sh`, a copy is placed alongside the extension.

## How It Works

1. **Command Registration**: The extension registers 5 slash commands with Pi's Extension API
2. **Context Injection**: When a command is invoked, it reads HARNESS.md and the relevant command spec
3. **Message Construction**: Builds a comprehensive message with methodology, specs, and user arguments
4. **Agent Execution**: Injects the message into the agent session via `pi.sendUserMessage()`
5. **Path Remapping**: Automatically remaps container paths to local system paths

## Path Remapping

The extension handles path remapping between the containerized environment (referenced in HARNESS.md) and the local system:

| Container Path | Local Path |
|----------------|------------|
| `/root/cli-anything/<software>/` | Current working directory |
| `cli-anything-plugin/repl_skin.py` | Resolved from `cli-anything-plugin/` (single source of truth) |
| `~/.claude/plugins/cli-anything/` | `<extension>/` |

## Development

To modify or extend this extension:

1. Edit `index.ts` for command behavior changes
2. Edit files in `commands/` for command specification changes
3. Edit `cli-anything-plugin/HARNESS.md` for methodology changes (the canonical source)
4. Edit `guides/` for implementation guide changes

## Dependencies

- `@mariozechner/pi-coding-agent` - Pi Extension API
- Node.js built-in modules: `fs`, `path`, `url`

## License

MIT License - See the main CLI-Anything repository for full license details.

## See Also

- [CLI-Anything Main Repository](https://github.com/HKUDS/CLI-Anything)
- [CLI-Hub](https://hkuds.github.io/CLI-Anything/) - Browse all community CLIs
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - Contribution guidelines
