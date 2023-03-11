# forms.py

from wtforms import Form, StringField, SelectField

class LeadSearchForm(Form):
    choices = [('name', 'Name'),
               ('ad_name', 'Ad Name'),
               ('interested_in', 'Interested In')]
    select = SelectField('Search for Lead:', choices=choices)
    search = StringField('')