import os

# Map your existing hardcoded colors directly to the new CSS variables
replacements = {
    "#0f172a": "var(--bg-color)",
    "#1e293b": "var(--bg-panel)",
    "#334155": "var(--border-color)",
    "#f8fafc": "var(--text-primary)",
    "#cbd5e1": "var(--text-secondary)",
    "#94a3b8": "var(--text-muted)",
    "#22d3ee": "var(--accent)"
}

for root, _, files in os.walk('frontend/src'):
    for file in files:
        if file.endswith('.jsx'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()

            for old, new in replacements.items():
                content = content.replace(old, new)

            with open(path, 'w') as f:
                f.write(content)

print("Theme tokens instantly mapped across all React components!")
