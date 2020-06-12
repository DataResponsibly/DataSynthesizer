from typing import Union

import numpy as np
from pandas import Series

from DataSynthesizer.datatypes.AbstractAttribute import AbstractAttribute
from DataSynthesizer.datatypes.utils.DataType import DataType
from DataSynthesizer.lib import utils


class StringAttribute(AbstractAttribute):
    """Variable min and max are the lengths of the shortest and longest strings.

    """

    def __init__(self, name: str, is_candidate_key, is_categorical, histogram_size: Union[int, str], data: Series):
        super().__init__(name, is_candidate_key, is_categorical, histogram_size, data)
        self.is_numerical = False
        self.data_type = DataType.STRING
        self.data_dropna_len = self.data_dropna.astype(str).map(len)

    def infer_domain(self, categorical_domain=None, numerical_range=None):
        if categorical_domain:
            lengths = [len(i) for i in categorical_domain]
            self.min = min(lengths)
            self.max = max(lengths)
            self.distribution_bins = np.array(categorical_domain)
        else:
            self.min = int(self.data_dropna_len.min())
            self.max = int(self.data_dropna_len.max())
            if self.is_categorical:
                self.distribution_bins = self.data_dropna.unique()
            else:
                self.distribution_bins = np.array([self.min, self.max])

        self.distribution_probabilities = np.full_like(self.distribution_bins, 1 / self.distribution_bins.size)

    def infer_distribution(self):
        if self.is_categorical:
            distribution = self.data_dropna.value_counts()
            for value in set(self.distribution_bins) - set(distribution.index):
                distribution[value] = 0
            distribution.sort_index(inplace=True)
            self.distribution_probabilities = utils.normalize_given_distribution(distribution)
            self.distribution_bins = np.array(distribution.index)
        else:
            distribution = np.histogram(self.data_dropna_len, bins=self.histogram_size)
            self.distribution_bins = distribution[1][:-1]
            self.distribution_probabilities = utils.normalize_given_distribution(distribution[0])

    def generate_values_as_candidate_key(self, n):
        length = np.random.randint(self.min, self.max)
        vectorized = np.vectorize(lambda x: '{}{}'.format(utils.generate_random_string(length), x))
        return vectorized(np.arange(n))

    def sample_values_from_binning_indices(self, binning_indices):
        column = super().sample_values_from_binning_indices(binning_indices)
        if not self.is_categorical:
            column[~column.isnull()] = column[~column.isnull()].apply(lambda x: utils.generate_random_string(int(x)))

        return column
