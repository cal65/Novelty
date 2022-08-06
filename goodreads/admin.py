from django.contrib import admin
from .models import ExportData, Authors, Books


@admin.register(ExportData)
class ExportDataAdmin(admin.ModelAdmin):
    list_display = (
        "book_id",
        "title",
        "author",
        "number_of_pages",
        "my_rating",
        "average_rating",
        "original_publication_year",
        "username",
    )


@admin.register(Authors)
class AuthorsAdmin(admin.ModelAdmin):
    list_display = (
        "author_name",
        "gender",
        "nationality1",
        "nationality2",
        "nationality_chosen",
    )


@admin.register(Books)
class BooksAdmin(admin.ModelAdmin):
    list_display = (
        "book_id",
        "shelf1",
        "shelf2",
        "shelf3",
        "shelf4",
        "shelf5",
        "shelf6",
        "shelf7",
        "added_by",
        "to_reads",
        "narrative",
        "ts_updated",
    )
