from django.conf.urls import url

from . import views

app_name = 'synthesizer'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^proc_data_dash/$', views.proc_data_dash, name='proc_data_dash'),
    url(r'^proc_json_processing/$', views.proc_json_processing, name='proc_json_processing'),

    url(r'^synthesizer_display/$', views.synthesizer_display, name='synthesizer_display'),
    url(r'^res_json_processing_plot/$', views.res_json_processing_plot, name='res_json_processing_plot'),
    url(r'^res_json_processing/$', views.res_json_processing, name='res_json_processing'),
    url(r'^res_json_processing_after/$', views.res_json_processing_after, name='res_json_processing_after'),

    url(r'^com_data/$', views.com_data, name='com_data'),
    url(r'^com_histogram/$', views.com_histogram, name='com_histogram'),
    url(r'^com_hitmap/$', views.com_hitmap, name='com_hitmap'),
]
