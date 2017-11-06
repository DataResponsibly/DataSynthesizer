import json

import numpy as np
import pandas as pd
from DataSynthesizer.lib.utils import read_json_file

def save_uploaded_file(f, current_file):
    with open(current_file+".csv", 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def get_score_scatter(current_file):
    data = pd.read_csv(current_file+"_weightsum.csv")
    scatter_points = []
    score_value = data["score"].tolist()
    position_value = [x for x in range(1, len(data) + 1)]
    for i in range(len(score_value)):
        scatter_points.append([position_value[i], score_value[i]])
    return scatter_points

def compute_statistic(chosed_atts,current_file):
    data = pd.read_csv(current_file+"_weightsum.csv")
    statistic_data = {"topTen":[],"topHundred":[]}
    # get the median data
    for atti in chosed_atts:
        att_info_topT = []
        att_info_topH = []

        att_info_topT.append(max(data[atti][0:10]))
        att_info_topT.append(np.median(data[atti][0:10]))
        att_info_topT.append(min(data[atti][0:10]))
        formatted_att_info_topT = [ '%.2f' % elem for elem in att_info_topT ]
        statistic_data["topTen"].append(formatted_att_info_topT)

        att_info_topH.append(max(data[atti][0:100]))
        att_info_topH.append(np.median(data[atti][0:100]))
        att_info_topH.append(min(data[atti][0:100]))
        formatted_att_info_topH = ['%.2f' % elem for elem in att_info_topH]
        statistic_data['topHundred'].append(formatted_att_info_topH)
    return statistic_data

def generateRanking(current_file):
    ranks_file = current_file + "_rankings.json"
    rankings_paras = read_json_file(ranks_file)
    data = pd.read_csv(current_file + ".csv").head(100)
    # before compute the score, replace the NA in the data with 0
    filled_data = data.fillna(value=0)
    chosed_atts = rankings_paras["ranked_atts"]
    filled_data["score"] = 0
    for i in range(len(chosed_atts)):
        cur_weight = rankings_paras["ranked_atts_weight"][i]
        filled_data["score"] += cur_weight * filled_data[chosed_atts[i]]
    filled_data = filled_data.reindex_axis(['score'] + list([a for a in filled_data.columns if a != 'score']), axis=1)
    # save data with weight sum to a csv on server
    filled_data.sort_values(by="score",ascending=False,inplace=True)
    filled_data.to_csv(current_file+"_weightsum.csv")
    # display_data = data.head(100)
    return filled_data.to_json(orient='records')



def standardizeData(inputdata,colums_to_exclude=[]):
    """
        inputdata is a dataframe stored all the data read from a csv source file
        noweightlist is a array like data structure stored the attributes which should be ignored in the normalization process.
        return the distribution of every attribute
    """
    df = inputdata.loc[:, inputdata.columns.difference(colums_to_exclude)]# remove no weight attributes
    df_stand = (df - df.mean())/np.std(df)
    inputdata.loc[:, inputdata.columns.difference(colums_to_exclude)] = df_stand
    return inputdata

def normalizeDataset(input_file_name,noweightlist=[]):
    """
        inputdata is the file name of the csv source file
        noweightlist is a array like data structure stored the attributes which should be ignored in the normalization process.
        return the processed inputdata
    """
    input_data = pd.read_csv(input_file_name)
    df = input_data.loc[:,input_data.columns.difference(noweightlist)] # remove no weight attributes
    #normalize attributes
    norm_df = (df - df.min()) / (df.max() - df.min())

    input_data.loc[:,input_data.columns.difference(noweightlist)] = norm_df

    return input_data

def cleanseData(input_file_name, columns_to_exclude=[]):
    """
            inputdata is the file name of the csv source file
            noweightlist is a array like data structure stored the attributes which should be ignored in the normalization process.
            return the cleansed inputdata using normalizating and standization
        """
    norm_data = normalizeDataset(input_file_name, columns_to_exclude)
    return standardizeData(norm_data, columns_to_exclude)

class DataDescriberUI(object):
    """Analyze input dataset, then save the dataset description in a JSON file.
       Used to display in datatable.
    Attributes:
        threshold_size: float, threshold when size of input_dataset exceed this value, then only display first 100 row in input_dataset
        dataset_description: Dict, a nested dictionary (equivalent to JSON) recording the mined dataset information.

        input_dataset: the dataset to be analyzed.

    """

    def __init__(self, threshold_size=100):
        self.threshold_size = threshold_size
        self.dataset_description = {}
        self.input_dataset = pd.DataFrame()
        self.json_data = {}

    def read_dataset_from_csv(self, file_name=None):
        try:
            self.input_dataset = pd.read_csv(file_name)
        except (UnicodeDecodeError, NameError):
            self.input_dataset = pd.read_csv(file_name, encoding='latin1')

        num_tuples, num_attributes = self.input_dataset.shape
        if num_tuples > self.threshold_size:
            self.display_dataset = self.input_dataset.head(100)
        else:
            self.display_dataset = self.input_dataset

    def get_dataset_meta_info(self):
        num_tuples, num_attributes = self.input_dataset.shape
        attribute_list = self.input_dataset.columns.tolist()

        meta_info = {"num_tuples": num_tuples, "num_attributes": num_attributes, "attribute_list": attribute_list}
        self.dataset_description['meta'] = meta_info

    def get_json_data(self):
        self.json_data = self.display_dataset.to_json(orient='records')

    def save_dataset_description_to_file(self, file_name):
        with open(file_name, 'w') as outfile:
            json.dump(self.dataset_description, outfile, indent=4)

    def save_dataset_to_file(self, file_name):

        with open(file_name, 'w') as outfile:
            outfile.write(str(self.json_data))

    def display_dataset_description(self):
        print(json.dumps(self.dataset_description, indent=4))
