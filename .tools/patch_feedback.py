import io
path = "app/models/feedback.py"
text = io.open(path, encoding="utf-8").read()
anchor = 'CORRECTION_STATUSES = ["new", "reviewing", "resolved", "rejected"]\n'
addition = anchor + '''

def utcnow() -> datetime:
    """Timezone aware ``now`` used by the default timestamp columns."""
    return datetime.now(timezone.utc)
'''
assert anchor in text and "def utcnow" not in text
text = text.replace(anchor, addition, 1)
io.open(path, "w", encoding="utf-8", newline="\n").write(text)
print("feedback utcnow added")
