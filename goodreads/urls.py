from django.urls import path
from django.views.generic import RedirectView
from django.conf.urls import url
from .views import *

urlpatterns = [
    path("", index, name="index-view"),
    path("upload-csv/", upload_view_goodreads, name="upload-view-goodreads"),
    path("upload-spotify-home", upload_view_spotify, name="upload-spotify"),
    path("upload-json-spotify/", upload_spotify, name="json-upload-spotify"),
    path("upload/", upload, name="upload"),
    path("run-script/", runscript, name="run-script"),
    path("run-script-spotify/", runscriptSpotify, name="run-script-spotify"),
    path("finish-plot/", finish_plot_view, name="finish-plot"),
    path("nationality-map/", nationality_map_view, name="nationality-map"),
    path("popularity-spectrum/", popularity_spectrum_view, name="popularity-spectrum"),
    path("summary-plot/", summary_plot_view, name="summary-plot"),
    path("about-this/", about_this, name="about-this"),
    path("about-this-netflix/", about_this_netflix, name="about-this-netflix"),
    path("books-home/", books_home, name="books-home"),
    path("music-home/", music_home, name="music-home"),
    path("plots/", plots_view, name="plots"),
    path("geography/", geography, name="geography-home"),
    path("streaming/", streaming, name="streaming-home"),
    path("faq/", faq, name="faq"),
    url(r"^favicon\.ico$", RedirectView.as_view(url="/static/admin/img/favicon.ico")),
    path("spotify-plots/", spot_plots_view, name="spotify-plots"),
    path("upload-view-netflix/", upload_view_netflix, name="upload-view-netflix"),
    path("upload-netflix/", upload_netflix, name="upload-netflix"),
    path("netflix-plots/", netflix_plots_view, name="netflix-plots"),
    path("gallery-books/", gallery_books, name="gallery-books"),
    path("gallery-music/", gallery_music, name="gallery-music"),
    path("spot-text/", spot_text, name="spot-text"),
]
