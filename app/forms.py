"""WTForms definitions.

Flask-WTF gives every form CSRF protection and server side validation. The
admin forms use the same validators as the API so the rules cannot drift.
"""
from __future__ import annotations

import re

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, Regexp, ValidationError

from app.models.business import BUSINESS_CATEGORIES, BUSINESS_STATUSES

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_slug(form, field):
    if field.data and not SLUG_PATTERN.match(field.data.strip()):
        raise ValidationError("Use lowercase letters, numbers and single hyphens only (for example neermahal).")


def validate_latitude(form, field):
    if field.data is None:
        return
    if field.data < -90 or field.data > 90:
        raise ValidationError("Latitude must be between -90 and 90.")


def validate_longitude(form, field):
    if field.data is None:
        return
    if field.data < -180 or field.data > 180:
        raise ValidationError("Longitude must be between -180 and 180.")


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


class RegistrationForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email address", validators=[DataRequired(), Email(), Length(max=180)])
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128, message="Use at least 8 characters.")],
    )
    confirm_password = PasswordField(
        "Confirm password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email address", validators=[DataRequired(), Email(), Length(max=180)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Keep me signed in on this device")
    submit = SubmitField("Sign in")


class InquiryForm(FlaskForm):
    name = StringField("Your name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email address", validators=[DataRequired(), Email(), Length(max=180)])
    phone = StringField("Phone (optional)", validators=[Optional(), Length(max=40)])
    message = TextAreaField(
        "Message",
        validators=[DataRequired(), Length(min=10, max=1200, message="Please write at least 10 characters.")],
    )
    submit = SubmitField("Send inquiry")


class CorrectionForm(FlaskForm):
    message = TextAreaField(
        "What is incorrect or missing?",
        validators=[DataRequired(), Length(min=10, max=1200)],
    )
    reporter_email = StringField("Your email (optional)", validators=[Optional(), Email(), Length(max=180)])
    submit = SubmitField("Send report")


class PlaceForm(FlaskForm):
    """Admin form for destination records."""

    name = StringField("Destination name", validators=[DataRequired(), Length(max=160)])
    slug = StringField("URL slug", validators=[DataRequired(), Length(max=160), validate_slug])
    tagline = StringField("Tagline", validators=[Optional(), Length(max=200)])
    short_description = StringField("Short description (card)", validators=[Optional(), Length(max=300)])
    description = TextAreaField("Full description", validators=[Optional()])

    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    district_id = SelectField("District", coerce=coerce_optional_int, validators=[Optional()])
    locality = StringField("Locality", validators=[Optional(), Length(max=160)])
    address = StringField("Address / landmark", validators=[Optional(), Length(max=300)])

    latitude = DecimalField("Latitude", validators=[Optional(), validate_latitude], places=6)
    longitude = DecimalField("Longitude", validators=[Optional(), validate_longitude], places=6)
    coordinates_verified = BooleanField("Coordinates verified in the field")
    coordinate_source = StringField("Coordinate source", validators=[Optional(), Length(max=300)])

    image_url = StringField("Main image path or URL", validators=[Optional(), Length(max=400)])
    image_alt = StringField("Image alt text", validators=[Optional(), Length(max=300)])

    entry_fee_indian = StringField("Entry fee (Indian visitors)", validators=[Optional(), Length(max=120)])
    entry_fee_foreign = StringField("Entry fee (foreign visitors)", validators=[Optional(), Length(max=120)])
    opening_info = StringField("Opening hours", validators=[Optional(), Length(max=200)])
    closed_day = StringField("Closed day(s)", validators=[Optional(), Length(max=120)])
    best_season = StringField("Best season", validators=[Optional(), Length(max=160)])
    typical_visit_hours = DecimalField("Typical visit length (hours)", validators=[Optional(), NumberRange(min=0, max=24)], places=1)
    facilities = StringField("Facilities", validators=[Optional(), Length(max=300)])
    accessibility_info = StringField("Accessibility", validators=[Optional(), Length(max=300)])
    safety_notes = StringField("Safety notes", validators=[Optional(), Length(max=300)])
    contact_info = StringField("Contact information", validators=[Optional(), Length(max=200)])

    extra_tags = StringField("Secondary interests (comma separated)", validators=[Optional(), Length(max=200)])
    popularity = IntegerField("Popularity score (0-100)", validators=[Optional(), NumberRange(min=0, max=100)], default=0)

    is_published = BooleanField("Published (visible to visitors)")
    is_verified = BooleanField("Information verified by a named person")
    verified_by = StringField("Verified by", validators=[Optional(), Length(max=160)])
    last_verified_at = DateField("Last verified on", validators=[Optional()])
    verification_notes = TextAreaField("Verification notes", validators=[Optional()])
    source_note = TextAreaField("Source note", validators=[Optional()])

    submit = SubmitField("Save destination")

    def validate(self, extra_validators=None):  # type: ignore[override]
        valid = super().validate(extra_validators=extra_validators)
        # Either both coordinates are supplied or neither: a half-filled pair
        # would put the marker in the wrong place.
        lat_set = self.latitude.data is not None
        lng_set = self.longitude.data is not None
        if lat_set != lng_set:
            message = "Enter both latitude and longitude, or leave both empty."
            if not lat_set:
                self.latitude.errors.append(message)
            else:
                self.longitude.errors.append(message)
            valid = False
        if self.coordinates_verified.data and not (lat_set and lng_set):
            self.coordinates_verified.errors.append("Coordinates can only be marked verified when both values are present.")
            valid = False
        if self.is_verified.data and not (self.verified_by.data or "").strip():
            self.verified_by.errors.append("Record the name of the person who verified this information.")
            valid = False
        return valid


class BusinessForm(FlaskForm):
    """Admin form for local provider listings."""

    name = StringField("Provider name", validators=[DataRequired(), Length(max=160)])
    slug = StringField("URL slug", validators=[DataRequired(), Length(max=160), validate_slug])
    category = SelectField("Category", choices=[(value, value) for value in BUSINESS_CATEGORIES], validators=[DataRequired()])
    district_id = SelectField("District", coerce=coerce_optional_int, validators=[Optional()])
    short_description = StringField("Short description", validators=[Optional(), Length(max=300)])
    description = TextAreaField("Description", validators=[Optional()])
    locality = StringField("Locality", validators=[Optional(), Length(max=160)])
    address = StringField("Address", validators=[Optional(), Length(max=300)])
    contact_name = StringField("Contact person", validators=[Optional(), Length(max=160)])
    contact_phone = StringField("Contact phone", validators=[Optional(), Length(max=40)])
    contact_email = StringField("Contact email", validators=[Optional(), Email(), Length(max=180)])
    languages = StringField("Languages spoken", validators=[Optional(), Length(max=160)])
    price_note = StringField("Indicative price note", validators=[Optional(), Length(max=200)])
    image_url = StringField("Image path or URL", validators=[Optional(), Length(max=400)])
    image_alt = StringField("Image alt text", validators=[Optional(), Length(max=300)])
    approval_status = SelectField(
        "Approval status", choices=[(value, value.title()) for value in BUSINESS_STATUSES], validators=[DataRequired()]
    )
    status_note = StringField("Internal status note", validators=[Optional(), Length(max=300)])
    submit = SubmitField("Save provider")


class InquiryStatusForm(FlaskForm):
    status = SelectField("Status", choices=[("new", "New"), ("in_progress", "In progress"), ("closed", "Closed")])
    admin_note = StringField("Internal note", validators=[Optional(), Length(max=300)])
    submit = SubmitField("Update inquiry")


class CorrectionStatusForm(FlaskForm):
    status = SelectField(
        "Status",
        choices=[("new", "New"), ("reviewing", "Reviewing"), ("resolved", "Resolved"), ("rejected", "Rejected")],
    )
    admin_note = StringField("Internal note", validators=[Optional(), Length(max=300)])
    submit = SubmitField("Update report")


class ItinerarySettingsForm(FlaskForm):
    """Small form used on the saved-trip page to rename or re-plan a trip."""

    title = StringField("Trip title", validators=[DataRequired(), Length(max=160)])
    starting_location = StringField("Starting location", validators=[DataRequired(), Length(max=160)])
    duration_days = IntegerField("Days", validators=[DataRequired(), NumberRange(min=1, max=3)])
    budget = IntegerField("Budget (INR, optional)", validators=[Optional(), NumberRange(min=0)])
    travel_date = DateField("Travel date (optional)", validators=[Optional()])
    submit = SubmitField("Save changes")