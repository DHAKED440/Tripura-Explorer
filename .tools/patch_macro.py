import io, pathlib
old = '{% from "partials/_place_card.html" import place_card %}'
new = '{% from "partials/_place_card.html" import place_card with context %}'
count = 0
for path in pathlib.Path("app/templates").rglob("*.html"):
    text = io.open(path, encoding="utf-8").read()
    if old in text:
        io.open(path, "w", encoding="utf-8", newline="\n").write(text.replace(old, new))
        count += 1
        print("patched", path)
print("files patched:", count)
