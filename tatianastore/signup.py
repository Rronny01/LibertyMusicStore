"""

    Sign up form.

"""


from django import forms

from django import shortcuts
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib.auth.models import Group
from django.conf import settings

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from slugify import slugify

from . import models
from . import emailer


CURRENCIES = [
    ("USD", "USD"),
    ("EUR", "EUR"),
    ("GBP", "GBP"),
]


class SignupForm(forms.Form):
    """ Signing up for the service.
    """

    email = forms.EmailField(label="Email", required=True, help_text="We'll email you the username and the password")

    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)

    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput, help_text=_("Enter the same password as above, for verification."))

    artist_name = forms.CharField(label="Artist / band name", help_text="The name used on the store")

    store_url = forms.URLField(label="Homepage", help_text="Link to your homepage, Facebook page or blog", required=True)

    #btc_address = forms.CharField(label="Bitcoin address",
    #                              help_text="The receiving Bitcoin address where you get the payments for the purchases. You can fill in this later if you don't have Bitcoin wallet right now.",
    #                              required=False)

    currency = forms.ChoiceField(label="Currency", help_text="Your local currency", choices=CURRENCIES)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if models.User.objects.filter(email=email).count() > 0:
            raise forms.ValidationError("This email address is already registered")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match")
        return password2

    def create_user(self):
        """ Create user and corresponding store. """
        data = self.cleaned_data

        artist_name = data["artist_name"]
        username = slugify(artist_name)
        password = data["password1"]
        email = data["email"]
        store_url = data["store_url"]
        # btc_address = data["btc_address"]
        currency = data["currency"]

        u = models.User.objects.create(email=email)
        u.username = username
        u.first_name = artist_name
        u.set_password(password)
        u.is_staff = True

        group = Group.objects.get(name="Store operators")
        u.groups = [group]
        u.save()

        store = models.Store.objects.create(name=artist_name, store_url=store_url, currency=currency)
        store.operators = [u]
        store.save()

        site_url = settings.SITE_URL
        emailer.mail_store_owner(store, "Liberty Music Store sign up confirmation", "email/sign_up.html", dict(store=store, user=u, site_url=site_url))


def signup(request):

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            form.create_user()

    else:
        form = SignupForm()

    form.helper = FormHelper()
    form.helper.add_input(Submit('submit', 'Submit'))

    return shortcuts.render_to_response("site/signup.html", locals(), context_instance=RequestContext(request))


urlpatterns = patterns('',
    url(r'^$', signup, name="signup"),
)
