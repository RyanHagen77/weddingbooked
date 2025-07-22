# wedding_day_guide/models.py
from django.db import models


class WeddingDayGuide(models.Model):
    contract = models.OneToOneField('contracts.Contract', on_delete=models.CASCADE, related_name='wedding_day_guide')
    event_date = models.DateField(null=True, blank=True)
    primary_contact = models.CharField(max_length=255, null=True, blank=True)
    primary_email = models.EmailField(null=True, blank=True)
    primary_phone = models.CharField(max_length=15, null=True, blank=True)
    partner_contact = models.CharField(max_length=255, null=True, blank=True)
    partner_email = models.EmailField(null=True, blank=True)
    partner_phone = models.CharField(max_length=15, null=True, blank=True)
    dressing_location = models.CharField(max_length=255, null=True, blank=True)
    dressing_address = models.CharField(max_length=255, null=True, blank=True)
    dressing_start_time = models.TimeField(null=True, blank=True)
    ceremony_site = models.CharField(max_length=255, null=True, blank=True)
    ceremony_address = models.CharField(max_length=255, null=True, blank=True)
    ceremony_phone = models.CharField(max_length=15, null=True, blank=True)
    ceremony_start = models.TimeField(null=True, blank=True)
    ceremony_end = models.TimeField(null=True, blank=True)
    reception_site = models.CharField(max_length=255, null=True, blank=True)
    reception_address = models.CharField(max_length=255, null=True, blank=True)
    reception_phone = models.CharField(max_length=15, null=True, blank=True)
    reception_start = models.TimeField(null=True, blank=True)
    dinner_start = models.TimeField(null=True, blank=True)
    reception_end = models.TimeField(null=True, blank=True)
    staff_table = models.CharField(max_length=255, null=True, blank=True)
    photo_stop1 = models.CharField(max_length=255, null=True, blank=True)
    photo_stop2 = models.CharField(max_length=255, null=True, blank=True)
    photo_stop3 = models.CharField(max_length=255, null=True, blank=True)
    photo_stop4 = models.CharField(max_length=255, null=True, blank=True)
    photographer2_start_location = models.CharField(max_length=255, null=True, blank=True)
    photographer2_start_location_address = models.CharField(max_length=255, null=True, blank=True)
    photographer2_start = models.TimeField(null=True, blank=True)
    p1_attendant_of_honor = models.CharField(max_length=255, null=True, blank=True)
    p1_attendant_qty = models.IntegerField(null=True, blank=True)
    flower_attendant_qty = models.IntegerField(null=True, blank=True)
    usher_qty = models.IntegerField(null=True, blank=True)
    p2_attendant_of_honor = models.CharField(max_length=255, null=True, blank=True)
    p2_attendant_qty = models.IntegerField(null=True, blank=True)
    ring_bearer_qty = models.IntegerField(null=True, blank=True)
    p1_parent_names = models.TextField(max_length=255, null=True, blank=True)
    p1_sibling_names = models.TextField(max_length=255, null=True, blank=True)
    p1_grandparent_names = models.TextField(max_length=255, null=True, blank=True)
    p2_parent_names = models.TextField(max_length=255, null=True, blank=True)
    p2_sibling_names = models.TextField(max_length=255, null=True, blank=True)
    p2_grandparent_names = models.TextField(max_length=255, null=True, blank=True)
    additional_photo_request1 = models.TextField(max_length=255, null=True, blank=True)
    additional_photo_request2 = models.TextField(max_length=255, null=True, blank=True)
    additional_photo_request3 = models.TextField(max_length=255, null=True, blank=True)
    additional_photo_request4 = models.TextField(max_length=255, null=True, blank=True)
    additional_photo_request5 = models.TextField(max_length=255, null=True, blank=True)

    video_client_names = models.CharField(max_length=255, null=True, blank=True)
    wedding_story_song_title = models.CharField(max_length=255, null=True, blank=True)
    wedding_story_song_artist = models.CharField(max_length=255, null=True, blank=True)
    dance_montage_song_title = models.CharField(max_length=255, null=True, blank=True)
    dance_montage_song_artist = models.CharField(max_length=255, null=True, blank=True)
    video_special_dances = models.TextField(max_length=255, null=True, blank=True)

    photo_booth_text_line1 = models.TextField(max_length=255, null=True, blank=True)
    photo_booth_text_line2 = models.TextField(max_length=255, null=True, blank=True)
    photo_booth_placement = models.TextField(max_length=255, null=True, blank=True)
    photo_booth_end_time = models.TimeField(max_length=255, null=True, blank=True)


    version_number = models.IntegerField(default=1)  # Version control

    submitted = models.BooleanField(default=False)

    def __str__(self):
        return f"Wedding Day Guide for {self.primary_contact} and {self.partner_contact}"

    def save(self, *args, **kwargs):
        if not self.pk:  # Only populate if it's a new instance
            contract = self.contract
            self.event_date = contract.event_date
            self.primary_contact = contract.client.primary_contact
            self.primary_email = contract.client.primary_email
            self.primary_phone = contract.client.primary_phone1
            self.partner_contact = contract.client.partner_contact
            self.partner_email = contract.client.partner_email
            self.partner_phone = contract.client.partner_phone1
        super().save(*args, **kwargs)