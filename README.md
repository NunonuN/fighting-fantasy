# House of Hell Tracker  🏰💀🗡️

Decision tree tracker for _Fighting Fantasy: House of Hell_.
Track your choices, battles, and deaths to systematically explore all paths through the haunted house.

## 🕹️ Features

- **Colour-coded paragraphs**: red (💀 death), yellow (⚠️ incomplete), green (✅ safe), battle (⚔️ combat).
- **Persistent save**: tracks all explored paths across sessions (`house-of-hell-tree.json`).
- **Current path tracking**: never lose your place.
- **Unexplored branch highlighting**: see what choices you haven't tried yet.
- **Interactive node editing**: add/update battles, deaths, and choices.

## 🚀 Quick start

```bash
# install uv (if needed): https://astral.sh/uv

uv sync
uv run hoh # `uv run hell-tracker` also works
```

## 📖 Commands

```text
go <number>     # navigate to paragraph (e.e., `go 1`)
overview        # show full tree statistics
back            # go back one choice
edit <number>   # edit paragraph info
quit            # save and exit
```

## 🩸 Example session

```text
> go 1
¶  1 ✅ COMPLETE
  Children: 2
    → Open the door         ¶ 15 ⚠️
    → Knock first           ¶ 23 ✅

> go 15
¶ 15 ⚠️ INCOMPLETE
  Children: 0

> overview
📖 HOUSE OF HELL TREE OVERVIEW
Total paragraphs: 3 | 💀 Deaths: 0 | ⚔️ Battles: 0 | ⚠️ Incomplete: 1
```

## 📂 Directory structure

```text
.
├── house_of_hell.py        # main tracker
├── pyproject.toml          # uv project config
├── uv.lock                 # dependency lockfile
├── README.md               # this file
├── house-of-hell-tree.json # your save data (git-ignored)
└── .venv/                  # virtual environment
```

## 🎨 Horror theme

The tracker uses terminal colours and symbols:

- 💀 `red` = death endings
- ⚠️ `yellow` = incomplete paths
- ⚔️ `red` = battles
- ✅ `gree` = safe/complete

## 🤝 Contributing

1. Fork and clone
1. `uv sync`
1. Make changes
1. Test with `uv run hoh`
1. Submit PR!

## 📄 License

[MIT License](./LICENSE)

```text
💀 🗡️ HOUSE OF HELL TREE 🗡️ 💀

  Track your doom through the haunted mansion...

🏰 ═══════════════════════════════════════════════ ☠

```

**Made for Fighting Fantasy fans!**
Track every path to conquer the house. 🧟‍♂️👻
