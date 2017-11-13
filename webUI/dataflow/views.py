import json
from time import time

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render

from synthesizer.lib.DataSynthesizerWrapper import get_histograms_of
from synthesizer.lib.DataSynthesizerWrapper import get_categorical_attributes_csv
from .models import DataDescriberUI
from .models import get_score_scatter
from .models import save_uploaded_file
from .models import generateRanking
from .models import compute_statistic
from .models import cleanseData
from .models import computeFairPairs
from DataSynthesizer.lib.utils import read_json_file

# view functions to handle index page
def base(request):
    return render(request, "base.html", {})

def base_data(request):
    # NOTICE: no .csv suffix in current passed file name
    current_file = "./media/"  + str(time())
    if request.POST and request.FILES:
        csvfile = request.FILES['csv_file']
        save_uploaded_file(csvfile, current_file)

    request.session['passed_data_name'] = current_file
    return HttpResponseRedirect(reverse('dataflow:data_process'))

# view functions to handle unprocessing parameters setings part
def data_process(request):
    # NOTICE: no .csv suffix in current passed file name
    passed_data_name = request.session.get('passed_data_name')

    atts_info = get_histograms_of(passed_data_name + ".csv")
    cat_atts = atts_info["cate_atts"]
    att_list = atts_info["all_atts"]
    att_ids_list = ["att"+str(i) for i in range(len(att_list))]
    # initialize json data and header for dataTables
    json_data_table = []
    json_header_table = []
    for i in range(len(att_list)):
        json_data_table.append({"data": str(att_list[i])})
        json_header_table.append({"title": str(att_list[i]),"targets": i})
    # compute the list of numerical attributes
    num_atts_names = [x for x in att_list if x not in cat_atts]
    num_atts_ids = [att_ids_list[i] for i in range(len(att_list)) if att_list[i] not in cat_atts]
    zip_num_atts = zip(num_atts_names,num_atts_ids)

    if request.POST:
        # if user submit, save user input to server as parameter file
        # get user input
        json_parameter = {}
        included_atts = []
        included_atts_ids = []
        atts_weights = []

        for i in range(len(att_list)):
            atti_id = att_ids_list[i]
            atti_name = att_list[i]
            if atti_name not in cat_atts:
                atti_json = {}
                att_weight = request.POST[atti_id + "_weight"]
                att_rank = request.POST[atti_id + "_checks"]
                att_order = request.POST[atti_id + "_order"]
                if att_weight =="": # if empty then use default value 1.0
                    att_weight = 1.0
                atti_json["weight"] = att_weight
                atti_json["rank"] = att_rank
                atti_json["order"] = att_order

                if att_rank == atti_name:
                    ranked_weight = float(att_weight)
                    included_atts.append(atti_name)
                    included_atts_ids.append(atti_id)
                    if att_order == "lower":
                        ranked_weight = - ranked_weight
                    atts_weights.append(ranked_weight)

                json_parameter[atti_id] = atti_json
        json_parameter["ranked_atts"] = included_atts
        json_parameter["ranked_atts_weight"] = atts_weights
        # save user input parameters to server
        json_parameter_outputfn = passed_data_name + "_rankings.json"
        with open(json_parameter_outputfn, 'w') as outfile:
            json.dump(json_parameter, outfile, indent=4)

        res_ranked_cols = ["score"]
        res_ranked_cols = res_ranked_cols + included_atts
        json_rank_table = []
        json_rank_header_table = []
        for i in range(len(res_ranked_cols)):
            json_rank_table.append({"data": str(res_ranked_cols[i])})
            json_rank_header_table.append({"title": str(res_ranked_cols[i]),"targets": i})

        context = {'passed_data_name': passed_data_name, "passed_json_columns": json_data_table,
                   "passed_column_name": att_list, "drawable_atts": atts_info["drawable_atts"],
                   "passed_cate_atts": atts_info["cate_atts"], "passed_atts_json": json_parameter,
                   "passed_ranked_atts": included_atts, "passed_res_atts": res_ranked_cols,
                   "passed_json_ranks": json_rank_table, "passed_json_columns_header": json_header_table,
                   "passed_cols_ids": att_ids_list,"passed_json_ranks_header":json_rank_header_table,
                   "passed_ranked_atts_ids": included_atts_ids,"passed_zip_numeric":zip_num_atts,
                   "passed_num_atts_ids": num_atts_ids,"passed_num_atts_names":num_atts_names}
        request.session['running_data'] = "unprocessed"

        return render(request, 'dataflow/parameters_dash.html', context)
    else: # first access this link without post parameters
        res_ranked_cols = "false"
        context = {'passed_data_name': passed_data_name, "passed_json_columns": json_data_table,
                   "passed_column_name": att_list, "drawable_atts": atts_info["drawable_atts"],
                   "passed_cate_atts": atts_info["cate_atts"],"passed_res_atts": res_ranked_cols,
                   "passed_json_columns_header": json_header_table, "passed_cols_ids": att_ids_list,
                   "passed_ranked_atts": res_ranked_cols,"passed_ranked_atts_ids": res_ranked_cols,
                   "passed_zip_numeric":zip_num_atts,"passed_atts_json": res_ranked_cols,
                   "passed_num_atts_ids": num_atts_ids,"passed_num_atts_names":num_atts_names}

        request.session['running_data'] = "unprocessed"
        return render(request, 'dataflow/parameters_dash.html', context)

def json_processing_data(request):
    passed_data_name = request.session.get('passed_data_name')

    up_data = DataDescriberUI()
    up_data.read_dataset_from_csv(passed_data_name+".csv")
    up_data.get_json_data()

    total_json = up_data.json_data

    return HttpResponse(total_json, content_type='application/json')

def json_processing_hist(request):
    passed_data_name = request.session.get('passed_data_name')
    description_file = passed_data_name + "_plot.json"
    plot_json = read_json_file(description_file)
    return HttpResponse(json.dumps(plot_json), content_type='application/json')

def json_generate_ranking(request):
    passed_data_name = request.session.get('passed_data_name')

    res_ranking = generateRanking(passed_data_name)

    return HttpResponse(res_ranking, content_type='application/json')


# view function to handle processing parameter settings
def norm_process(request):
    # NOTICE: no .csv suffix in current passed file name
    passed_data_name = request.session.get('passed_data_name')
    # get the string attribute first
    cat_atts = get_categorical_attributes_csv(passed_data_name + ".csv")
    # cleanse the data first, creating a csv named "_norm.csv"
    norm_data = cleanseData(passed_data_name + ".csv", columns_to_exclude=cat_atts)
    norm_data_name = passed_data_name + "_norm"
    norm_data.to_csv(norm_data_name+".csv", index=False)

    atts_info = get_histograms_of(norm_data_name + ".csv")
    cat_atts = atts_info["cate_atts"]
    att_list = atts_info["all_atts"]
    att_ids_list = ["att" + str(i) for i in range(len(att_list))]
    # initialize json data and header for dataTables
    json_data_table = []
    json_header_table = []
    for i in range(len(att_list)):
        json_data_table.append({"data": str(att_list[i])})
        json_header_table.append({"title": str(att_list[i]), "targets": i})
    # compute the list of numerical attributes
    num_atts_names = [x for x in att_list if x not in cat_atts]
    num_atts_ids = [att_ids_list[i] for i in range(len(att_list)) if att_list[i] not in cat_atts]
    zip_num_atts = zip(num_atts_names, num_atts_ids)

    if request.method == 'POST':
        # if user submit, save user input to server as parameter file
        # get user input
        json_parameter = {}
        included_atts = []
        included_atts_ids = []
        atts_weights = []

        for i in range(len(att_list)):
            atti_id = att_ids_list[i]
            atti_name = att_list[i]
            if atti_name not in cat_atts:
                atti_json = {}
                att_weight = request.POST[atti_id + "_weight"]
                att_rank = request.POST[atti_id + "_checks"]
                att_order = request.POST[atti_id + "_order"]
                if att_weight == "":  # if empty then use default value 1.0
                    att_weight = 1.0
                atti_json["weight"] = att_weight
                atti_json["rank"] = att_rank
                atti_json["order"] = att_order

                if att_rank == atti_name:
                    ranked_weight = float(att_weight)
                    included_atts.append(atti_name)
                    included_atts_ids.append(atti_id)
                    if att_order == "lower":
                        ranked_weight = - ranked_weight
                    atts_weights.append(ranked_weight)

                json_parameter[atti_id] = atti_json
        json_parameter["ranked_atts"] = included_atts
        json_parameter["ranked_atts_weight"] = atts_weights
        # save user input parameters to server
        json_parameter_outputfn = norm_data_name + "_rankings.json"
        with open(json_parameter_outputfn, 'w') as outfile:
            json.dump(json_parameter, outfile, indent=4)

        res_ranked_cols = ["score"]
        res_ranked_cols = res_ranked_cols + included_atts
        json_rank_table = []
        json_rank_header_table = []
        for i in range(len(res_ranked_cols)):
            json_rank_table.append({"data": str(res_ranked_cols[i])})
            json_rank_header_table.append({"title": str(res_ranked_cols[i]),"targets": i})

        context = {'passed_data_name': passed_data_name, "passed_json_columns": json_data_table,
                   "passed_column_name": att_list, "drawable_atts": atts_info["drawable_atts"],
                   "passed_cate_atts": atts_info["cate_atts"], "passed_atts_json": json_parameter,
                   "passed_ranked_atts": included_atts, "passed_res_atts": res_ranked_cols,
                   "passed_json_ranks": json_rank_table, "passed_json_columns_header": json_header_table,
                   "passed_cols_ids": att_ids_list, "passed_json_ranks_header": json_rank_header_table,
                   "passed_ranked_atts_ids": included_atts_ids, "passed_zip_numeric": zip_num_atts,
                   "passed_num_atts_ids": num_atts_ids, "passed_num_atts_names": num_atts_names}
        request.session['running_data'] = "processed"
        return render(request, 'dataflow/parameters_norm_dash.html', context)
    else:
        res_ranked_cols = "false"
        context = {'passed_data_name': passed_data_name, "passed_json_columns": json_data_table,
                   "passed_column_name": att_list, "drawable_atts": atts_info["drawable_atts"],
                   "passed_cate_atts": atts_info["cate_atts"], "passed_res_atts": res_ranked_cols,
                   "passed_json_columns_header": json_header_table, "passed_cols_ids": att_ids_list,
                   "passed_ranked_atts": res_ranked_cols, "passed_ranked_atts_ids": res_ranked_cols,
                   "passed_zip_numeric": zip_num_atts, "passed_atts_json": res_ranked_cols,
                   "passed_num_atts_ids": num_atts_ids, "passed_num_atts_names": num_atts_names}

        request.session['running_data'] = "processed"
    return render(request, 'dataflow/parameters_norm_dash.html', context)

def norm_json_processing_data(request):
    # NOTICE: input name need to update to _norm version for processing data
    passed_data_name = request.session.get('passed_data_name')

    up_data = DataDescriberUI()
    up_data.read_dataset_from_csv(passed_data_name + "_norm.csv")
    up_data.get_json_data()

    total_json = up_data.json_data

    return HttpResponse(total_json, content_type='application/json')

def norm_json_processing_hist(request):
    # NOTICE: input name need to update to _norm version for processing data
    passed_data_name = request.session.get('passed_data_name')
    description_file = passed_data_name + "_norm_plot.json"
    plot_json = read_json_file(description_file)
    return HttpResponse(json.dumps(plot_json), content_type='application/json')

def norm_json_generate_ranking(request):
    # NOTICE: input name need to update to _norm version for processing data
    passed_data_name = request.session.get('passed_data_name')
    res_ranking = generateRanking(passed_data_name+"_norm")
    return HttpResponse(res_ranking, content_type='application/json')


# view functions to handle results page
def nutrition_facts(request):
    passed_data_name = request.session.get('passed_data_name')
    passed_running_data_flag = request.session.get("running_data")
    unprocessed_flag = True
    if passed_running_data_flag == "processed":
        ranks_file = passed_data_name + "_norm_rankings.json"
        cur_data_name = passed_data_name + "_norm"
        unprocessed_flag = False
    else:
        ranks_file = passed_data_name + "_rankings.json"
        cur_data_name = passed_data_name

    rankings_paras = read_json_file(ranks_file)
    chosed_atts = rankings_paras["ranked_atts"]

    # get all the names of att to create att ids, used to avoid long attribute name with space
    # att_names = list(rankings_paras.keys())
    # att_names = att_names[:len(att_names)-2]
    chosed_att_ids_list = ["att" + str(i) for i in range(len(chosed_atts))]
    chosed_atts_zip = zip(chosed_atts, chosed_att_ids_list)
    att_weights = {}
    for i in range(len(chosed_atts)):
        att_weights[chosed_atts[i]] = rankings_paras["ranked_atts_weight"][i]

    chosed_atts_tuple = [(chosed_atts[i],chosed_att_ids_list[i]) for i in range(len(chosed_atts))]

    att_stats = compute_statistic(chosed_atts,cur_data_name)

    context = {'passed_data_name': passed_data_name, "chosed_atts":chosed_atts,
               "att_weights":att_weights, "att_stats":att_stats,
               "passed_choosed_att_zip": chosed_atts_zip, "passed_cols_ids": chosed_att_ids_list,
               "chosed_atts_tuple": chosed_atts_tuple, "passed_unprocessing_flag":unprocessed_flag}

    return render(request, 'dataflow/nutrition_dashboard.html', context)


def res_personal(request):
    passed_data_name = request.session.get('passed_data_name')
    passed_running_data_flag = request.session.get("running_data")
    unprocessed_flag = True
    if passed_running_data_flag == "processed":
        unprocessed_flag = False

    up_data = DataDescriberUI()
    up_data.read_dataset_from_csv(passed_data_name+".csv")
    up_data.get_dataset_meta_info()

    att_list = up_data.dataset_description['meta']['attribute_list']
    index_list = [x for x in range(len(up_data.display_dataset))]

    context = {'passed_data_name': passed_data_name, "passed_index": index_list,
               "passed_column_name": att_list, "passed_unprocessing_flag":unprocessed_flag}

    return render(request, 'dataflow/res_personal.html', context)

def res_fairness(request):
    passed_data_name = request.session.get('passed_data_name')
    passed_running_data_flag = request.session.get("running_data")
    unprocessed_flag = True
    if passed_running_data_flag == "processed":
        unprocessed_flag = False
    up_data = DataDescriberUI()
    up_data.read_dataset_from_csv(passed_data_name + ".csv")
    up_data.get_dataset_meta_info()

    att_list = up_data.dataset_description['meta']['attribute_list']
    att_ids_list = ["att" + str(i) for i in range(len(att_list))]
    zip_atts = zip(att_list,att_ids_list)

    if request.method == 'POST':
        # run the fairness pairs computation
        fair_check_atts = []
        fair_checked_atts_ids = []
        for i in range(len(att_list)):
            atti_id = att_ids_list[i]
            atti_name = att_list[i]

            att_check = request.POST[atti_id + "_sensi_checks"]

            if att_check == atti_name:
                fair_check_atts.append(atti_name)
                fair_checked_atts_ids.append(atti_id)
        # compute the att's pairs of group in the generated ranking

        fair_check_json = computeFairPairs(fair_check_atts, passed_data_name)

        context = {'passed_data_name': passed_data_name, "passed_column_name": att_list,
                   "passed_unprocessing_flag": unprocessed_flag, "passed_column_ids": att_ids_list,
                   "passed_zip_atts": zip_atts, "passed_checked_atts":fair_check_atts,
                   "passed_fair_table": fair_check_json, "passed_checked_atts_ids": fair_checked_atts_ids}
    else:
        # return the normal access parameters
        fair_table_flag = "false"
        context = {'passed_data_name': passed_data_name,"passed_column_name":att_list,
                   "passed_unprocessing_flag": unprocessed_flag,"passed_column_ids":att_ids_list,
                   "passed_zip_atts":zip_atts, "passed_fair_table":fair_table_flag}

    return render(request, 'dataflow/res_fairness.html', context)

def json_scatter_score(request):
    passed_data_name = request.session.get('passed_data_name')
    passed_running_data_flag = request.session.get("running_data")
    if passed_running_data_flag == "processed":
        cur_data_name = passed_data_name + "_norm"
    else:
        cur_data_name = passed_data_name

    scatter_data = get_score_scatter(cur_data_name)
    return HttpResponse(json.dumps(scatter_data), content_type='application/json')



