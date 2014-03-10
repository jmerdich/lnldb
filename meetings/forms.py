from django import forms
from django.db.models import Q
from django.forms import Form, ModelForm

import datetime

from meetings.models import Meeting,MeetingAnnounce,CCNoticeSend
from events.models import Event,Location

from ajax_select import make_ajax_field
from ajax_select.fields import AutoCompleteSelectMultipleField,AutoCompleteSelectField

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout,Fieldset,Button,ButtonHolder,Submit,Div,MultiField,Field,HTML,Hidden
from crispy_forms.bootstrap import AppendedText,InlineCheckboxes,InlineRadios,Tab,TabHolder,FormActions

class MeetingAdditionForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.layout = Layout(
            'datetime',
            'attendance',
            'meeting_type',
            'location',
            FormActions(
                Submit('save', 'Save Changes'),
            )
        )
        super(MeetingAdditionForm,self).__init__(*args,**kwargs)
    attendance = AutoCompleteSelectMultipleField('Users',required=False)
    location = forms.ModelChoiceField(queryset = Location.objects.filter(available_for_meetings=True),label="Location", required=False)
    
    class Meta:
        model = Meeting
        widgets = {
            'datetime' :forms.widgets.DateInput(attrs={"class":"datepick"}),
        }
        
        
class AnnounceSendForm(forms.ModelForm):
    def __init__(self,meeting,*args,**kwargs):
        super(AnnounceSendForm,self).__init__(*args,**kwargs)
        now = meeting.datetime
        twodaysago = now + datetime.timedelta(days=-3)
        aweekfromnow = now + datetime.timedelta(days=8)
        
        self.fields["events"].queryset = Event.objects.filter(datetime_setup_complete__gte=twodaysago,approved=True,datetime_setup_complete__lte=aweekfromnow).exclude(Q(closed=True)|Q(cancelled=True))
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.layout = Layout(
            Hidden('meeting',meeting.id),
            Field('events',css_class="span6",size="15"),
            'subject',
            'message',
            'email_to',
            FormActions(
                Submit('save', 'Save Changes'),
                )
            )
        
    class Meta:
        model = MeetingAnnounce
        
    events = forms.ModelMultipleChoiceField(queryset=Event.objects.all(),required=False)
       
       
class AnnounceCCSendForm(forms.ModelForm):
    def __init__(self,meeting,*args,**kwargs):
        now = meeting.datetime
        twodaysago = now + datetime.timedelta(days=-4)
        aweekfromnow = now + datetime.timedelta(days=8)
        
        
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.layout = Layout(
            Hidden('meeting',meeting.id),
            Field('events',css_class="span6",size="15"),
            Field('addtl_message',css_class="span6"),
            FormActions(
                Submit('save', 'Send'),
                ),
            )
        super(AnnounceCCSendForm,self).__init__(*args,**kwargs)

        self.fields["events"].queryset = Event.objects.filter(datetime_setup_complete__gte=twodaysago,approved=True,datetime_setup_complete__lte=aweekfromnow).exclude(Q(closed=True)|Q(cancelled=True))
        
    class Meta:
        model = CCNoticeSend
        
    #events = forms.ModelMultipleChoiceField(queryset=Event.objects.all(),required=False)
