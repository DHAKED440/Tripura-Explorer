import io
path = "app/routes/admin.py"
text = io.open(path, encoding="utf-8").read()
old = '    return render_template("admin/categories.html", categories=Category.query.order_by(Category.name.asc()).all())'
new = '''    return render_template(
        "admin/categories.html",
        categories=Category.query.order_by(Category.name.asc()).all(),
        districts=District.query.order_by(District.name.asc()).all(),
    )'''
assert old in text
text = text.replace(old, new, 1)
io.open(path, "w", encoding="utf-8", newline="\n").write(text)
print("categories route patched")
