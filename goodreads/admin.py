from django.contrib import admin
from .models import (
    ExportData,
    Books,
    Authors,
    NetflixTitles,
    NetflixGenres,
    NetflixActors,
    SpotifyTracks,
    SpotifyArtist,
    RefNationality,
    BooksLists,
    Comments,
)


@admin.register(ExportData)
class ExportDataAdmin(admin.ModelAdmin):
    search_fields = ("book_id__startswith", "title__contains", "author__startswith")
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


@admin.register(Books)
class BooksAdmin(admin.ModelAdmin):
    search_fields = ("book_id__startswith",)
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


@admin.register(Authors)
class AuthorsAdmin(admin.ModelAdmin):
    search_fields = ("author_name__contains", "nationality_chosen__startswith")
    list_display = (
        "author_name",
        "gender",
        "nationality1",
        "nationality2",
        "nationality_chosen",
        "ts_updated",
    )


@admin.register(NetflixTitles)
class NetflixTitlesAdmin(admin.ModelAdmin):
    search_fields = ("title__contains", "netflix_id__startswith")
    list_display = (
        "netflix_id",
        "title",
        "director",
        "release_year",
        "title_type",
        "alt_votes",
        "default_image",
        "ts_updated",
    )


@admin.register(NetflixGenres)
class NetflixGenresAdmin(admin.ModelAdmin):
    search_fields = ("netflix_id__startswith", "genre__contains")
    list_display = (
        "netflix_id",
        "genres",
    )


@admin.register(NetflixActors)
class NetflixActorsCast(admin.ModelAdmin):
    search_fields = ("netflix_id__startswith", "cast__contains")
    list_display = (
        "netflix_id",
        "cast",
    )


@admin.register(SpotifyTracks)
class SpotifyTracksAdmin(admin.ModelAdmin):
    search_fields = ("uri__startswith", "name__startswith")
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
        "artist_uri",
        "ts_updated",
    )


@admin.register(SpotifyArtist)
class SpotifyArtistAdmin(admin.ModelAdmin):
    search_fields = ("uri__contains", "artist_name__contains", "genres_contains")
    list_display = (
        "uri",
        "artist_name",
        "genres",
        "popularity",
        "followers_total",
        "image_url",
    )


@admin.register(RefNationality)
class RefNationalityAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "region",
        "nationality",
    )


@admin.register(BooksLists)
class BooksListsAdmin(admin.ModelAdmin):
    search_fields = ("title__contains", "list_name__contains")
    list_display = (
        "id",
        "book_id",
        "title",
        "author",
        "list_name",
        "rank",
    )


@admin.register(Comments)
class Comments(admin.ModelAdmin):
    list_display = ("username", "comments", "timestamp")

