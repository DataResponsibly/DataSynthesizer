import json
import random
from string import ascii_lowercase

import numpy as np
from pandas import Series, DataFrame
from sklearn.metrics import mutual_info_score, normalized_mutual_info_score


def set_random_seed(seed=0):
    random.seed(seed)
    np.random.seed(seed)


def mutual_information(labels_x: Series, labels_y: DataFrame):
    """Mutual information of distributions in format of Series or DataFrame.

    Parameters
    ----------
    labels_x : Series
    labels_y : DataFrame
    """
    if labels_y.shape[1] == 1:
        labels_y = labels_y.iloc[:, 0]
    else:
        labels_y = labels_y.apply(lambda x: ' '.join(x.values), axis=1)

    return mutual_info_score(labels_x, labels_y)


def pairwise_attributes_mutual_information(dataset):
    """Compute normalized mutual information for all pairwise attributes. Return a DataFrame."""
    sorted_columns = sorted(dataset.columns)
    mi_df = DataFrame(columns=sorted_columns, index=sorted_columns, dtype=float)
    for row in mi_df.columns:
        for col in mi_df.columns:
            mi_df.loc[row, col] = normalized_mutual_info_score(dataset[row].astype(str),
                                                               dataset[col].astype(str),
                                                               average_method='arithmetic')
    return mi_df


def normalize_given_distribution(frequencies):
    distribution = np.array(frequencies, dtype=float)
    distribution = distribution.clip(0)  # replace negative values with 0
    summation = distribution.sum()
    if summation > 0:
        if np.isinf(summation):
            return normalize_given_distribution(np.isinf(distribution))
        else:
            return distribution / summation
    else:
        return np.full_like(distribution, 1 / distribution.size)


def read_json_file(json_file):
    with open(json_file, 'r') as file:
        return json.load(file)


def infer_numerical_attributes_in_dataframe(dataframe):
    describe = dataframe.describe()
    # DataFrame.describe() usually returns 8 rows.
    if describe.shape[0] == 8:
        return set(describe.columns)
    # DataFrame.describe() returns less than 8 rows when there is no numerical attribute.
    else:
        return set()


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
