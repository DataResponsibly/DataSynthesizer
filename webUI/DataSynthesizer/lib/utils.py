import json
import random
from string import ascii_lowercase

import numpy as np
import pandas as pd
from sklearn.metrics import mutual_info_score, normalized_mutual_info_score


def set_random_seed(seed=0):
    random.seed(seed)
    np.random.seed(seed)


def mutual_information(labels_true, labels_pred):
    """Mutual information of distributions in format of pd.Series or pd.DataFrame.

    Parameters
    ----------
        labels_true : Series or DataFrame
        labels_pred : Series or DataFrame
    """
    if isinstance(labels_true, pd.DataFrame):
        labels_true = labels_true.astype(str).apply(lambda x: ' '.join(x.tolist()), axis=1)
    if isinstance(labels_pred, pd.DataFrame):
        labels_pred = labels_pred.astype(str).apply(lambda x: ' '.join(x.tolist()), axis=1)

    assert isinstance(labels_pred, pd.Series)
    return mutual_info_score(labels_true.astype(str), labels_pred.astype(str))


def pairwise_attributes_mutual_information(dataset):
    """Compute normalized mutual information for all pairwise attributes. Return a DataFrame."""
    mi_df = pd.DataFrame(columns=dataset.columns, index=dataset.columns, dtype=float)
    for row in mi_df.columns:
        for col in mi_df.columns:
            mi_df.loc[row, col] = normalized_mutual_info_score(dataset[row].astype(str),
                                                               dataset[col].astype(str))
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


def infer_numerical_attributes_in_dataframe(dataframe):
    describe = dataframe.describe()
    # pd.DataFrame.describe() usually returns 8 rows.
    if describe.shape[0] == 8:
        return describe.columns.tolist()
    # pd.DataFrame.describe() returns less than 8 rows when there is no numerical attribute.
    else:
        return []


def display_bayesian_network(bn):
    length = 0
    for child, _ in bn:
        if len(child) > length:
            length = len(child)

    print('Constructed Bayesian network:')
    for child, parents in bn:
        print("    {0:{width}} has parents {1}.".format(child, parents, width=length))


def generate_random_string(length):
    return ''.join(np.random.choice(list(ascii_lowercase), size=length))
