import json

import numpy as np
import pandas as pd

from datatypes.AbstractAttribute import AbstractAttribute
from datatypes.DateTimeAttribute import is_datetime, DateTimeAttribute
from datatypes.FloatAttribute import FloatAttribute
from datatypes.IntegerAttribute import IntegerAttribute
from datatypes.SocialSecurityNumberAttribute import is_ssn, SocialSecurityNumberAttribute
from datatypes.StringAttribute import StringAttribute
from datatypes.utils.DataType import DataType
from lib import utils
from lib.PrivBayes import greedy_bayes, construct_noisy_conditional_distributions


# TODO detect datetime formats.
class DataDescriber(object):
    """Analyze input dataset, then save the dataset description in a JSON file.

    Attributes
    ----------
        histogram_size : int
            Number of bins in histograms.
        threshold_of_categorical_variable : int
            Categorical variables have no more than "this number" of distinct values.
        null_values: scalar, str, list-like, or dict
            Additional strings to recognize as NULL. If dict passed, specific per-column NA values.
            By default the following values are interpreted as NULL: ‘’, ‘NULL’, ‘N/A’, ‘NA’, ‘NaN’, ‘nan’, etc.
        attribute_to_datatype : dict
            Mappings of {attribute: datatype}, e.g., {"age": "Integer", "gender": "String"}.
        attribute_to_is_categorical : dict
            Mappings of {attribute: boolean}, e.g., {"gender":True, "age":False}.
        attribute_to_is_candidate_key: dict
            Mappings of {attribute: boolean}, e.g., {"id":True, "name":False}.
        dataset_description: dict
            Nested dictionary (equivalent to JSON) recording the mined dataset information.
        input_dataset : DataFrame
            The dataset to be analyzed.
        input_dataset_as_list : List
            List of Attributes, essentially the same as input_dataset.
        bayesian_network : list
            List of [child, [parent,]] to represent constructed BN.
        encoded_dataset : DataFrame
            A discrete dataset taken as input by PrivBayes in correlated attribute mode.
    """

    def __init__(self, histogram_size=20, threshold_of_categorical_variable=10, null_values=None):
        self.histogram_size = histogram_size
        self.threshold_of_categorical_variable = threshold_of_categorical_variable
        self.null_values = null_values
        self.attribute_to_datatype = {}
        self.attribute_to_is_categorical = {}
        self.attribute_to_is_candidate_key = {}
        self.dataset_description = {}
        self.input_dataset = None
        self.input_dataset_as_column_dict = {}
        self.bayesian_network = []
        self.encoded_dataset = None

    # TODO remove superfluous information in random mode.
    def describe_dataset_in_random_mode(self, dataset_file, attribute_to_datatype={}, attribute_to_is_categorical={},
                                        attribute_to_is_candidate_key={}, seed=0):
        self.describe_dataset_in_independent_attribute_mode(dataset_file, attribute_to_datatype=attribute_to_datatype,
                                                            attribute_to_is_categorical=attribute_to_is_categorical,
                                                            attribute_to_is_candidate_key=attribute_to_is_candidate_key,
                                                            seed=seed)
        # After running independent attribute mode, 1) make all distributions uniform; 2) set missing rate to zero.
        for attr in self.dataset_description['attribute_description']:
            distribution = self.dataset_description['attribute_description'][attr]['distribution_probabilities']
            uniform_distribution = np.ones_like(distribution)
            uniform_distribution = utils.normalize_given_distribution(uniform_distribution).tolist()
            self.dataset_description['attribute_description'][attr]['distribution_probabilities'] = uniform_distribution
            self.dataset_description['attribute_description'][attr]['missing_rate'] = 0

    def describe_dataset_in_independent_attribute_mode(self, dataset_file, epsilon=0.1, attribute_to_datatype={},
                                                       attribute_to_is_categorical={}, attribute_to_is_candidate_key={},
                                                       seed=0):

        utils.set_random_seed(seed)
        self.attribute_to_datatype = {attr: DataType(data_type) for attr, data_type in attribute_to_datatype.items()}
        self.attribute_to_is_categorical = dict(attribute_to_is_categorical)
        self.attribute_to_is_candidate_key = dict(attribute_to_is_candidate_key)
        self.read_dataset_from_csv(dataset_file)
        self.infer_attribute_data_types()
        self.get_dataset_meta_info()
        self.convert_input_dataset_into_a_dict_of_columns()
        self.infer_domains()
        self.inject_laplace_noise_into_distribution_per_attribute(epsilon)
        # record attribute information in json format
        self.dataset_description['attribute_description'] = {}
        for attr, column in self.input_dataset_as_column_dict.items():
            assert isinstance(column, AbstractAttribute)
            self.dataset_description['attribute_description'][attr] = column.to_json()

    def describe_dataset_in_correlated_attribute_mode(self, dataset_file, k=0, epsilon=0.1, attribute_to_datatype={},
                                                      attribute_to_is_categorical={}, attribute_to_is_candidate_key={},
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
                Mappings of {attribute: datatype}, e.g., {"age": "Integer", "gender": "String"}.
            attribute_to_is_categorical : dict
                Mappings of {attribute: boolean}, e.g., {"gender":True, "age":False}.
            attribute_to_is_candidate_key: dict
                Mappings of {attribute: boolean}, e.g., {"id":True, "name":False}.
            seed : int or float
                Seed the random number generator.
        """

        self.describe_dataset_in_independent_attribute_mode(dataset_file, epsilon, attribute_to_datatype,
                                                            attribute_to_is_categorical, attribute_to_is_candidate_key,
                                                            seed)
        self.encoded_dataset = self.encode_dataset_into_binning_indices()
        if self.encoded_dataset.shape[1] < 2:
            raise Exception("Constructing Bayesian Network needs more attributes.")

        self.bayesian_network = greedy_bayes(self.encoded_dataset, k, epsilon)
        self.dataset_description['bayesian_network'] = self.bayesian_network
        self.dataset_description['conditional_probabilities'] = construct_noisy_conditional_distributions(
            self.bayesian_network, self.encoded_dataset, epsilon)

    def read_dataset_from_csv(self, file_name=None):
        try:
            self.input_dataset = pd.read_csv(file_name, skipinitialspace=True, na_values=self.null_values)
        except (UnicodeDecodeError, NameError):
            self.input_dataset = pd.read_csv(file_name, skipinitialspace=True, na_values=self.null_values,
                                             encoding='latin1')

        # drop columns with empty active domain, i.e., all values are missing.
        attributes_before = set(self.input_dataset.columns)
        self.input_dataset.dropna(axis=1, how='all')
        attributes_after = set(self.input_dataset.columns)
        if len(attributes_before) != len(attributes_after):
            print("Empty columns are removed, including {}.".format(attributes_before - attributes_after))

    def infer_attribute_data_types(self):
        attributes_with_unknown_datatype = set(self.input_dataset.columns) - set(self.attribute_to_datatype)
        inferred_numerical_attributes = set(utils.infer_numerical_attributes_in_dataframe(self.input_dataset))
        for attr in attributes_with_unknown_datatype:
            column_dropna = self.input_dataset[attr].dropna()

            # current attribute is either Integer or Float.
            if attr in inferred_numerical_attributes:
                # TODO Testing all values may become very slow for large datasets.
                if (column_dropna == column_dropna.astype(int)).all():
                    self.attribute_to_datatype[attr] = DataType.INTEGER
                else:
                    self.attribute_to_datatype[attr] = DataType.FLOAT

            # current attribute is either String, DateTime, or SocialSecurityNumber.
            else:
                # Sample 20 values to test its data_type.
                datetime_tests = column_dropna.sample(20, replace=True).map(is_datetime)
                if all(datetime_tests):
                    self.attribute_to_datatype[attr] = DataType.DATETIME
                else:
                    ssn_tests = column_dropna.sample(20, replace=True).map(is_ssn)
                    if all(ssn_tests):
                        self.attribute_to_datatype[attr] = DataType.SOCIAL_SECURITY_NUMBER
                    else:
                        self.attribute_to_datatype[attr] = DataType.STRING

    def get_dataset_meta_info(self):
        all_attributes = self.input_dataset.columns.tolist()

        # find all candidate keys.
        for attr in set.difference(set(all_attributes), set(self.attribute_to_is_candidate_key)):
            self.attribute_to_is_candidate_key[attr] = self.input_dataset[attr].is_unique

        candidate_keys = [attr for attr, is_key in self.attribute_to_is_candidate_key.items() if is_key]

        # find all categorical attributes.
        for attr in set.difference(set(all_attributes), set(self.attribute_to_is_categorical)):
            self.attribute_to_is_categorical[attr] = self.is_categorical(attr)

        non_categorical_string_attributes = []
        for attr in all_attributes:
            if (not self.attribute_to_is_categorical[attr]) and self.attribute_to_datatype[attr] is DataType.STRING:
                non_categorical_string_attributes.append(attr)

        attributes_in_BN = list(set(all_attributes) - set(candidate_keys) - set(non_categorical_string_attributes))
        num_attributes_in_BN = len(attributes_in_BN)
        self.dataset_description['meta'] = {"num_tuples": self.input_dataset.shape[0],
                                            "num_attributes": self.input_dataset.shape[1],
                                            "num_attributes_in_BN": num_attributes_in_BN,
                                            "all_attributes": all_attributes,
                                            "candidate_keys": candidate_keys,
                                            "non_categorical_string_attributes": non_categorical_string_attributes,
                                            "attributes_in_BN": attributes_in_BN}

    def is_categorical(self, attr):
        """ Detect whether an attribute is categorical.

        Parameters
        ----------
            attr : str
                Attribute name.
        """
        if attr in self.attribute_to_is_categorical:
            return self.attribute_to_is_categorical[attr]
        else:
            if self.input_dataset[attr].dropna().unique().size <= self.threshold_of_categorical_variable:
                return True
            else:
                return False

    def convert_input_dataset_into_a_dict_of_columns(self):
        self.input_dataset_as_column_dict = {}
        for attr in self.input_dataset:
            data_type = self.attribute_to_datatype[attr]
            is_candidate_key = self.attribute_to_is_candidate_key[attr]
            is_categorical = self.attribute_to_is_categorical[attr]
            paras = (attr, is_candidate_key, is_categorical, self.histogram_size)
            if data_type is DataType.INTEGER:
                self.input_dataset_as_column_dict[attr] = IntegerAttribute(*paras)
            elif data_type is DataType.FLOAT:
                self.input_dataset_as_column_dict[attr] = FloatAttribute(*paras)
            elif data_type is DataType.DATETIME:
                self.input_dataset_as_column_dict[attr] = DateTimeAttribute(*paras)
            elif data_type is DataType.STRING:
                self.input_dataset_as_column_dict[attr] = StringAttribute(*paras)
            elif data_type is DataType.SOCIAL_SECURITY_NUMBER:
                self.input_dataset_as_column_dict[attr] = SocialSecurityNumberAttribute(*paras)
            else:
                raise Exception('The data type of attribute {} is unknown.'.format(attr))

    def infer_domains(self):
        for column in self.input_dataset_as_column_dict.values():
            assert isinstance(column, AbstractAttribute)
            column.infer_domain(self.input_dataset[column.name])

    def inject_laplace_noise_into_distribution_per_attribute(self, epsilon=0.1):
        num_attributes_in_BN = self.dataset_description['meta']['num_attributes_in_BN']
        for column in self.input_dataset_as_column_dict.values():
            assert isinstance(column, AbstractAttribute)
            column.inject_laplace_noise(epsilon, num_attributes_in_BN)

    def encode_dataset_into_binning_indices(self):
        """Before constructing Bayesian network, encode input dataset into binning indices."""
        encoded_dataset = pd.DataFrame()
        for attr in self.dataset_description['meta']['attributes_in_BN']:
            encoded_dataset[attr] = self.input_dataset_as_column_dict[attr].encode_values_into_binning_indices()
        return encoded_dataset

    def save_dataset_description_to_file(self, file_name):
        with open(file_name, 'w') as outfile:
            json.dump(self.dataset_description, outfile, indent=4)

    def display_dataset_description(self):
        print(json.dumps(self.dataset_description, indent=4))


if __name__ == '__main__':
    from DataGenerator import DataGenerator

    # input dataset
    input_data = './data/adult_ssn.csv'
    # location of two output files
    mode = 'correlated_attribute_mode'
    description_file = './out/{}/description.txt'.format(mode)
    synthetic_data = './out/{}/sythetic_data.csv'.format(mode)

    # An attribute is categorical if its domain size is less than this threshold.
    # Here modify the threshold to adapt to the domain size of "education" (which is 14 in input dataset).
    threshold_value = 20

    # Additional strings to recognize as NA/NaN.
    null_values = '<NULL>'

    # specify which attributes are candidate keys of input dataset.
    candidate_keys = {'age': False}

    # A parameter in differential privacy.
    # It roughtly means that removing one tuple will change the probability of any output by  at most exp(epsilon).
    # Set epsilon=0 to turn off differential privacy.
    epsilon = 0.1

    # The maximum number of parents in Bayesian network, i.e., the maximum number of incoming edges.
    degree_of_bayesian_network = 2

    # Number of tuples generated in synthetic dataset.
    num_tuples_to_generate = 32561  # Here 32561 is the same as input dataset, but it can be set to another number.

    describer = DataDescriber(threshold_of_categorical_variable=threshold_value, null_values=null_values)
    describer.describe_dataset_in_correlated_attribute_mode(input_data, epsilon=epsilon, k=degree_of_bayesian_network,
                                                            attribute_to_is_candidate_key=candidate_keys)
    describer.save_dataset_description_to_file(description_file)

    generator = DataGenerator()
    generator.generate_dataset_in_correlated_attribute_mode(num_tuples_to_generate, description_file)
    generator.save_synthetic_data(synthetic_data)
    print(generator.synthetic_dataset.head())
