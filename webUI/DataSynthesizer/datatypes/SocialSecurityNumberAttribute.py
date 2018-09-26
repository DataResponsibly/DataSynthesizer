import numpy as np

from DataSynthesizer.datatypes.AbstractAttribute import AbstractAttribute
from DataSynthesizer.datatypes.utils.DataType import DataType


def preprocess(column):
    if type(column.iloc[0]) is int:
        return column
    elif type(column.iloc[0]) is str:
        return column.map(lambda x: int(x.replace('-', '')))
    else:
        raise Exception('Invalid SocialSecurityNumber.')


# TODO Some special numbers are never allocated. https://en.wikipedia.org/wiki/Social_Security_number
def is_ssn(value):
    if type(value) is int:
        return 0 < value < 1e9
    elif type(value) is str:
        value = value.replace('-', '')
        if value.isdigit():
            return 0 < int(value) < 1e9
    return False


class SocialSecurityNumberAttribute(AbstractAttribute):
    """ SocialSecurityNumber format AAA-GG-SSSS """

    def __init__(self, name, is_candidate_key=False, is_categorical=False, histogram_size=20):
        super().__init__(name, is_candidate_key, is_categorical, histogram_size)
        self.is_numerical = True
        self.data_type = DataType.SOCIAL_SECURITY_NUMBER

    def infer_domain(self, column):
        super().infer_domain(preprocess(column))
        self.min = int(self.min)
        self.max = int(self.max)

    def generate_values_as_candidate_key(self, n):
        if n < 1e9:
            values = np.linspace(0, 1e9 - 1, num=n, dtype=int)
            values = np.random.permutation(values)
            values = [str(i).zfill(9) for i in values]
            return ['{}-{}-{}'.format(i[:3], i[3:5], i[5:]) for i in values]
        else:
            raise Exception('The candidate key "{}" cannot generate more than 1e9 distinct values.', self.name)

    def sample_values_from_binning_indices(self, binning_indices):
        return super().sample_binning_indices_in_independent_attribute_mode(binning_indices)
