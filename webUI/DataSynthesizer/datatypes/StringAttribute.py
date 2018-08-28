import numpy as np
from pandas import Series

from DataSynthesizer.datatypes.AbstractAttribute import AbstractAttribute
from DataSynthesizer.datatypes.utils.DataType import DataType
from DataSynthesizer.lib import utils


class StringAttribute(AbstractAttribute):
    """Variable min and max are the lengths of the shortest and longest strings."""

    def __init__(self, name, is_candidate_key=False, is_categorical=False, histogram_size=20):
        super().__init__(name, is_candidate_key, is_categorical, histogram_size)
        self.is_numerical = False
        self.data_type = DataType.STRING

    def infer_domain(self, column):
        assert isinstance(column, Series)
        self.data = column
        self.data_dropna = self.data.dropna()
        data_dropna_len = self.data_dropna.map(len)
        self.missing_rate = (self.data.size - self.data_dropna.size) / self.data.size
        self.min = float(data_dropna_len.min())
        self.max = float(data_dropna_len.max())

        if self.is_categorical:
            distribution = self.data_dropna.value_counts()
            distribution.sort_index(inplace=True)
            self.distribution_probabilities = utils.normalize_given_distribution(distribution).tolist()
            self.distribution_bins = np.array(distribution.index).tolist()
        else:
            distribution = np.histogram(data_dropna_len, bins=self.histogram_size)
            self.distribution_probabilities = utils.normalize_given_distribution(distribution[0]).tolist()
            bins = distribution[1][:-1].tolist()
            bins[0] = bins[0] - 0.001 * (bins[1] - bins[0])
            self.distribution_bins = bins

    def generate_values_as_candidate_key(self, n):
        length = np.random.randint(self.min, self.max)
        vectorized = np.vectorize(lambda x: '{}{}'.format(utils.generate_random_string(length), x))
        return vectorized(np.arange(n))

    def sample_values_from_binning_indices(self, binning_indices):
        column = super().sample_values_from_binning_indices(binning_indices)
        if not self.is_categorical:
            column[~column.isnull()] = column[~column.isnull()].apply(lambda x: utils.generate_random_string(int(x)))

        return column
