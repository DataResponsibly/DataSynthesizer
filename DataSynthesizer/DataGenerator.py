from numpy import random
from pandas import DataFrame

from DataSynthesizer.datatypes.utils.AttributeLoader import parse_json
from DataSynthesizer.lib.utils import set_random_seed, read_json_file, generate_random_string


class DataGenerator(object):
    def __init__(self):
        self.n = 0
        self.synthetic_dataset = None
        self.description = {}
        self.encoded_dataset = None

    def generate_dataset_in_random_mode(self, n, description_file, seed=0, minimum=0, maximum=100):
        set_random_seed(seed)
        description = read_json_file(description_file)

        self.synthetic_dataset = DataFrame()
        for attr in description['attribute_description'].keys():
            attr_info = description['attribute_description'][attr]
            datatype = attr_info['data_type']
            is_categorical = attr_info['is_categorical']
            is_candidate_key = attr_info['is_candidate_key']
            if is_candidate_key:
                self.synthetic_dataset[attr] = parse_json(attr_info).generate_values_as_candidate_key(n)
            elif is_categorical:
                self.synthetic_dataset[attr] = random.choice(attr_info['distribution_bins'], n)
            elif datatype == 'String':
                length = random.randint(attr_info['min'], attr_info['max'] + 1)
                self.synthetic_dataset[attr] = length
                self.synthetic_dataset[attr] = self.synthetic_dataset[attr].map(lambda x: generate_random_string(x))
            else:
                if datatype == 'Integer':
                    self.synthetic_dataset[attr] = random.randint(minimum, maximum + 1, n)
                else:
                    self.synthetic_dataset[attr] = random.uniform(minimum, maximum, n)

    def generate_dataset_in_independent_mode(self, n, description_file, seed=0):
        set_random_seed(seed)
        self.description = read_json_file(description_file)

        all_attributes = self.description['meta']['all_attributes']
        candidate_keys = set(self.description['meta']['candidate_keys'])
        self.synthetic_dataset = DataFrame(columns=all_attributes)
        for attr in all_attributes:
            attr_info = self.description['attribute_description'][attr]
            column = parse_json(attr_info)

            if attr in candidate_keys:
                self.synthetic_dataset[attr] = column.generate_values_as_candidate_key(n)
            else:
                binning_indices = column.sample_binning_indices_in_independent_attribute_mode(n)
                self.synthetic_dataset[attr] = column.sample_values_from_binning_indices(binning_indices)

    def generate_dataset_in_correlated_attribute_mode(self, n, description_file, seed=0):
        set_random_seed(seed)
        self.n = n
        self.description = read_json_file(description_file)

        all_attributes = self.description['meta']['all_attributes']
        candidate_keys = set(self.description['meta']['candidate_keys'])
        self.encoded_dataset = DataGenerator.generate_encoded_dataset(self.n, self.description)
        self.synthetic_dataset = DataFrame(columns=all_attributes)
        for attr in all_attributes:
            attr_info = self.description['attribute_description'][attr]
            column = parse_json(attr_info)

            if attr in self.encoded_dataset:
                self.synthetic_dataset[attr] = column.sample_values_from_binning_indices(self.encoded_dataset[attr])
            elif attr in candidate_keys:
                self.synthetic_dataset[attr] = column.generate_values_as_candidate_key(n)
            else:
                # for attributes not in BN or candidate keys, use independent attribute mode.
                binning_indices = column.sample_binning_indices_in_independent_attribute_mode(n)
                self.synthetic_dataset[attr] = column.sample_values_from_binning_indices(binning_indices)

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
        encoded_df = DataFrame(columns=DataGenerator.get_sampling_order(bn))
        encoded_df[bn_root_attr] = random.choice(len(root_attr_dist), size=n, p=root_attr_dist)

        for child, parents in bn:
            child_conditional_distributions = description['conditional_probabilities'][child]
            for parents_instance in child_conditional_distributions.keys():
                dist = child_conditional_distributions[parents_instance]
                parents_instance = list(eval(parents_instance))

                filter_condition = ''
                for parent, value in zip(parents, parents_instance):
                    filter_condition += f"(encoded_df['{parent}']=={value})&"

                filter_condition = eval(filter_condition[:-1])

                size = encoded_df[filter_condition].shape[0]
                if size:
                    encoded_df.loc[filter_condition, child] = random.choice(len(dist), size=size, p=dist)

            unconditioned_distribution = description['attribute_description'][child]['distribution_probabilities']
            encoded_df.loc[encoded_df[child].isnull(), child] = random.choice(len(unconditioned_distribution),
                                                                              size=encoded_df[child].isnull().sum(),
                                                                              p=unconditioned_distribution)
        encoded_df[encoded_df.columns] = encoded_df[encoded_df.columns].astype(int)
        return encoded_df

    def save_synthetic_data(self, to_file):
        self.synthetic_dataset.to_csv(to_file, index=False)


if __name__ == '__main__':
    from time import time

    dataset_description_file = '../out/AdultIncome/description_test.txt'
    generator = DataGenerator()

    t = time()
    generator.generate_dataset_in_correlated_attribute_mode(51, dataset_description_file)
    print('running time: {} s'.format(time() - t))
    print(generator.synthetic_dataset.loc[:50])
