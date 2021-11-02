from django.urls import path
from django.views.generic import RedirectView
from django.conf.urls import url
from .views import *

urlpatterns = [
    path('', index, name='index-view'),
    path('upload-csv/', upload_view, name='csv-upload'),
    path('run-script/', runscript, name='run-script'),
    path('finish-plot/', finish_plot_view, name='finish-plot'),
    path('nationality-map/', nationality_map_view, name='nationality-map'),
    path('popularity-spectrum/', popularity_spectrum_view, name='popularity-spectrum'),
    path('summary-plot/', summary_plot_view, name='summary-plot'),
    path('yearly-pages-read/', yearly_pages_read_view, name='yearly-pages-read'),
    path('about-this/', about_this, name='about-this'),
    path('plots/', plots_view, name='plots'),
    path('geography/', geography, name='geography'),
    url(r'^favicon\.ico$',RedirectView.as_view(url='/static/admin/img/favicon.ico')),
]