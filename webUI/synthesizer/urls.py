from django.conf.urls import url

from . import views

app_name = 'synthesizer'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^index_data', views.index_data, name='index_data'),
    url(r'^proc_data_dash/$', views.proc_data_dash, name='proc_data_dash'),
    url(r'^proc_json_processing/$', views.proc_json_processing, name='proc_json_processing'),

    # url(r'^proc_data_tables/$', views.proc_data_tables, name='proc_data_tables'),
    # url(r'^proc_random_mode/$', views.proc_random_mode, name='proc_random_mode'),
    # url(r'^proc_corre_mode/$', views.proc_corre_mode, name='proc_corre_mode'),
    # url(r'^proc_other_mode/$', views.proc_other_mode, name='proc_other_mode'),

    # url(r'^reload_display/$', views.reload_display, name='reload_display'),
    url(r'^synthesizer_display/$', views.synthesizer_display, name='synthesizer_display'),
    # url(r'^json_synthetic_data/$', views.json_synthetic_data, name='json_synthetic_data'),
    url(r'^res_json_processing_plot/$', views.res_json_processing_plot, name='res_json_processing_plot'),
    url(r'^res_json_processing/$', views.res_json_processing, name='res_json_processing'),
    url(r'^res_json_processing_after/$', views.res_json_processing_after, name='res_json_processing_after'),

    url(r'^com_data/$', views.com_data, name='com_data'),
    url(r'^com_histogram/$', views.com_histogram, name='com_histogram'),
    url(r'^com_hitmap/$', views.com_hitmap, name='com_hitmap'),
    # url(r'^att_histogram/$', views.att_histogram, name='att_histogram'),
    # url(r'^correlation/$', views.correlation, name='correlation'),
    # url(r'^syn_data_tables/$', views.syn_data_tables, name='syn_data_tables'),
    # url(r'^random_mode/$', views.random_mode, name='random_mode'),
    # url(r'^corre_mode/$', views.corre_mode, name='corre_mode'),
    # url(r'^other_mode/$', views.other_mode, name='other_mode'),
]
