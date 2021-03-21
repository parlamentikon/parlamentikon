
from collections import namedtuple
import pandas as pd

from parlamentikon.setup_logger import log


#######################################################################
# Pomocné struktury pro přetížení pd.DataFrame

class MySeries(pd.Series):
    @property
    def _constructor(self):
        return MySeries

    @property
    def _constructor_expanddim(self):
        return MyDataFrame


class MyDataFrame(pd.DataFrame):
    # temporary properties
    _internal_names = pd.DataFrame._internal_names
    _internal_names_set = set(_internal_names)

    # normal properties
    _metadata = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def _constructor(self):
        return MyDataFrame

    @property
    def _constructor_sliced(self):
        return MySeries


#######################################################################
# Pomocné struktury pro asociovaná metadata k sloupcům tabulek

MItem = namedtuple('MItem', ("typ", "popis"))


class Meta(object):
    def __init__(self, columns=[], defaults={}, dtypes={}, index_name='name'):
        self.defaults = defaults
        c = set([index_name]).union(columns).union(defaults.keys()).union(dtypes.keys())
        self.data = pd.DataFrame([], columns=c).set_index(index_name)

    def __init__(self, defaults={}, dtypes={}, index_name='name'):
        self.defaults = defaults
        columns = set([index_name]).union(defaults.keys()).union(dtypes.keys())
        self.data = pd.DataFrame([], columns=columns).set_index(index_name)

        for key, dtype in dtypes.items():
            self.data[key] = self.data[key].astype(dtype)

    def __getitem__(self, name):
        found = self.data[self.data.index.isin([name])]
        if len(found) > 0:
            return found.iloc[0]
        else:
            return None

    def __setitem__(self, name, val):
        found = self.data[self.data.index.isin([name])]
        if len(found) > 0:
            # insert
            for k, i in val.items():
                self.data.loc[self.data.index == name, k] = i
        else:
            # update
            missing_keys = self.defaults.keys() - val.keys()
            for k in missing_keys:
                val[k] = self.defaults[k]
            self.data = self.data.append(pd.Series(val.values(), index=val.keys(), name=name))
            #self.data = self.data.update(pd.Series(val.values(), index=val.keys(), name=name))

    def __contains__(self, name):
        found = self.data[self.data.index.isin([name])]
        if len(found) > 0:
            return True
        else:
            return False

    def __iter__(self):
        for c in self.data.index:
            yield c

    def __str__(self):
          return str(self.data)
