from django.db import models
from adaptor.model import CsvModel
from adaptor.fields import CharField


class ExportData(models.Model):
    book_id = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    author = models.CharField(max_length=250)
    number_of_pages = models.IntegerField(blank=True, null=True)
    my_rating = models.FloatField(blank=True, null=True)
    average_rating = models.FloatField(blank=True, null=True)
    original_publication_year = models.FloatField(blank=True, null=True)
    shelf1 = models.CharField(max_length=250)
    shelf2 = models.CharField(max_length=250)
    shelf3 = models.CharField(max_length=250)
    user = models.CharField(max_length=30, unique=True, default='Random')
    # author_l_f = models.CharField(max_length=250)
    # additional_authors = models.CharField(max_length=250)
    # isbn = models.CharField(max_length=250)
    # isbn13 = models.CharField(max_length=250)
    # publisher = models.CharField(max_length=250)
    # binding = models.CharField(max_length=250)
    # year_published = models.CharField(max_length=250)
    # original_pub_year = models.CharField(max_length=250)
    # date_read = models.CharField(max_length=250)
    # date_added = models.CharField(max_length=250)
    # bookshelves = models.CharField(max_length=250)
    # bookshelves_with_positions = models.CharField(max_length=250)
    # exclusive_shelf = models.CharField(max_length=250)
    # my_review = models.TextField()
    # spoiler = models.CharField(max_length=2500)
    # private_notes = models.CharField(max_length=2500)
    # read_count = models.CharField(max_length=250)
    # recommended_for = models.CharField(max_length=250)
    # recommended_by = models.CharField(max_length=250)
    # owned_copies = models.CharField(max_length=250)
    # original_purchase_date = models.CharField(max_length=250)
    # original_purchase_location = models.CharField(max_length=250)
    # condition = models.CharField(max_length=250)
    # condition_description = models.CharField(max_length=250)
    # bcid = models.CharField(max_length=250)


class Authors(models.Model):
    author_name = models.CharField(max_length=250)
    gender = models.CharField(blank=True, null=True, max_length=50)
    nationality1 = models.CharField(blank=True, null=True, max_length=80)
    nationality2 = models.CharField(blank=True, null=True, max_length=80)
    nationality_chosen = models.CharField(blank=True, null=True, max_length=80)


