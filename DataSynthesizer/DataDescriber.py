import json

import numpy as np
import pandas as pd
from dateutil.parser import parse

import DataSynthesizer.lib.utils as utils
from DataSynthesizer.lib.PrivBayes import greedy_bayes, construct_noisy_conditional_distributions


# TODO allow users to specify Null values.
# TODO detect datetime formats.
class DataDescriber(object):
    """Analyze input dataset, then save the dataset description in a JSON file.

    Attributes
    ----------
        histogram_size : int
            Number of bins in histograms.
        threshold_of_categorical_variable : int
            Categorical variables have no more than "this number" distinct values.
        attribute_to_datatype : dict
            Mappings of {attribute: datatype}, e.g., {"age": "int", "gender": "string"}.
        attribute_to_is_categorical : dict
            Mappings of {attribute: boolean},, e.g., {"gender":True, "age":False}.
        ignored_attributes_by_BN : list
            Attributes containing only unique values are ignored in BN construction.
        dataset_description: dict
            Nested dictionary (equivalent to JSON) recording the mined dataset information.
        input_dataset : DataFrame
            The dataset to be analyzed.
        bayesian_network : list of [child, [parent,]] in constructed BN.
        encoded_dataset : DataFrame
            A discrete dataset taken as input by PrivBayes in correlated attribute mode.
        datatypes : set
            The data types supported by DataSynthesizer.
        numerical_datatypes : set
            The datatypes which are numerical.
    """

    def __init__(self, histogram_size=20, threshold_of_categorical_variable=10):
        self.histogram_size = histogram_size
        self.threshold_of_categorical_variables = threshold_of_categorical_variable
        self.attribute_to_datatype = {}
        self.attribute_to_is_categorical = {}
        self.ignored_attributes_by_BN = []
        self.dataset_description = {}
        self.input_dataset = None
        self.bayesian_network = []
        self.encoded_dataset = None

        self.datatypes = {'integer', 'float', 'datetime', 'string'}
        self.numerical_datatypes = {'integer', 'float', 'datetime'}

    def describe_dataset_in_random_mode(self,
                                        dataset_file,
                                        attribute_to_datatype={},
                                        attribute_to_is_categorical={},
                                        seed=0):
        self.describe_dataset_in_independent_attribute_mode(dataset_file,
                                                            attribute_to_datatype=attribute_to_datatype,
                                                            attribute_to_is_categorical=attribute_to_is_categorical,
                                                            seed=seed)
        # After running independent attribute mode, 1) make all distributions uniform; 2) set missing rate to zero.
        for attr in self.dataset_description['attribute_description']:
            distribution = self.dataset_description['attribute_description'][attr]['distribution_probabilities']
            uniform_distribution = np.ones_like(distribution)
            uniform_distribution = utils.normalize_given_distribution(uniform_distribution).tolist()
            self.dataset_description['attribute_description'][attr]['distribution_probabilities'] = uniform_distribution
            self.dataset_description['attribute_description'][attr]['missing_rate'] = 0

    def describe_dataset_in_independent_attribute_mode(self,
                                                       dataset_file,
                                                       epsilon=0.1,
                                                       attribute_to_datatype={},
                                                       attribute_to_is_categorical={},
                                                       seed=0):
        utils.set_random_seed(seed)
        self.attribute_to_datatype = dict(attribute_to_datatype)
        self.attribute_to_is_categorical = dict(attribute_to_is_categorical)
        self.read_dataset_from_csv(dataset_file)
        self.get_dataset_meta_info()
        self.infer_attribute_datatypes()
        self.infer_domains()
        self.inject_laplace_noise_into_distribution_per_attribute(epsilon)

    def describe_dataset_in_correlated_attribute_mode(self,
                                                      dataset_file,
                                                      k=0,
                                                      epsilon=0.1,
                                                      attribute_to_datatype={},
                                                      attribute_to_is_categorical={},
                                                      seed=0):
        """Generate dataset description using correlated attribute mode.

        Users only need to call this function. It packages the rest functions.

        Parameters
        ----------
            dataset_file : str
                File name (with directory) of the sensitive dataset as input in csv format.
            k : int
                Maximum number of parents in Bayesian network.
            epsilon : float
                A parameter in differential privacy.
            attribute_to_datatype : dict
                Mappings of {attribute: datatype}, e.g., {"age": "int"}.
            attribute_to_is_categorical : dict
                Mappings of {attribute: boolean},, e.g., {"age":False}.
            seed : int or float
                Seed the random number generator.
        """

        self.describe_dataset_in_independent_attribute_mode(dataset_file, epsilon, attribute_to_datatype,
                                                            attribute_to_is_categorical, seed)
        self.encoded_dataset = self.encode_dataset_into_interval_indices()
        self.bayesian_network = greedy_bayes(self.input_dataset[self.encoded_dataset.columns], k, epsilon)
        self.dataset_description['bayesian_network'] = self.bayesian_network
        self.dataset_description['conditional_probabilities'] = construct_noisy_conditional_distributions(
            self.bayesian_network, self.encoded_dataset, epsilon)

    def read_dataset_from_csv(self, file_name=None):
        try:
            self.input_dataset = pd.read_csv(file_name)
        except (UnicodeDecodeError, NameError):
            self.input_dataset = pd.read_csv(file_name, encoding='latin1')

        # find attributes whose values are all unique (e.g., ID) or missing (i.e., empty domain).
        for attribute in self.input_dataset:
            if self.input_dataset[attribute].dropna().is_unique:
                self.ignored_attributes_by_BN.append(attribute)

    def get_dataset_meta_info(self):
        self.dataset_description['meta'] = {"num_tuples": self.input_dataset.index.size,
                                            "num_attributes": self.input_dataset.columns.size,
                                            "attribute_list": self.input_dataset.columns.tolist()}

    def infer_attribute_datatypes(self):
        attributes_with_unspecified_datatype = set(self.input_dataset.columns) - set(self.attribute_to_datatype)
        numeric_attributes = set(utils.get_numeric_column_list_from_dataframe(self.input_dataset))
        for attr in attributes_with_unspecified_datatype:
            current_column = self.input_dataset[attr].dropna()

            # current attribute is either int or float.
            if attr in numeric_attributes:
                if (current_column == current_column.astype(int)).all():
                    self.attribute_to_datatype[attr] = 'integer'
                else:
                    self.attribute_to_datatype[attr] = 'float'

            # current attribute is either string or datetime.
            else:
                # Sample 20 values to test whether the elements of current attribute are of type datetime.
                tests = current_column.sample(20, replace=True).map(utils.is_datetime)
                if all(tests):
                    self.attribute_to_datatype[attr] = 'datetime'
                else:
                    self.attribute_to_datatype[attr] = 'string'

    def is_categorical(self, attribute):
        """Detect whether a column is categorical.

        Parameters
        ----------
            attribute : str
                Attribute name.
        """
        if attribute in self.attribute_to_is_categorical:
            return self.attribute_to_is_categorical[attribute]
        else:
            if self.input_dataset[attribute].dropna().unique().size <= self.threshold_of_categorical_variables:
                return True
            else:
                return False

    def infer_domain_of_numeric_attribute(self, attribute):
        datatype = self.attribute_to_datatype[attribute]
        column_values = self.input_dataset[attribute]
        column_dropna = column_values.dropna()

        # use timestamp to represent datetime
        if datatype == 'datetime':
            column_dropna = column_dropna.map(lambda x: parse(x).timestamp())

        is_categorical_attr = self.is_categorical(attribute)
        if is_categorical_attr:
            distribution = column_dropna.value_counts()
            distribution.sort_index(inplace=True)
            distribution_probabilities = utils.normalize_given_distribution(distribution).tolist()
            distribution_bins = np.array(distribution.index).tolist()
        else:
            distribution = np.histogram(column_dropna, bins=self.histogram_size)
            distribution_probabilities = utils.normalize_given_distribution(distribution[0]).tolist()
            distribution_bins = distribution[1][:-1].tolist()
            distribution_bins[0] = distribution_bins[0] - 0.001 * (distribution_bins[1] - distribution_bins[0])

        attribute_info = {'datatype': datatype,
                          'is_categorical': is_categorical_attr,
                          'min': float(column_dropna.min()),
                          'max': float(column_dropna.max()),
                          'distribution_bins': distribution_bins,
                          'distribution_probabilities': distribution_probabilities,
                          'missing_rate': column_values.isnull().sum() / column_values.index.size}

        if datatype == 'integer':
            attribute_info['min'] = int(column_dropna.min())
            attribute_info['max'] = int(column_dropna.max())

        return attribute_info

    def infer_domain_of_string_attribute(self, attribute):
        datatype = self.attribute_to_datatype[attribute]
        column_values = self.input_dataset[attribute]
        column_dropna = column_values.dropna()
        column_value_lengths = column_dropna.astype(str).map(len)

        is_categorical_attribute = self.is_categorical(attribute)
        if is_categorical_attribute:
            distribution = column_dropna.value_counts()
            distribution.sort_index(inplace=True)
            distribution_probabilities = utils.normalize_given_distribution(distribution).tolist()
            distribution_bins = np.array(distribution.index).tolist()
        else:
            distribution = np.histogram(column_value_lengths, bins=self.histogram_size)
            distribution_probabilities = utils.normalize_given_distribution(distribution[0]).tolist()
            distribution_bins = distribution[1][:-1].tolist()
            distribution_bins[0] = distribution_bins[0] - 0.001 * (distribution_bins[1] - distribution_bins[0])

        attribute_info = {'datatype': datatype,
                          'is_categorical': is_categorical_attribute,
                          'min_length': int(column_value_lengths.min()),
                          'max_length': int(column_value_lengths.max()),
                          'distribution_bins': distribution_bins,
                          'distribution_probabilities': distribution_probabilities,
                          'missing_rate': column_values.isnull().sum() / column_values.index.size}

        return attribute_info

    def infer_domains(self):
        """Infer the attribute domains.
        
        The domain of an attribute includes
            (1) is_categorical or not 
            (2) datatype 
            (3) [min, max] 
            (4) 1-D distribution
            (5) missing rate

        Parameters
        ----------
            attribute : str
                Attribute name
        """
        self.dataset_description['attribute_description'] = {}
        for attribute in self.input_dataset:
            datatype = self.attribute_to_datatype[attribute]
            if datatype in self.numerical_datatypes:
                attribute_info = self.infer_domain_of_numeric_attribute(attribute)
            else:
                attribute_info = self.infer_domain_of_string_attribute(attribute)
            self.dataset_description['attribute_description'][attribute] = attribute_info

    def inject_laplace_noise_into_distribution_per_attribute(self, epsilon=0.1):
        for attr in self.dataset_description['attribute_description']:
            distribution = self.dataset_description['attribute_description'][attr]['distribution_probabilities']
            noisy_scale = 1 / (epsilon * self.input_dataset.shape[0])
            laplace_noises = np.random.laplace(0, scale=noisy_scale, size=len(distribution))
            noisy_distribution = np.asarray(distribution) + laplace_noises
            noisy_distribution = utils.normalize_given_distribution(noisy_distribution).tolist()
            self.dataset_description['attribute_description'][attr]['distribution_probabilities'] = noisy_distribution

    def encode_dataset_into_interval_indices(self):
        """Before constructing Bayesian network, encode input dataset by binning indices."""
        encoded_dataset = self.input_dataset.copy()
        for attribute in self.input_dataset:
            attribute_info = self.dataset_description['attribute_description'][attribute]

            datatype = attribute_info['datatype']
            is_categorical = attribute_info['is_categorical']
            bins = attribute_info['distribution_bins']

            if datatype == 'string' and not is_categorical:
                # non-categorical string attributes are ignored in BN construction.
                encoded_dataset.drop(attribute, axis=1, inplace=True)
                self.ignored_attributes_by_BN.append(attribute)
                continue
            elif datatype == 'datetime':
                encoded_dataset[attribute] = encoded_dataset[attribute].map(lambda x: parse(x).timestamp())

            if is_categorical:
                encoded_dataset[attribute] = encoded_dataset[~encoded_dataset[attribute].isnull()][attribute].map(
                    lambda x: bins.index(x))
            else:
                # the intervals are half-open, i.e., [1, 2)
                encoded_dataset[attribute] = encoded_dataset[~encoded_dataset[attribute].isnull()][attribute].map(
                    lambda x: bins.index([i for i in bins if i <= x][-1]))

            # missing values are replaced with len(bins).
            encoded_dataset[attribute].fillna(value=len(bins), inplace=True)

        self.dataset_description['meta']['ignored_attributes_by_BN'] = self.ignored_attributes_by_BN
        return encoded_dataset

    def save_dataset_description_to_file(self, file_name):
        with open(file_name, 'w') as outfile:
            json.dump(self.dataset_description, outfile, indent=4)

    def display_dataset_description(self):
        print(json.dumps(self.dataset_description, indent=4))


if __name__ == '__main__':
    # AdultIncome - reduced
    input_dataset_file = '../data/adult_reduced.csv'
    dataset_description_file = '../out/AdultIncome/description_test.txt'
    synthetic_dataset_file = '../out/AdultIncome/output_test.csv'

    df = pd.read_csv(input_dataset_file)
    print(df['age'].min())
