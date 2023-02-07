from django.urls import path
from django.views.generic import RedirectView
from django.conf.urls import url
from .views import *

urlpatterns = [
    path("", index, name="index-view"),
    path("upload-csv/", upload_view_goodreads, name="csv-upload"),
    path("upload/", upload, name="upload"),
    path("run-script/", runscript, name="run-script"),
    path("finish-plot/", finish_plot_view, name="finish-plot"),
    path("nationality-map/", nationality_map_view, name="nationality-map"),
    path("popularity-spectrum/", popularity_spectrum_view, name="popularity-spectrum"),
    path("summary-plot/", summary_plot_view, name="summary-plot"),
    path("monthly-pages-read/", monthly_pages_read_view, name="monthly-pages-read"),
    path("yearly-pages-read/", yearly_pages_read_view, name="yearly-pages-read"),
    path("about-this/", about_this, name="about-this"),
    path("books-home/", books_home, name="books-home"),
    path("music-home/", music_home, name="music-home"),
    path("plots/", plots_view, name="plots"),
    path("geography/", geography, name="geography-home"),
    path("faq/", faq, name="faq"),
    url(r"^favicon\.ico$", RedirectView.as_view(url="/static/admin/img/favicon.ico")),
]
