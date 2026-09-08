-- Personal Hyprland layer, symlinked here by omarchy/install.py.
--
-- Omarchy's own defaults, and anything you put in ~/.config/hypr/bindings.lua
-- by hand, both still apply: hyprland.lua requires this module after those, so
-- it only adds to them. Keep it to things the dotfiles themselves install —
-- Omarchy already binds the terminal, browser, editor, file manager, herdr,
-- tmux and 1Password, and duplicating those here would just fight the next
-- Omarchy release.

-- Transcript search across every coding agent on this machine (memex topic).
o.bind("SUPER + SHIFT + CTRL + M", "Memex", { tui = "memex", focus = true })

-- Past Claude Code sessions (claude topic).
o.bind("SUPER + SHIFT + CTRL + H", "Claude history", { tui = "claude-history", focus = true })
