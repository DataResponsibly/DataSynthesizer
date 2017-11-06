from random import uniform

import numpy as np
import pandas as pd

from DataSynthesizer.lib.utils import set_random_seed, read_json_file, generate_random_string


class DataGenerator(object):
    def __init__(self):
        self.n = 0
        self.synthetic_dataset = pd.DataFrame()

    def generate_dataset_in_random_mode(self, n, description_file, seed=0):
        set_random_seed(seed)
        description = read_json_file(description_file)

        self.synthetic_dataset = pd.DataFrame()
        for attr in description['attribute_description'].keys():
            attr_description = description['attribute_description'][attr]
            datatype = attr_description['datatype']
            is_categorical = attr_description['is_categorical']
            if is_categorical:
                self.synthetic_dataset[attr] = np.random.choice(attr_description['distribution_bins'], n)
            elif datatype == 'string':
                length = np.random.randint(attr_description['min_length'], attr_description['max_length'])
                self.synthetic_dataset[attr] = length
                self.synthetic_dataset[attr] = self.synthetic_dataset[attr].map(lambda x: generate_random_string(x))
            else:
                minimum, maximum = attr_description['min'], attr_description['max']
                if datatype == 'integer':
                    self.synthetic_dataset[attr] = np.random.randint(minimum, maximum + 1, n)
                else:
                    self.synthetic_dataset[attr] = np.random.uniform(minimum, maximum, n)

    def generate_dataset_in_independent_mode(self, n, description_file, seed=0):
        set_random_seed(seed)
        self.description = read_json_file(description_file)

        attributes = self.description['meta']['attribute_list']
        self.encoded_dataset = pd.DataFrame(columns=attributes, index=list(range(n)))
        for attr in attributes:
            attr_info = self.description['attribute_description'][attr]
            bins = attr_info['distribution_bins']
            probs = attr_info['distribution_probabilities']
            self.encoded_dataset[attr] = np.random.choice(list(range(len(bins))), size=n, p=probs)

        self.sample_from_encoded_dataset()

    def generate_dataset_in_correlated_attribute_mode(self, n, description_file, seed=0):
        self.n = n
        set_random_seed(seed)
        self.description = read_json_file(description_file)
        self.encoded_dataset = DataGenerator.generate_encoded_dataset(self.n, self.description)

        for attr in self.description['meta']['ignored_attributes_by_BN']:
            attr_info = self.description['attribute_description'][attr]
            bins = attr_info['distribution_bins']
            probs = attr_info['distribution_probabilities']
            self.encoded_dataset[attr] = np.random.choice(list(range(len(bins))), size=n, p=probs)

        self.sample_from_encoded_dataset()

    def sample_from_encoded_dataset(self):
        self.synthetic_dataset = self.encoded_dataset.copy()
        for attribute in self.synthetic_dataset:
            datatype = self.description['attribute_description'][attribute]['datatype']
            not_categorical = not self.description['attribute_description'][attribute]['is_categorical']
            self.synthetic_dataset[attribute] = self.synthetic_dataset[attribute].apply(
                lambda x: self.sample_uniformly_for_attribute(attribute, int(x)))
            if datatype == 'integer':
                self.synthetic_dataset[attribute] = self.synthetic_dataset[~self.synthetic_dataset[attribute].isnull()][
                    attribute].astype(int)
            elif datatype == 'string' and not_categorical:
                self.synthetic_dataset[attribute] = self.synthetic_dataset[~self.synthetic_dataset[attribute].isnull()][
                    attribute].map(lambda x: generate_random_string(int(x)))

        self.synthetic_dataset = self.synthetic_dataset.loc[:, self.description['meta']['attribute_list']]

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

                size = encoded_df[filter_condition].shape[0]
                if size:
                    encoded_df.loc[filter_condition, child] = np.random.choice(len(dist), size=size, p=dist)

            unconditioned_distribution = description['attribute_description'][child]['distribution_probabilities']
            encoded_df.loc[encoded_df[child].isnull(), child] = np.random.choice(len(unconditioned_distribution),
                                                                                 size=encoded_df[child].isnull().sum(),
                                                                                 p=unconditioned_distribution)
        return encoded_df

    def sample_uniformly_for_attribute(self, attribute, idx):
        dist = np.array(self.description['attribute_description'][attribute]['distribution_bins']).tolist()
        if idx == len(dist):
            return np.nan
        elif self.description['attribute_description'][attribute]['is_categorical']:
            return dist[idx]
        else:
            dist.append(2 * dist[-1] - dist[-2])
            return uniform(dist[idx], dist[idx + 1])

    def save_synthetic_data(self, to_file):
        self.synthetic_dataset.to_csv(to_file, index=False)


if __name__ == '__main__':
    from time import time

    dataset_description_file = '../out/AdultIncome/description_test.txt'
    dataset_description_file = '/home/haoyue/GitLab/data-responsibly-webUI/dataResponsiblyUI/static/intermediatedata/1498175138.8088856_description.txt'

    generator = DataGenerator()

    t = time()
    generator.generate_dataset_in_correlated_attribute_mode(51, dataset_description_file)
    print('running time: {} s'.format(time() - t))
    print(generator.synthetic_dataset.loc[:50])
