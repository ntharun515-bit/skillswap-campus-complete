"""Fix invalid HTML tag name in generated files. Run: python scripts/fix_tags.py"""
import os

TAG = "m" + "o" + "t" + "i" + "o" + "n" + "l" + "e" + "s" + "s"
ROOT = os.path.join(os.path.dirname(__file__), "..")

for dp, _, files in os.walk(ROOT):
    for name in files:
        if not name.endswith((".html", ".js")):
            continue
        path = os.path.join(dp, name)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        if TAG not in text:
            continue
        text = text.replace(f"<{TAG}", "<div").replace(f"</{TAG}>", "</div>")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print("Fixed:", path)

print("Done.")
