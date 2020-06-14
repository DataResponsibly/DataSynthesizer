from typing import List

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from numpy import arange
from pandas import DataFrame, Series
from scipy.stats import entropy, ks_2samp

from DataSynthesizer.lib.utils import pairwise_attributes_mutual_information, normalize_given_distribution

matplotlib.rc('xtick', labelsize=20)
matplotlib.rc('ytick', labelsize=20)

sns.set()


def get_distribution_of_categorical_attribute(attribute: Series, indicies=None):
    distribution = attribute.dropna().value_counts()
    if indicies is not None:
        for idx in set(indicies) - set(distribution.index):
            distribution.loc[idx] = 0
    distribution.sort_index(inplace=True)
    return distribution / sum(distribution)


def kl_test(df_in: DataFrame, df_out: DataFrame, attr: str):
    """
    df_in: the sensitive dataset
    df_out: the synthetic dataset
    attr: the attribute that will be calculated for KL-divergence.
    """
    distribution_in = get_distribution_of_categorical_attribute(df_in[attr])
    distribution_out = get_distribution_of_categorical_attribute(df_out[attr], distribution_in.index)
    return entropy(distribution_out, distribution_in)


def ks_test(df_in: DataFrame, df_out: DataFrame, attr: str):
    """
    df_in: the sensitive dataset
    df_out: the synthetic dataset
    attr: the attribute that will be calculated for Two-sample Kolmogorov–Smirnov test.
    """
    return ks_2samp(df_in[attr], df_out[attr])[0]


class ModelInspector(object):
    def __init__(self, private_df: DataFrame, synthetic_df: DataFrame, attribute_description):
        self.private_df = private_df
        self.synthetic_df = synthetic_df
        self.attribute_description = attribute_description

        self.candidate_keys = set()
        for attr in synthetic_df:
            is_candidate = self.attribute_description[attr]['is_candidate_key']
            if is_candidate:
                self.candidate_keys.add(attr)

        self.private_df.drop(columns=self.candidate_keys, inplace=True)
        self.synthetic_df.drop(columns=self.candidate_keys, inplace=True)

    def compare_histograms(self, attribute):
        datatype = self.attribute_description[attribute]['data_type']
        is_categorical = self.attribute_description[attribute]['is_categorical']

        # ignore datetime attributes, since they are converted into timestamps
        if datatype == 'DateTime':
            return
        # ignore non-categorical string attributes
        elif datatype == 'String' and not is_categorical:
            return
        elif attribute in self.candidate_keys:
            return
        else:
            fig = plt.figure(figsize=(15, 5), dpi=120)
            ax1 = fig.add_subplot(121)
            ax2 = fig.add_subplot(122)

            if is_categorical:
                dist_priv = self.private_df[attribute].value_counts()
                dist_synt = self.synthetic_df[attribute].value_counts()
                for idx, number in dist_priv.iteritems():
                    if idx not in dist_synt.index:
                        dist_synt.loc[idx] = 0
                for idx, number in dist_synt.iteritems():
                    if idx not in dist_priv.index:
                        dist_priv.loc[idx] = 0
                dist_priv.index = [str(i) for i in dist_priv.index]
                dist_synt.index = [str(i) for i in dist_synt.index]
                dist_priv.sort_index(inplace=True)
                dist_synt.sort_index(inplace=True)
                pos_priv = list(range(len(dist_priv)))
                pos_synt = list(range(len(dist_synt)))
                ax1.bar(pos_priv, normalize_given_distribution(dist_priv.values))
                ax2.bar(pos_synt, normalize_given_distribution(dist_synt.values))
                ax1.set_xticks(arange(min(pos_priv), max(pos_priv) + 1, 1.0))
                ax2.set_xticks(arange(min(pos_synt), max(pos_synt) + 1, 1.0))
                ax1.set_xticklabels(dist_priv.index.tolist(), fontsize=15)
                ax2.set_xticklabels(dist_synt.index.tolist(), fontsize=15)
            # the rest are non-categorical numeric attributes.
            else:
                ax1.hist(self.private_df[attribute].dropna(), bins=15, align='left', density=True)
                ax2.hist(self.synthetic_df[attribute].dropna(), bins=15, align='left', density=True)

            ax1_x_min, ax1_x_max = ax1.get_xlim()
            ax2_x_min, ax2_x_max = ax2.get_xlim()
            ax1_y_min, ax1_y_max = ax1.get_ylim()
            ax2_y_min, ax2_y_max = ax2.get_ylim()
            x_min = min(ax1_x_min, ax2_x_min)
            x_max = max(ax1_x_max, ax2_x_max)
            y_min = min(ax1_y_min, ax2_y_min)
            y_max = max(ax1_y_max, ax2_y_max)
            ax1.set_xlim([x_min, x_max])
            ax1.set_ylim([y_min, y_max])
            ax2.set_xlim([x_min, x_max])
            ax2.set_ylim([y_min, y_max])
            fig.autofmt_xdate()

    def mutual_information_heatmap(self, attributes: List = None):
        if attributes:
            private_df = self.private_df[attributes]
            synthetic_df = self.synthetic_df[attributes]
        else:
            private_df = self.private_df
            synthetic_df = self.synthetic_df

        private_mi = pairwise_attributes_mutual_information(private_df)
        synthetic_mi = pairwise_attributes_mutual_information(synthetic_df)

        fig = plt.figure(figsize=(15, 6), dpi=120)
        fig.suptitle('Pairwise Mutual Information Comparison (Private vs Synthetic)', fontsize=20)
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        sns.heatmap(private_mi, ax=ax1, cmap="Blues")
        sns.heatmap(synthetic_mi, ax=ax2, cmap="Blues")
        ax1.set_title('Private, max=1', fontsize=15)
        ax2.set_title('Synthetic, max=1', fontsize=15)
        fig.autofmt_xdate()
        fig.tight_layout()
        plt.subplots_adjust(top=0.83)
