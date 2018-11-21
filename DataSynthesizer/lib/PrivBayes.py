import random
import warnings
from itertools import combinations, product
from math import log, ceil
from multiprocessing.pool import Pool

import numpy as np
import pandas as pd
from scipy.optimize import fsolve

from lib.utils import mutual_information, normalize_given_distribution

"""
This module is based on PrivBayes in the following paper:

Zhang J, Cormode G, Procopiuc CM, Srivastava D, Xiao X.
PrivBayes: Private Data Release via Bayesian Networks.
"""


def sensitivity(num_tuples):
    """Sensitivity function for Bayesian network construction. PrivBayes Lemma 1.

    Parameters
    ----------
    num_tuples : int
        Number of tuples in sensitive dataset.

    Return
    --------
    int
        Sensitivity value.
    """
    a = (2 / num_tuples) * log((num_tuples + 1) / 2)
    b = (1 - 1 / num_tuples) * log(1 + 2 / (num_tuples - 1))
    return a + b


def delta(num_attributes, num_tuples, epsilon):
    """Computing delta, which is a factor when applying differential privacy.

    More info is in PrivBayes Section 4.2 "A First-Cut Solution".

    Parameters
    ----------
    num_attributes : int
        Number of attributes in dataset.
    num_tuples : int
        Number of tuples in dataset.
    epsilon : float
        Parameter of differential privacy.
    """
    return 2 * (num_attributes - 1) * sensitivity(num_tuples) / epsilon


def usefulness_minus_target(k, num_attributes, num_tuples, target_usefulness=5, epsilon=0.1):
    """Usefulness function in PrivBayes.

    Parameters
    ----------
    k : int
        Max number of degree in Bayesian networks construction
    num_attributes : int
        Number of attributes in dataset.
    num_tuples : int
        Number of tuples in dataset.
    target_usefulness : int or float
    epsilon : float
        Parameter of differential privacy.
    """
    if k == num_attributes:
        print('here')
        usefulness = target_usefulness
    else:
        usefulness = num_tuples * epsilon / ((num_attributes - k) * (2 ** (k + 3)))  # PrivBayes Lemma 3
    return usefulness - target_usefulness


def calculate_k(num_attributes, num_tuples, target_usefulness=4, epsilon=0.1):
    """Calculate the maximum degree when constructing Bayesian networks. See PrivBayes Lemma 3."""
    default_k = 3
    initial_usefulness = usefulness_minus_target(default_k, num_attributes, num_tuples, 0, epsilon)
    if initial_usefulness > target_usefulness:
        return default_k
    else:
        arguments = (num_attributes, num_tuples, target_usefulness, epsilon)
        warnings.filterwarnings("error")
        try:
            ans = fsolve(usefulness_minus_target, int(num_attributes / 2), args=arguments)[0]
            ans = ceil(ans)
        except RuntimeWarning:
            print("Warning: k is not properly computed!")
            ans = default_k
        if ans < 1 or ans > num_attributes:
            ans = default_k
        return ans


def worker(paras):
    child, V, num_parents, split, dataset = paras
    parents_pair_list = []
    mutual_info_list = []

    if split + num_parents - 1 < len(V):
        for other_parents in combinations(V[split + 1:], num_parents - 1):
            parents = list(other_parents)
            parents.append(V[split])
            parents_pair_list.append((child, parents))
            # TODO consider to change the computation of MI by combined integers instead of strings.
            mi = mutual_information(dataset[child], dataset[parents])
            mutual_info_list.append(mi)

    return parents_pair_list, mutual_info_list


def greedy_bayes(dataset, k=2, epsilon=0):
    """Construct a Bayesian Network (BN) using greedy algorithm.

    Parameters
    ----------
    dataset : DataFrame
        Input dataset, which only contains categorical attributes.
    k : int
        Maximum degree of the constructed BN. If k=0, k is automatically calculated.
    epsilon : float
        Parameter of differential privacy.
    """
    dataset = dataset.astype(str, copy=False)
    num_tuples, num_attributes = dataset.shape
    if not k:
        k = calculate_k(num_attributes, num_tuples)

    print('================ Constructing Bayesian Network (BN) ================')
    root_attribute = random.choice(dataset.columns)
    V = [root_attribute]
    rest_attributes = set(dataset.columns)
    rest_attributes.remove(root_attribute)
    print(f'Adding ROOT {root_attribute}')
    N = []
    while rest_attributes:
        parents_pair_list = []
        mutual_info_list = []

        num_parents = min(len(V), k)
        tasks = [(child, V, num_parents, split, dataset) for child, split in
                 product(rest_attributes, range(len(V) - num_parents + 1))]
        with Pool() as pool:
            res_list = pool.map(worker, tasks)

        for res in res_list:
            parents_pair_list += res[0]
            mutual_info_list += res[1]

        if epsilon:
            sampling_distribution = exponential_mechanism(dataset, mutual_info_list, epsilon)
            idx = np.random.choice(list(range(len(mutual_info_list))), p=sampling_distribution)
        else:
            idx = mutual_info_list.index(max(mutual_info_list))

        N.append(parents_pair_list[idx])
        adding_attribute = parents_pair_list[idx][0]
        V.append(adding_attribute)
        rest_attributes.remove(adding_attribute)
        print(f'Adding attribute {adding_attribute}')

    print('========================= BN constructed =========================')

    return N


def exponential_mechanism(dataset, mutual_info_list, epsilon=0.1):
    """Applied in Exponential Mechanism to sample outcomes."""
    num_tuples, num_attributes = dataset.shape
    mi_array = np.array(mutual_info_list)
    mi_array = mi_array / (2 * delta(num_attributes, num_tuples, epsilon))
    mi_array = np.exp(mi_array)
    mi_array = normalize_given_distribution(mi_array)
    return mi_array


def laplace_noise_parameter(k, num_attributes, num_tuples, epsilon):
    """The noises injected into conditional distributions. PrivBayes Algorithm 1."""
    return 4 * (num_attributes - k) / (num_tuples * epsilon)


def get_noisy_distribution_of_attributes(attributes, encoded_dataset, epsilon=0.1):
    data = encoded_dataset.copy().loc[:, attributes]
    data['count'] = 1
    stats = data.groupby(attributes).sum()

    iterables = [range(int(encoded_dataset[attr].max()) + 1) for attr in attributes]
    full_space = pd.DataFrame(columns=attributes, data=list(product(*iterables)))
    stats.reset_index(inplace=True)
    stats = pd.merge(full_space, stats, how='left')
    stats.fillna(0, inplace=True)

    if epsilon:
        k = len(attributes) - 1
        num_tuples, num_attributes = encoded_dataset.shape
        noise_para = laplace_noise_parameter(k, num_attributes, num_tuples, epsilon)
        laplace_noises = np.random.laplace(0, scale=noise_para, size=stats.index.size)
        stats['count'] += laplace_noises
        stats.loc[stats['count'] < 0, 'count'] = 0

    return stats


def construct_noisy_conditional_distributions(bayesian_network, encoded_dataset, epsilon=0.1):
    """See more in Algorithm 1 in PrivBayes.

    """

    k = len(bayesian_network[-1][1])
    conditional_distributions = {}

    # first k+1 attributes
    root = bayesian_network[0][1][0]
    kplus1_attributes = [root]
    for child, _ in bayesian_network[:k]:
        kplus1_attributes.append(child)

    noisy_dist_of_kplus1_attributes = get_noisy_distribution_of_attributes(kplus1_attributes, encoded_dataset, epsilon)

    # generate noisy distribution of root attribute.
    root_stats = noisy_dist_of_kplus1_attributes.loc[:, [root, 'count']].groupby(root).sum()['count']
    conditional_distributions[root] = normalize_given_distribution(root_stats).tolist()

    for idx, (child, parents) in enumerate(bayesian_network):
        conditional_distributions[child] = {}

        if idx < k:
            stats = noisy_dist_of_kplus1_attributes.copy().loc[:, parents + [child, 'count']]
        else:
            stats = get_noisy_distribution_of_attributes(parents + [child], encoded_dataset, epsilon)

        stats = pd.DataFrame(stats.loc[:, parents + [child, 'count']].groupby(parents + [child]).sum())

        if len(parents) == 1:
            for parent_instance in stats.index.levels[0]:
                dist = normalize_given_distribution(stats.loc[parent_instance]['count']).tolist()
                conditional_distributions[child][str([parent_instance])] = dist
        else:
            for parents_instance in product(*stats.index.levels[:-1]):
                dist = normalize_given_distribution(stats.loc[parents_instance]['count']).tolist()
                conditional_distributions[child][str(list(parents_instance))] = dist

    return conditional_distributions
