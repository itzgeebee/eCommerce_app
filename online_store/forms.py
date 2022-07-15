from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, \
    SelectField, IntegerField, URLField, HiddenField
from wtforms.validators import DataRequired, URL, Length, NumberRange, Email


class CreateUserForm(FlaskForm):
    email = EmailField("",validators=[DataRequired(), Email()],
                       render_kw={"placeholder": "Email"})
    password = PasswordField("",validators=[DataRequired(),
                                         Length(min=6, max=30)],
                             id="password_field", render_kw={"placeholder": "Password"})
    confirm_password = PasswordField("",validators=[DataRequired(),
                                                 Length(min=6, max=25)],
                                     render_kw={"placeholder": "Confirm Password"})
    first_name = StringField("",validators=[DataRequired(), Length(min=2)],
                             render_kw={"placeholder": "First Name"})
    last_name = StringField("",validators=[DataRequired(),
                                        Length(min=2)],
                            render_kw={"placeholder": "Last Name"})
    street = StringField("",validators=[DataRequired(),
                                     Length(min=2)],
                         render_kw={"placeholder": "Street"})
    city = StringField("",validators=[DataRequired(),
                                   Length(min=2)],
                       render_kw={"placeholder": "City"})
    zip = StringField("",validators=[DataRequired(),
                                         Length(min=2, max=8)],
                      render_kw={"placeholder":"Zip"})
    phone = StringField("",validators=[DataRequired(),
                                             Length(min=2, max=12)],
                        render_kw={"placeholder":"Phone"})
    submit = SubmitField("Register",  render_kw={"class":"buttons"})


class LoginUserForm(FlaskForm):
    email = EmailField("",validators=[DataRequired(), Email()],
                       render_kw={"placeholder": "Email"})
    password = PasswordField("",validators=[DataRequired()],
                             render_kw={"placeholder": "Password"})
    submit = SubmitField("Sign in", render_kw={"class": "buttons"})


class ChangePassword(FlaskForm):
    old_password = PasswordField("Old Password", validators=[DataRequired()])
    new_password = PasswordField("New  Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired()])
    submit = SubmitField("Submit", render_kw={"class":"buttons"})


class ResetPassword(FlaskForm):
    new_password = PasswordField("New  Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired()])
    submit = SubmitField("Submit", render_kw={"class":"buttons"})


class EditUserForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    first_name = StringField("First Name", validators=[DataRequired(), Length(min=2)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(min=2)])
    street = StringField("Street", validators=[DataRequired(), Length(min=2)])
    city = StringField("City", validators=[DataRequired(), Length(min=2)])
    zip = StringField("Zip", validators=[DataRequired(), Length(min=2, max=8)])
    phone = StringField("Phone", validators=[DataRequired(), Length(min=2, max=12)])
    submit = SubmitField("Submit")


class UploadForm(FlaskForm):
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1)], default=100)
    product_name = StringField("Product name", validators=[DataRequired()])
    product_description = StringField("Description", validators=[DataRequired()])
    category = SelectField("Category", choices=["Phone", "Laptop"], validators=[DataRequired()])
    price = IntegerField("Price", validators=[DataRequired()])
    img_url = URLField("Image url", validators=[DataRequired()])
    submit = SubmitField("Submit", render_kw={"class":"buttons"})
