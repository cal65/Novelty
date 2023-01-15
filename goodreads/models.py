from django.db import models


class ExportData(models.Model):
    class Meta:
        managed = True
        constraints = [models.UniqueConstraint(fields=["book_id", "username"], name="book_per_user")]

    id = models.AutoField(primary_key=True)
    book_id = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    author = models.CharField(max_length=250)
    number_of_pages = models.IntegerField(blank=True, null=True)
    my_rating = models.FloatField(blank=True, null=True)
    average_rating = models.FloatField(blank=True, null=True)
    original_publication_year = models.FloatField(blank=True, null=True)
    date_read = models.DateField(auto_now=False, blank=True, null=True)
    exclusive_shelf = models.CharField(max_length=30, default="read")
    username = models.CharField(max_length=30, default="Random")
    ts_updated = models.DateTimeField(auto_now=True)
    # author_l_f = models.CharField(max_length=250)
    # additional_authors = models.CharField(max_length=250)
    # isbn = models.CharField(max_length=250)
    # isbn13 = models.CharField(max_length=250)
    # publisher = models.CharField(max_length=250)
    # binding = models.CharField(max_length=250)
    # my_review = models.TextField()


class Authors(models.Model):
    author_name = models.CharField(max_length=250, primary_key=True)
    gender = models.CharField(blank=True, null=True, max_length=50)
    nationality1 = models.CharField(blank=True, null=True, max_length=80)
    nationality2 = models.CharField(blank=True, null=True, max_length=80)
    nationality_chosen = models.CharField(blank=True, null=True, max_length=80)
    ts_updated = models.DateTimeField(auto_now=True)


class Books(models.Model):
    book_id = models.CharField(max_length=250, primary_key=True)
    shelf1 = models.CharField(max_length=250, null=True)
    shelf2 = models.CharField(max_length=250, null=True)
    shelf3 = models.CharField(max_length=250, null=True)
    shelf4 = models.CharField(max_length=250, null=True)
    shelf5 = models.CharField(max_length=250, null=True)
    shelf6 = models.CharField(max_length=250, null=True)
    shelf7 = models.CharField(max_length=250, null=True)
    added_by = models.IntegerField(blank=True, null=True, default=0)
    to_reads = models.IntegerField(blank=True, null=True, default=0)
    narrative = models.CharField(max_length=250, default="Fiction")
    ts_updated = models.DateTimeField(auto_now=True)


class RefNationality(models.Model):
    id = models.BigAutoField(primary_key=True)
    region = models.CharField(max_length=250, null=True)
    nationality = models.CharField(max_length=250, blank=True, null=True)
