import json
import random

import numpy as np
import pandas as pd
from dateutil.parser import parse
from sklearn.metrics import mutual_info_score, normalized_mutual_info_score


def set_random_seed(seed=0):
    random.seed(seed)
    np.random.seed(seed)


def is_datetime(date_string):
    weekdays = [("Mon", "Monday"),
                ("Tue", "Tuesday"),
                ("Wed", "Wednesday"),
                ("Thu", "Thursday"),
                ("Fri", "Friday"),
                ("Sat", "Saturday"),
                ("Sun", "Sunday")]
    months = [("Jan", "January"),
              ("Feb", "February"),
              ("Mar", "March"),
              ("Apr", "April"),
              ("May", "May"),
              ("Jun", "June"),
              ("Jul", "July"),
              ("Aug", "August"),
              ("Sep", "Sept", "September"),
              ("Oct", "October"),
              ("Nov", "November"),
              ("Dec", "December")]
    for entry in weekdays + months:
        for value in entry:
            if date_string.lower() == value.lower():
                return False
    try:
        parse(date_string)
        return True
    except ValueError:
        return False


def mutual_information(labels_true, labels_pred):
    """Mutual information of distributions in format of pd.Series or pd.DataFrame.

    Args:
        labels_true: Series or DataFrame
        labels_pred: Series or DataFrame
    """
    if isinstance(labels_true, pd.DataFrame):
        labels_true = labels_true.astype(str).apply(lambda x: ' '.join(x.tolist()), axis=1)
    if isinstance(labels_pred, pd.DataFrame):
        labels_pred = labels_pred.astype(str).apply(lambda x: ' '.join(x.tolist()), axis=1)

    assert isinstance(labels_true, pd.Series)
    assert isinstance(labels_pred, pd.Series)

    return mutual_info_score(labels_true.astype(str), labels_pred.astype(str))


def pairwise_attributes_mutual_information(dataset):
    """Compute mutual information for all pairwise attributes. Return a DataFrame."""
    mi_df = pd.DataFrame(columns=dataset.columns, index=dataset.columns, dtype=float)
    for row in mi_df.columns:
        for col in mi_df.columns:
            mi_df.loc[row, col] = normalized_mutual_info_score(dataset[row], dataset[col])
    return mi_df


def normalize_given_distribution(frequencies):
    distribution = np.array(frequencies, dtype=float)
    distribution = distribution.clip(0)  # replace negative values with 0
    if distribution.sum() == 0:
        distribution.fill(1 / distribution.size)
    else:
        distribution = distribution / distribution.sum()
    return distribution


def read_json_file(json_file):
    with open(json_file, 'r') as file:
        return json.load(file)


def get_numeric_column_list_from_dataframe(dataframe):
    return dataframe.describe().columns.tolist()


def display_bayesian_network(bn):
    length = 0
    for child, _ in bn:
        if len(child) > length:
            length = len(child)

    print('Constructed Bayesian network:')
    for child, parents in bn:
        print("    {0:{width}} has parents {1}.".format(child, parents, width=length))
