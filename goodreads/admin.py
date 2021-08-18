from django.contrib import admin
from .models import ExportData


@admin.register(ExportData)
class ExportDataAdmin(admin.ModelAdmin):
    list_display = ('book_id', 'title', 'author')
