from pandas import Series

from datatypes.DateTimeAttribute import DateTimeAttribute
from datatypes.FloatAttribute import FloatAttribute
from datatypes.IntegerAttribute import IntegerAttribute
from datatypes.SocialSecurityNumberAttribute import SocialSecurityNumberAttribute
from datatypes.StringAttribute import StringAttribute
from datatypes.utils.DataType import DataType


def parse_json(attribute_in_json):
    name = attribute_in_json['name']
    data_type = DataType(attribute_in_json['data_type'])
    is_candidate_key = attribute_in_json['is_candidate_key']
    is_categorical = attribute_in_json['is_categorical']
    histogram_size = len(attribute_in_json['distribution_bins'])
    if data_type is DataType.INTEGER:
        attribute = IntegerAttribute(name, is_candidate_key, is_categorical, histogram_size, Series())
    elif data_type is DataType.FLOAT:
        attribute = FloatAttribute(name, is_candidate_key, is_categorical, histogram_size, Series())
    elif data_type is DataType.DATETIME:
        attribute = DateTimeAttribute(name, is_candidate_key, is_categorical, histogram_size, Series())
    elif data_type is DataType.STRING:
        attribute = StringAttribute(name, is_candidate_key, is_categorical, histogram_size, Series())
    elif data_type is data_type.SOCIAL_SECURITY_NUMBER:
        attribute = SocialSecurityNumberAttribute(name, is_candidate_key, is_categorical, histogram_size, Series())
    else:
        raise Exception('Data type {} is unknown.'.format(data_type.value))

    attribute.missing_rate = attribute_in_json['missing_rate']
    attribute.min = attribute_in_json['min']
    attribute.max = attribute_in_json['max']
    attribute.distribution_bins = attribute_in_json['distribution_bins']
    attribute.distribution_probabilities = attribute_in_json['distribution_probabilities']

    return attribute
