import io
path = "app/forms.py"
text = io.open(path, encoding="utf-8").read()
addition = '''

def coerce_optional_int(value):
    """Coerce an optional numeric select value; blank means None."""
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.lower() in {"none", "null"}:
        return None
    try:
        return int(text)
    except (TypeError, ValueError):
        return None
'''
anchor = 'class RegistrationForm(FlaskForm):'
assert anchor in text
text = text.replace(anchor, addition.strip() + "\n\n\n" + anchor, 1)
text = text.replace('district_id = SelectField("District", coerce=int, validators=[Optional()])\n    locality = StringField("Locality", validators=[Optional(), Length(max=160)])\n    address = StringField("Address / landmark"',
                    'district_id = SelectField("District", coerce=coerce_optional_int, validators=[Optional()])\n    locality = StringField("Locality", validators=[Optional(), Length(max=160)])\n    address = StringField("Address / landmark"', 1)
text = text.replace('district_id = SelectField("District", coerce=int, validators=[Optional()])\n    short_description',
                    'district_id = SelectField("District", coerce=coerce_optional_int, validators=[Optional()])\n    short_description', 1)
io.open(path, "w", encoding="utf-8", newline="\n").write(text)
print(text.count("coerce=coerce_optional_int"), "district fields patched")
