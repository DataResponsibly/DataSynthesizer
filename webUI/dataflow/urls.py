from django.conf.urls import url

from . import views

app_name = 'dataflow'
urlpatterns = [
    url(r'^$', views.base, name='base'),
    url(r'^base_data$', views.base_data, name='base_data'),
    url(r'^data_process/$', views.data_process, name='data_process'),
    url(r'^data_tables/$', views.data_tables, name='data_tables'),
    url(r'^proc_fairness/$', views.proc_fairness, name='proc_fairness'),
    url(r'^proc_stability/$', views.proc_stability, name='proc_stability'),

    url(r'^nutrition_facts/$', views.nutrition_facts, name='nutrition_facts'),
    url(r'^res_data_tables/$', views.res_data_tables, name='res_data_tables'),
    url(r'^stability/$', views.stability, name='stability'),
    url(r'^json_processing/$', views.json_processing, name='json_processing'),
    url(r'^json_nutrition/$', views.json_nutrition, name='json_nutrition'),
]
