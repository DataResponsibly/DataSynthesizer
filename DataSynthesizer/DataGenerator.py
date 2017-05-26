from random import uniform

import numpy as np
import pandas as pd

from DataSynthesizer.lib.utils import set_random_seed, read_json_file


class DataGenerator(object):
    def __init__(self):
        self.n = 0

    def generate_dataset_in_random_mode(self, n, description_file, seed=0):
        self.n = n
        set_random_seed(seed)
        self.description = read_json_file(description_file)

        self.synthetic_dataset = pd.DataFrame()
        for attr in self.description['attribute_description'].keys():
            attr_description = self.description['attribute_description'][attr]
            datatype = attr_description['datatype']
            is_categorical = attr_description['is_categorical']
            if is_categorical:
                self.synthetic_dataset[attr] = np.random.choice()

    def generate_dataset_in_correlated_attribute_mode(self, n, description_file, seed=0):
        self.n = n
        set_random_seed(seed)
        self.description = read_json_file(description_file)
        self.encoded_dataset = DataGenerator.generate_encoded_dataset(self.n, self.description)

        self.synthetic_dataset = self.encoded_dataset.copy()
        for attribute in self.synthetic_dataset:
            self.synthetic_dataset.loc[:, attribute] = self.synthetic_dataset[attribute].apply(
                lambda x: self.sample_uniformly_for_attribute(attribute, int(x)))
            if self.description['attribute_description'][attribute]['datatype'] == 'int':
                self.synthetic_dataset[attribute] = self.synthetic_dataset[attribute].astype(int)

        ordered_attributes = []
        for attribute in self.description['attribute_description'].keys():
            if attribute in self.synthetic_dataset:
                ordered_attributes.append(attribute)
        self.synthetic_dataset = self.synthetic_dataset.loc[:, ordered_attributes]

    @staticmethod
    def get_sampling_order(bn):
        order = [bn[0][1][0]]
        for child, _ in bn:
            order.append(child)
        return order

    @staticmethod
    def generate_encoded_dataset(n, description):
        bn = description['bayesian_network']
        bn_root_attr = bn[0][1][0]
        root_attr_dist = description['conditional_probabilities'][bn_root_attr]

        encoded_df = pd.DataFrame(columns=DataGenerator.get_sampling_order(bn), dtype=int)
        encoded_df[bn_root_attr] = np.random.choice(len(root_attr_dist), size=n, p=root_attr_dist)

        for child, parents in bn:
            child_conditional_distributions = description['conditional_probabilities'][child]
            for parents_instance in child_conditional_distributions.keys():
                dist = child_conditional_distributions[parents_instance]
                parents_instance = list(eval(parents_instance))

                filter_condition = ''
                for parent, value in zip(parents, parents_instance):
                    filter_condition += '({0}["{1}"]=={2}) & '.format('encoded_df', parent, value)

                filter_condition = eval(filter_condition[:-3])

                size = encoded_df.loc[filter_condition].reset_index().index.size
                if size:
                    encoded_df.loc[filter_condition, child] = np.random.choice(len(dist), size=size, p=dist)

        encoded_df.dropna(inplace=True)
        encoded_df = encoded_df.iloc[:n]
        return encoded_df

    def sample_uniformly_for_attribute(self, attribute, idx):
        dist = np.array(self.description['attribute_description'][attribute]['distribution_bins']).tolist()
        if self.description['attribute_description'][attribute]['is_categorical']:
            return dist[idx]
        else:
            dist.append(2 * dist[-1] - dist[-2])
            return uniform(dist[idx], dist[idx + 1])

    def save_synthetic_data(self, to_file):
        self.synthetic_dataset.to_csv(to_file, index=False)


if __name__ == '__main__':
    from time import time

    dataset_description_file = '../out/AdultIncome/description_test.txt'

    generator = DataGenerator()

    t = time()
    generator.generate_dataset_in_correlated_attribute_mode(4000, dataset_description_file)
    print('running time: {} s'.format(time() - t))
    print(generator.synthetic_dataset.loc[:100])
