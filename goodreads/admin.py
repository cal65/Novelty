from django.contrib import admin
from .models import ExportData, Authors, NetflixTitles, NetflixGenres, SpotifyTracks


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


@admin.register(NetflixTitles)
class NetflixTitlesAdmin(admin.ModelAdmin):
    list_display = (
        "netflix_id",
        "title",
        "director",
        "release_year",
        "title_type",
    )


@admin.register(NetflixGenres)
class NetflixGenresAdmin(admin.ModelAdmin):
    list_display = (
        "netflix_id",
        "genres",
    )


@admin.register(SpotifyTracks)
class SpotifyTracksAdmin(admin.ModelAdmin):
    list_display = (
        "uri",
        "name",
        "artist",
        "duration",
        "popularity",
        "release_date",
        "genres",
        "album",
        "explicit",
        "trackname",
        "podcast",
        "genre_chosen",
    )
