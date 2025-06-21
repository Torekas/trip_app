from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired, NumberRange

from flask_wtf.file import FileField, FileRequired, FileAllowed

class ItemForm(FlaskForm):
    category = StringField("Category", validators=[DataRequired()])
    item_name = StringField("Item Name", validators=[DataRequired()])
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField("Save")

class UploadForm(FlaskForm):
    file = FileField(
        "Excel file",
        validators=[
            FileRequired(),
            FileAllowed(["xls", "xlsx"], "Excel files only")
        ]
    )
    submit = SubmitField("Upload")
