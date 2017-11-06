import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from DataSynthesizer.lib.utils import pairwise_attributes_mutual_information

matplotlib.rc('xtick', labelsize=20)
matplotlib.rc('ytick', labelsize=20)

sns.set()


class ModelInspector(object):
    def __init__(self, private_df, synthetic_df, attribute_description):
        self.private_df = private_df
        self.synthetic_df = synthetic_df
        self.attribute_description = attribute_description

    def compare_histograms(self, attribute):
        fig = plt.figure(figsize=(15, 5))
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        is_categorical = self.attribute_description[attribute]['is_categorical']
        datatype = self.attribute_description[attribute]['datatype']
        if datatype in {'integer', 'float'}:
            ax1.hist(self.private_df[attribute].dropna(), bins=15, align='left')
            ax2.hist(self.synthetic_df[attribute].dropna(), bins=15, align='left')
        elif is_categorical:
            dist_priv = self.private_df[attribute].value_counts()
            dist_synt = self.synthetic_df[attribute].value_counts()
            for idx, number in dist_priv.iteritems():
                if idx not in dist_synt.index:
                    dist_synt[idx] = 0
            for idx, number in dist_synt.iteritems():
                if idx not in dist_priv.index:
                    dist_priv[idx] = 0
            dist_priv.sort_index(inplace=True)
            dist_synt.sort_index(inplace=True)
            pos_priv = list(range(len(dist_priv)))
            pos_synt = list(range(len(dist_synt)))
            ax1.bar(pos_priv, dist_priv.values)
            ax2.bar(pos_synt, dist_synt.values)
            ax1.set_xticks(np.arange(min(pos_priv), max(pos_priv) + 1, 1.0))
            ax2.set_xticks(np.arange(min(pos_synt), max(pos_synt) + 1, 1.0))
            ax1.set_xticklabels(dist_priv.index.tolist(), fontsize=15)
            ax2.set_xticklabels(dist_synt.index.tolist(), fontsize=15)

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

    def mutual_information_heatmap(self):
        private_mi = pairwise_attributes_mutual_information(self.private_df)
        synthetic_mi = pairwise_attributes_mutual_information(self.synthetic_df)

        fig = plt.figure(figsize=(15, 6))
        fig.suptitle('Pairwise Mutual Information Comparison (Private vs Synthetic)', fontsize=20)
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        sns.heatmap(private_mi, ax=ax1)
        sns.heatmap(synthetic_mi, ax=ax2)
        ax1.set_title('Private, max=1', fontsize=15)
        ax2.set_title('Synthetic, max=1', fontsize=15)
        fig.autofmt_xdate()
        fig.tight_layout()
        plt.subplots_adjust(top=0.83)


if __name__ == '__main__':
    # Directories of input and output files
    input_dataset_file = '../datasets/AdultIncomeData/adult.csv'
    dataset_description_file = '../output/description/AdultIncomeData_description.txt'
    synthetic_dataset_file = '../output/synthetic_data/AdultIncomeData_synthetic.csv'

    df = pd.read_csv(input_dataset_file)
    print(df.head(5))
