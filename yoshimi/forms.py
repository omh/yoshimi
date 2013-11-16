"""
    yoshimi.forms
    ~~~~~~~~~

    This module implements various forms based on WTForms.

    :copyright: (c) 2013 by Ole Morten Halvorsen
    :license: BSD, see LICENSE for more details.
"""
import hashlib
import pickle
from pyramid.httpexceptions import HTTPUnauthorized
from wtforms import Form
from wtforms.ext.csrf.form import SecureForm
from wtforms.ext.sqlalchemy.orm import model_form
from wtforms.fields import HiddenField
from wtforms.fields import PasswordField
from wtforms.fields import TextField
from wtforms.validators import DataRequired
from wtforms.validators import email
from wtforms.validators import required
from wtforms.validators import ValidationError
from yoshimi.content import Content


class BaseForm(Form):
    def render_hidden_tags(self):
        fields = [f for f in self if isinstance(f, HiddenField)]
        rv = []
        for field in fields:
            if isinstance(field, str):
                field = getattr(self, field)
            rv.append(str(field))
        return "".join(rv)


class CsrfForm(SecureForm, BaseForm):
    def __init__(self, *args, csrf_enabled=True, **kwargs):
        # Allow csrf_enabled to be set on the class. Useful for disabling it
        # csrf during testing.
        if not hasattr(self, 'csrf_enabled'):
            self.csrf_enabled = csrf_enabled
        super().__init__(*args, **kwargs)

    @classmethod
    def from_request(cls, request):
        """Convenience method to create a new form from a request object."""
        return cls(
            request.POST,
            data=request.POST,
            csrf_context=request.session,
        )

    def generate_csrf_token(self, csrf_context):
        if self.csrf_enabled:
            return csrf_context.get_csrf_token()

    def validate_csrf_token(self, field):
        if not self.csrf_enabled:
            return

        if field.data is None or field.current_token is None:
            raise HTTPUnauthorized('Invalid CSRF')
        if field.data != field.current_token:
            raise HTTPUnauthorized('Invalid CSRF')


class ConflictPreventionForm(CsrfForm):
    """Implements content conflict prevention to stop two people overwriting
    each other changes.

    This form detects the case where user A loads up this form and makes some
    changes while user B simultaneously loads up the same form and makes some
    other changes and saves them before user A.
    """
    cp_token = HiddenField(
        'Content conflict',
        validators=[
            DataRequired(message="The Content Changes Token is missing"),
        ]
    )

    def process(self, formdata=None, obj=None, **kwargs):
        super(ConflictPreventionForm, self).process(formdata, obj, **kwargs)

        self._cp_hash = self._object_hash(obj)
        if not formdata:
            self.cp_token.data = self._object_hash(obj)

    def validate_cp_token(form, cp_token):
        if not form._cp_hash == cp_token.data:
            raise ValidationError(
               "Could not save as the content has become outdated. " \
               "The content has changed since this page was " \
               "initially loaded."
            )

    def _object_hash(self, obj):
        props = vars(obj)
        fields = {k: v for k, v in props.items() if k in self._fields}

        return hashlib.md5(pickle.dumps(fields)).hexdigest()


class ContentEditForm:
    """Form class for editing Content objects"""
    def __new__(self, model_class, session, data=None, obj=None, **kwargs):
        FormCls = model_form(
            model_class,
            base_class=ConflictPreventionForm,
            only=self._editable_properties(obj, Content),
            db_session=session,
        )
        return FormCls(data, obj, **kwargs)

    @classmethod
    def from_request(cls, request):
        """Convenience method to create a new edit form with data from
        a request object."""
        return cls(
            request.context.content.__class__,
            session=request.y_db,
            data=request.POST,
            obj=request.context.content,
            csrf_context=request.session,
        )

    def _editable_properties(obj, BaseClass):
        """Returns list of columns that can be considered editable"""
        obj_columns = set(obj.__mapper__.columns.keys())
        content_cols = set(BaseClass.__mapper__.columns.keys())
        editable_content_cols = content_cols - BaseClass.__editable_fields__

        return list(obj_columns - editable_content_cols)


class LoginForm(BaseForm):
    email = TextField(u'Email', [required(), email()])
    password = PasswordField(u'Password', [required()])


class ContentMoveForm(CsrfForm):
    parent_location_id = HiddenField(validators=[required()])
