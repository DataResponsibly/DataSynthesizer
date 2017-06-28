import json
from time import time

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render

from .models import DataDescriberUI
from .models import chart_position_score
from .models import save_uploaded_file


def base(request):
    return render(request, "base.html")


def base_data(request):
    current_file = "./static/intermediatedata/" + str(time()) + ".csv"
    if request.POST and request.FILES:
        csvfile = request.FILES['csv_file']
        save_uploaded_file(csvfile, current_file)

    request.session['passed_data_name'] = current_file
    context = {'passed_data_name': current_file}
    return HttpResponseRedirect(reverse('dataflow:data_process'))


def data_process(request):
    passed_data_name = request.session.get('passed_data_name')
    up_data = DataDescriberUI()
    up_data.read_dataset_from_csv(passed_data_name)
    up_data.get_dataset_meta_info()
    up_data.get_json_data()

    json_header = []
    att_list = up_data.dataset_description['meta']['attribute_list']
    for i in range(len(att_list)):
        json_header.append({"data": str(att_list[i])})

    context = {'passed_data_name': passed_data_name, "passed_json_columns": json_header, "passed_column_name": att_list}
    return render(request, "dataflow/data_processing_dash.html", context)


def data_tables(request):
    passed_data_name = request.session.get('passed_data_name')

    up_data = DataDescriberUI()
    up_data.read_dataset_from_csv(passed_data_name)
    up_data.get_dataset_meta_info()
    up_data.get_json_data()

    json_header = []
    att_list = up_data.dataset_description['meta']['attribute_list']
    for i in range(len(att_list)):
        json_header.append({"data": str(att_list[i])})

    context = {'passed_data_name': passed_data_name, "passed_json_columns": json_header,
               "passed_column_name": att_list}

    return render(request, 'dataflow/data_tables.html', context)


def proc_fairness(request):
    passed_data = request.session.get('passed_data_name')
    context = {'passed_data_name': passed_data}
    return render(request, 'dataflow/proc_fairness.html', context)


def proc_stability(request):
    passed_data = request.session.get('passed_data_name')
    context = {'passed_data_name': passed_data}
    return render(request, 'dataflow/proc_stability.html', context)


def nutrition_facts(request):
    passed_data_name = request.session.get('passed_data_name')
    # data['chart_data'] = chart_position_score(passed_data_name)

    context = {'passed_data_name': passed_data_name}

    return render(request, 'dataflow/nutrition_dashboard.html', context)


def res_data_tables(request):
    passed_data_name = request.session.get('passed_data_name')

    up_data = DataDescriberUI()
    up_data.read_dataset_from_csv(passed_data_name)
    up_data.get_dataset_meta_info()
    up_data.get_json_data()

    json_header = []
    att_list = up_data.dataset_description['meta']['attribute_list']
    for i in range(len(att_list)):
        json_header.append({"data": str(att_list[i])})

    context = {'passed_data_name': passed_data_name, "passed_json_columns": json_header,
               "passed_column_name": att_list}

    return render(request, 'dataflow/res_data_tables.html', context)


def stability(request):
    passed_data_name = request.session.get('passed_data_name')

    context = {'passed_data_name': passed_data_name}

    return render(request, 'dataflow/stability.html', context)


def json_nutrition(request):
    data = {}
    passed_data_name = request.session.get('passed_data_name')
    data["scatters"] = chart_position_score(passed_data_name)
    return HttpResponse(json.dumps(data), content_type='application/json')


def json_processing(request):
    passed_data_name = request.session.get('passed_data_name')

    up_data = DataDescriberUI()
    up_data.read_dataset_from_csv(passed_data_name)
    up_data.get_dataset_meta_info()
    up_data.get_json_data()

    total_json = {}
    total_json = up_data.json_data

    return HttpResponse(total_json, content_type='application/json')
