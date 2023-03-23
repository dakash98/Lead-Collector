from django.db import models

# Create your models here.

class LeadsModel(models.Model):
    name = models.CharField(max_length=500)
    phone_number = models.CharField(max_length=20)
    interested_in = models.CharField(max_length=20)
    ad_name = models.CharField(max_length=300)
    email_sent = models.BooleanField(default=False)
    new_lead = models.BooleanField(default=False)
    created_at = models.CharField(max_length=250)

    def __str__(self):
        return self.name

