
import os
from os import path
from urllib.parse import urlparse

import pytz
from datetime import datetime
from uuid import uuid4

import pandas as pd
import numpy as np

from parlamentikon.Helpers import *
from parlamentikon.utility import *
from parlamentikon.setup_logger import log


class SnemovnaMeta(MyDataFrame):
    def __init__(self, cols=[], defaults={}, dtypes={}, index_name='name'):
        # Create an empty dataframe with defined columns
        columns = set(cols + [index_name] + list(defaults.keys()) + list(dtypes.keys()))
        super().__init__([], columns=columns)

        # Register custom variables that should not mix with the dataframe columns
        self._metadata = ['_cols', '_defaults', '_dtypes', '_index_name']
        self._cols, self._defaults, self._dtypes = cols, defaults, dtypes
        self._index_name = index_name

        # Set index
        self.set_index(index_name, inplace=True)

    def nastav_hodnotu(self, name, val):
        unregistered_keys = set(val.keys()) - set(self.columns)
        if len(unregistered_keys) > 0:
            raise ValueError(f"Found unregistered keys: {unregistered_keys}. Cannot set metadata!")
        missing_keys = self._defaults.keys() - val.keys()
        for k in missing_keys:
            val[k] = self._defaults[k]

        for k, i in val.items():
            self.at[name, k] = i


class SnemovnaDataFrame(MyDataFrame):
    """Základní třída, která zajišťuje sdílené proměnné a metody pro dětské třídy.

    Attributes
    ----------
    df : pandas DataFrame
        základní tabulka dané třídy
    paths : dict
        cesty k souborům načtených tabulek
    tbl : dict
        načtené tabulky
    meta : třída Meta
        metadata všech dostupných sloupců (napříč načtenými tabulkami)
    volební období : Int64
        volební období sněmovny
    snemovna : Int64
        objekt obsahujici data aktualni snemovny, defaultně None, hodnota se nastaví až v dětské třídě Orgány
    tzn : pytz formát
          časová zóna
    data_dir : string
        adresář, do kterého se ukládají data
    url : string
        url, na které jsou pro danou třídu zazipované tabulky
    zip_path
        lokální cesta k zazipovaným tabulkám
    file_name
        jméno zip souboru (basename)

    Methods
    -------
    drop_by_inconsistency (df, suffix, threshold, t1_name=None, t2_name=None, t1_on=None, t2_on=None, inplace=False)
        Prozkoumá tabulku a oveří konzistenci dat po mergování
    nastav_meta()
        Nastaví meta informace k sloupcům dle aktuálního stavu tabuky df
    rozsir_meta(header, tabulka=None, vlastni=None)
        Rozšíří meta informace k sloupcům dle hlavičky konkrétní tabulky
    """
    def __init__(self, volebni_obdobi=None, data_dir='./data', *args, **kwargs):
        log.debug("--> SnemovnaDataFrame")
        log.debug(f"Base kwargs: {kwargs}")
        super().__init__(*args, **kwargs)
        self._metadata = [
            "meta", 'tbl', 'parameters', 'paths',
            "volební období", "snemovna", "tzn"
        ]

        self.meta = SnemovnaMeta(
            index_name='sloupec',
            dtypes=dict(popis='string', tabulka='string', vlastni='bool', aktivni='bool'),
            defaults=dict(popis=None, tabulka=None, vlastni=None, aktivni=None),
        )
        self.tbl = {}
        self.paths = {}
        self.volebni_obdobi = volebni_obdobi
        self.snemovna = None
        self.tzn = pytz.timezone('Europe/Prague')

        self.parameters = {}
        self.parameters['data_dir'] = data_dir

        log.debug("<-- SnemovnaDataFrame")

    def pripoj_data(self, obj, jmeno=''):
        for key in obj.paths:
            self.paths[key] = obj.paths[key]
        for key in obj.tbl:
            self.tbl[key] = obj.tbl[key]
        for key in obj.meta:
            row = obj.meta.data.loc[key].to_dict()
            if row['tabulka'] == 'df':
                row['tabulka'] = jmeno + '_df'
            self.meta[key] = row
        return obj

    def popis(self):
        popis_tabulku(self, self.meta, schovej=['aktivni', 'sloupec'])

    def popis_sloupec(self, sloupec):
        popis_sloupec(self, sloupec)

    def drop_by_inconsistency (self, df, suffix, threshold, t1_name=None, t2_name=None, t1_on=None, t2_on=None, inplace=False, silent=False):
        inconsistency = {}
        abundance = []

        for col in df.columns[df.columns.str.endswith(suffix)]:
            short_col = col[:len(col)-len(suffix)]

            # Note: np.nan != np.nan by default
            difference = df[(df[short_col] != df[col]) & ~(df[short_col].isna() & df[col].isna())]
            if len(difference) > 0:
              inconsistency[short_col] = float(len(difference))/len(df)
              on = f", left_on={t1_on} right_on={t2_on}" if ((t1_on != None) and (t2_on != None)) else ''
              if not silent:
                  log.warning(f"While merging '{t1_name}' with '{t2_name}'{on}: Columns '{short_col}' and '{col}' differ in {len (difference)} values from {len(df)}. Inconsistency ratio: {inconsistency[short_col]:.4f}. Example of inconsistency: '{difference.iloc[0][short_col]}' (i.e. {short_col}@{difference.index[0]}) != '{difference.iloc[0][col]}' (i.e. {col}@{difference.index[0]})")
            else:
              abundance.append(short_col)

        to_drop = [col for (col, i) in inconsistency.items() if i >= threshold]
        if len(to_drop) > 0:
            if not silent:
                log.warning(f"While merging '{t1_name}' with '{t2_name}': Dropping {to_drop} because of big inconsistency.")

        to_skip = [col + suffix for col in set(inconsistency.keys()).union(abundance)]
        if len(to_skip) > 0:
            if not silent:
                log.warning(f"While merging '{t1_name}' with '{t2_name}': Dropping {to_skip} because of abundance.")

        if inplace == True:
            df.drop(columns=set(to_drop).union(to_skip), inplace=True)
            ret = df
        else:
            ret = df.drop(columns=set(to_drop).union(to_skip))

        return ret

    def nastav_dataframe(self, frame, odstran=[], vyber=[]):
        ordered_cols = list(vyber) + list(frame.columns)
        ordered_cols = [x for x in ordered_cols if x in frame.columns]
        ordered_cols =  list(dict.fromkeys(ordered_cols))

        # recreate the frame with ordered and selected columns
        self.drop(index=self.index, columns=self.columns, inplace=True)
        for col in ordered_cols:
            if col not in odstran:
                self[col] = frame[col].astype(frame[col].dtype)

        self.nastav_meta(odstran=odstran, vyber=vyber)

    def nastav_meta(self, odstran=[], vyber=[]):
        m = self.meta.copy()
        for key in m.index:
            if key in odstran:
                m.loc[key, 'aktivni'] = False
            elif key not in self.columns:
                m.loc[key, 'aktivni'] = False
            else:
                m.loc[key, 'aktivni'] = True

        for key in self.columns:
            if key not in m.index:
                log.warning(f"Pro sloupec '{key}' nebyla nalezena metadata!")

        ordered_idx = list(vyber) + list(m.index)
        ordered_idx = [x for x in ordered_idx if x in m.index]
        ordered_idx =  list(dict.fromkeys(ordered_idx))
        m = m.reindex(index=ordered_idx)

        self.meta.drop(index=self.meta.index, columns=self.meta.columns, inplace=True)
        for col in m.columns:
            self.meta[col] = m[col]

    def rozsir_meta(self, header, tabulka=None, vlastni=None):
        for key, i in header.items():
            val_dict = dict(popis=i.popis, tabulka=tabulka, vlastni=vlastni)
            self.meta.nastav_hodnotu(key, val_dict)

class SnemovnaZipDataMixin(object):
    def stahni_zip_data(self, nazev):
        url_prefix = "https://www.psp.cz/eknih/cdrom/opendata/"
        url = url_prefix + nazev + '.zip'
        data_dir = self.parameters['data_dir']

        a = urlparse(url)
        filename = os.path.basename(a.path)
        zip_path = f"{data_dir}/{filename}"
        log.debug(f"SnemovnaZipDataMixin: Nastavuji cestu k zip souboru na: {zip_path}")

        # smaz starý zip soubor, pokud existuje
        if os.path.isfile(zip_path):
            os.remove(zip_path)

        download_and_unzip(url, zip_path, data_dir)



