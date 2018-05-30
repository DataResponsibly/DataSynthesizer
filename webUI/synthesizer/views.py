import json
from time import time

from django.urls import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render

import synthesizer.lib.DataSynthesizerWrapper as wrapper
from DataSynthesizer.lib.utils import read_json_file
from .models import DataDescriberUI
from .models import save_uploaded_file


def index(request):
    return render(request, "synthesizer/index.html")


def index_data(request):
    current_file = "./media/" + str(time())
    if request.POST and request.FILES:
        csvfile = request.FILES['csv_file']
        save_uploaded_file(csvfile, current_file)

    request.session['passed_data_name'] = current_file
    # context = {'passed_data_name': current_file}
    return HttpResponseRedirect(reverse('synthesizer:proc_data_dash'))


def proc_data_dash(request):
    passed_data_name = request.session.get('passed_data_name')
    json_cate_info = wrapper.get_dataset_info(passed_data_name + ".csv")
    att_list = json_cate_info["attribute_list"]
    cat_att_list = json_cate_info["categorical_attributes"]
    key_att_list = json_cate_info['candidate_attributes']
    json_header = []
    for i in range(len(att_list)):
        json_header.append({"data": str(att_list[i])})

    request.session['passed_json_columns'] = json_header
    request.session['passed_column_name'] = att_list

    data_type_list = []
    for i in att_list:
        data_type_list.append(json_cate_info["attribute_datatypes"][i])
    tuple_n = json_cate_info["number_of_tuples"]

    context = {'passed_data_name': passed_data_name, "passed_json_columns": json_header, "passed_column_name": att_list,
               "passed_cat_atts": cat_att_list, "passed_att_types": data_type_list, "tuple_n": tuple_n,
               "passed_key_atts": key_att_list}

    return render(request, "synthesizer/proc_data_dash.html", context)


def proc_json_processing(request):
    passed_data_name = request.session.get('passed_data_name')

    up_data = DataDescriberUI()
    up_data.read_dataset_from_csv(passed_data_name)
    up_data.get_json_data()

    total_json = up_data.json_data

    return HttpResponse(total_json, content_type='application/json')


def res_json_processing(request):
    passed_data_name = request.session.get('passed_data_name')

    up_data = DataDescriberUI()
    up_data.read_dataset_from_csv(passed_data_name)
    up_data.get_json_data()

    total_json = up_data.json_data

    return HttpResponse(total_json, content_type='application/json')


def res_json_processing_after(request):
    passed_data_name = request.session.get('passed_data_name')

    up_data = DataDescriberUI()
    up_data.read_dataset_from_csv('{}_synthetic_data'.format(passed_data_name))
    up_data.get_json_data()

    total_json = up_data.json_data

    return HttpResponse(total_json, content_type='application/json')


def res_json_processing_plot(request):
    passed_data_name = request.session.get('passed_data_name')
    description_file = passed_data_name + "_plot.json"
    plot_json = read_json_file(description_file)
    return HttpResponse(json.dumps(plot_json), content_type='application/json')


def synthesizer_display(request):
    passed_data_name = request.session.get('passed_data_name')
    passed_json_columns = request.session.get('passed_json_columns')
    passed_column_name = request.session.get('passed_column_name')
    mode_name = request.session.get('mode_name')
    context = {'passed_data_name': passed_data_name, "passed_json_columns": passed_json_columns,
               "passed_column_name": passed_column_name, "mode_name": mode_name}

    return render(request, 'synthesizer/com_data.html', context)


def com_data(request):
    passed_data_name = request.session.get('passed_data_name')
    passed_json_columns = request.session.get('passed_json_columns')
    passed_column_name = request.session.get('passed_column_name')

    # get user input
    chosen_mode = request.POST['chose_mode']
    mode_id = chosen_mode.replace("mode", "")
    json_parameter = {}
    json_parameter["chose_mode"] = chosen_mode
    json_parameter["tuple_n"] = request.POST['tuple_N_m' + mode_id]
    json_parameter["categorical_atts"] = request.POST.getlist('checks_m' + mode_id)
    json_parameter["candidate_atts"] = request.POST.getlist('key_checks_m' + mode_id)
    # json_parameter["categorical_threshold"] = request.POST['cate_threshold_m' + mode_id]
    json_parameter["seed"] = request.POST['seed_m' + mode_id]

    mode_name = ""
    if mode_id != "1":
        json_parameter["histogram_size"] = request.POST['hist_size_m' + mode_id]
        json_parameter["epsilon"] = request.POST['epsilon_m' + mode_id]
        user_type_atts = {}
        for atti in passed_column_name:
            user_type_atts[atti] = request.POST[atti + "_m" + mode_id]

        json_parameter["type_atts"] = user_type_atts
    if mode_id == "3":
        json_parameter["max_degree"] = request.POST['max_degree']
    if mode_id == "1":
        mode_name = "Random Mode"
    if mode_id == "2":
        mode_name = "Independent Attribute Mode"
    if mode_id == "3":
        mode_name = "Correlated Attribute Mode"
    request.session["mode_name"] = mode_name
    # save user input parameters to server
    json_parameter_outputfn = passed_data_name + "_parameters.json"
    with open(json_parameter_outputfn, 'w') as outfile:
        json.dump(json_parameter, outfile, indent=4)

    wrapper.generate_data(passed_data_name)

    synthetic_data_name = passed_data_name + "_synthetic_data.csv"
    description_file = passed_data_name + "_description.json"
    wrapper.get_plot_data(passed_data_name + ".csv", synthetic_data_name, description_file)

    passed_download_data = synthetic_data_name.replace("./media/", "")
    passed_download_desp = description_file.replace("./media/", "")

    request.session["passed_download_data"] = passed_download_data
    request.session["passed_download_desp"] = passed_download_desp

    context = {'passed_data_name': passed_data_name, "passed_json_columns": passed_json_columns,
               "passed_column_name": passed_column_name, "mode_name": mode_name,
               "passed_download_data": passed_download_data, "passed_download_desp": passed_download_desp}
    return render(request, 'synthesizer/com_data.html', context)


def com_histogram(request):
    passed_data = request.session.get('passed_data_name')
    passed_json_columns = request.session.get('passed_json_columns')
    passed_column_name = request.session.get('passed_column_name')
    mode_name = request.session.get('mode_name')
    passed_download_data = request.session.get('passed_download_data')
    passed_download_desp = request.session.get('passed_download_desp')

    # get categorical attributes list
    cate_atts = wrapper.get_categorical_attributes(passed_data + '_plot.json')
    draw_atts = wrapper.get_drawable_attributes(passed_data + '_plot.json')
    context = {'passed_data_name': passed_data, "passed_json_columns": passed_json_columns,
               "passed_column_name": passed_column_name, "cate_column_name": cate_atts,
               "mode_name": mode_name, "drawable_atts": draw_atts,
               "passed_download_data": passed_download_data, "passed_download_desp": passed_download_desp}
    return render(request, 'synthesizer/com_histogram.html', context)


def com_hitmap(request):
    passed_data = request.session.get('passed_data_name')
    passed_json_columns = request.session.get('passed_json_columns')
    passed_column_name = request.session.get('passed_column_name')
    mode_name = request.session.get('mode_name')
    passed_download_data = request.session.get('passed_download_data')
    passed_download_desp = request.session.get('passed_download_desp')

    context = {'passed_data_name': passed_data, "passed_json_columns": passed_json_columns,
               "passed_column_name": passed_column_name, "mode_name": mode_name,
               "passed_download_data": passed_download_data, "passed_download_desp": passed_download_desp}
    return render(request, 'synthesizer/com_hitmap.html', context)
