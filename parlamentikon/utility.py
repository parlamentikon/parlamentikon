
import requests
from pathlib import Path
from os import listdir #, path # TODO: asi stačí buď jen Path, nebo path
import zipfile

import pandas as pd
#from IPython.display import display
#import numpy as np

import plotly.graph_objects as go

from parlamentikon.Helpers import *
from parlamentikon.setup_logger import log


#######################################################################
# Stahování dat

def download_and_unzip(url, zip_file_name, data_dir):
    log.info(f"Stahuji '{url}'.")
    log.debug(f"Vytvářím adresář: '{data_dir}'")
    Path(data_dir).mkdir(parents=True, exist_ok=True)

    log.debug(f"Stahuji data z: '{url}'")
    r = requests.get(url)
    with open(zip_file_name, 'wb') as f:
        f.write(r.content)
    log.debug(f"Status: {r.status_code}, headers: {r.headers['content-type']}, encoding: {r.encoding}")

    log.debug(f"Rozbaluji data do: '{data_dir}'")
    with zipfile.ZipFile(zip_file_name, 'r') as zip_ref:
        zip_ref.extractall(data_dir)


#######################################################################
# Popis dat v pandas tabulkách

def popis_tabulku(frame, meta=None, schovej=[]):
    """
    Popiš vlastnosti tabulky
    """
    df = frame.select_dtypes(exclude=['object'])

    print(f"Počet řádků v tabulce: {df.index.size}")
    print()

    neanalyzovane = list(set(frame.columns) - set(df.columns))
    if len(neanalyzovane) > 0:
        print(f"Nenalyzované sloupce: {neanalyzovane}")
        print()

    uniq = df.nunique()
    is_null = df.isnull().sum()
    not_null = len(df) - is_null
    out = pd.DataFrame({
        "sloupec": uniq.index,
        "počet unikátních hodnot": uniq.values,
        "počet nenulových hodnot": not_null.values,
        "typ": df.dtypes.astype(str)
    })#.set_index('sloupec')#sort_values(by="počet unikátních hodnot", ascending=False)

    if isinstance(meta, pd.DataFrame):
        for column in meta:
            out[column] = meta[column]

    sloupce_s_jedinou_hodnotou = out[out["počet unikátních hodnot"] == 1]
    if len(sloupce_s_jedinou_hodnotou) == 0:
        print("Každý sloupec obsahuje alespoň dvě různé hodnoty.")
    else:
        print("Sloupce s jedinou hodnotou:")
        ret = "\n".join([f"  '{column}' má všude hodnotu '{df[column].iloc[0]}'" for column in sloupce_s_jedinou_hodnotou.index])
        print(ret)

    print()
    print('Nulové hodnoty: ')
    popis_nulove_hodnoty(df)

    if len(schovej) > 0:
        out.drop(columns=schovej, inplace=True)

    print()
    return out

def popis_nulove_hodnoty(df):
    """
    Vypiš jména sloupců s nulovými hodnotami a odpovídající četnosti
    """
    nans_df = df[df.columns[df.isna().any()]]
    col_with_nans = nans_df.columns

    if len(col_with_nans) == 0:
        print("Tabulka neobsahuje žádné nulové hodnoty [NaNy atp.]")
        return

    for col in col_with_nans:
      cnt = len(df[df[col].isna() == True])
      print(f"Sloupec '{col}' obsahuje {100*cnt/len(df):.2f}% ({cnt} z {len(df)}) nulových hodnot (např. NaNů).")

def popis_sloupec(df, column):
    print(f"Typ: {df[column].dtype}")
    print(f"Počet hodnot: {df[column].count()}")
    print(f"Počet unikátních hodnot: {df[column].nunique()}")

    print()
    print("Seznam hodnot")
    print("--------------")
    for hodnota, pocet in df[column].value_counts().to_dict().items():
        print(f"{hodnota}: {pocet}")

def cetnost_opakovani_dle_sloupce(df, column, printout=False):
    """
    Cetnost radku dle sloupce
    """
    tmp_column = f"{column}_cnt"
    ret = df.groupby(column).agg('size').reset_index(name=tmp_column).groupby(tmp_column).size()

    if printout:
        freq_str = "\n".join([f"{cnt} hodnot se opakuje {freq} krát" for (freq, cnt) in ret.iteritems()])
        print(f"Četnost opakování '{column}' vzestupně:\n{freq_str}")
    return ret


#######################################################################
# Čištění  a úprava dat v pandas tabulkách

def pretypuj(df, header, name=None, inplace=False):
    if inplace:
        new_df = df
    else:
        new_df = df.copy()

    if name is not None:
        log.debug(f"Přetypování v tabulce '{name}'.")
    for col in df.columns:
        if col in header:
            #log.debug(f"Přetypovávám sloupec: '{col}'.")
            if isinstance(header[col], str):
                new_df[col] = df[col].astype(header[col])
            elif isinstance(header[col], MItem):
                new_df[col] = df[col].astype(header[col].typ)
            else:
                log.error(f"Chyba: Neznámý formát přetypování. Sloupec '{col}' nebylo možné přetypovat.")
    return new_df


def strip_all_string_columns(df):
    """
    Trims whitespace from ends of each value across all series in dataframe.
    """
    for col in df.columns:
        if str(df[col].dtype) == 'string':
            df[col] = df[col].str.strip()
    return df

def mask_by_values(series, mask):
    """
    Masks the values of a series according to adictionary
    """
    if True: #(series.dtype == pd.Int64Dtype()):
        series = series.astype(object)

    new_series = series.copy()

    for val_to_mask in series.unique():
        if val_to_mask in mask.keys(): # mask it
            new_series = new_series.mask(series == val_to_mask, mask[val_to_mask])

    return new_series

def format_to_datetime_and_report_skips(df, col, to_format):
    srs = df[col]
    new_srs = pd.to_datetime(srs[~srs.isna()], format=to_format, errors="coerce")
    skipped = srs[(~srs.isna() & new_srs.isna())| (new_srs.dt.strftime(to_format).ne(srs))]
    if len(skipped) > 0:
        log.warning(f"Skipped {len(skipped)} values while formatting '{col}' to datetime. Using format '{to_format}'. Example of skipped rows: {skipped.to_list()[:5]}.")

    return new_srs

def sort_column_by_predefined_order(column, ordered_list, how='head'):
    """Sort function"""
    if how == 'head':
        ordered_options = ordered_list + list(set(column.unique()) - set(ordered_list))
    elif how == 'tail':
        ordered_options = list(set(column.unique()) - set(ordered_list)) + ordered_list
    else:
        raise(ValueError(f"Špatný parametr: {how}"))

    correspondence = {t: o for o, t in enumerate(ordered_options)}
    return column.map(correspondence)


#######################################################################
# Zobrazování dat v pandas tabulkách

def groupby_bar(df, by, xlabel=None, ylabel=None, title=''):
    xlabel = by if xlabel == None else xlabel
    ylabel = '' if ylabel == None else ylabel

    groups = df.groupby(by).size()
    fig = go.Figure(go.Bar(
        x=groups.index,
        y=groups.values,
        hovertemplate=
            xlabel + ": %{x}<br>" +
            ylabel + ": %{y:.0}<br>" +
            "<extra></extra>"
    ))

    fig.update_xaxes(title_text=xlabel, type="category")
    fig.update_yaxes(title_text=ylabel)
    fig.update_layout(title=title, width=600, height=400)
    return fig


#######################################################################
# Struktury uložené v pandas tabulkách

#def find_children_ids(ids, id_field, df, parent_field, parent_ids, level=0):
#    children = df[df[parent_field].isin(parent_ids)]
#    if len(children) > 0:
#        for idx, child in children.iterrows():
#            #print(' '*level, ' ', child.nazev_organu_cz)
#            ids.append(child[id_field])
#            ids = find_children_ids(ids, id_field, df, parent_field, [child[id_field]], level+1)
#    return ids

def expand_hierarchy(df, id_field, parent_field, to_expand):
    children = df[df[parent_field].isin(to_expand)]
    if len(children) > 0:
        new_to_expand = [child[id_field] for idx, child in children.iterrows()]
        return to_expand + expand_hierarchy(df, id_field, parent_field, new_to_expand)
    else:
        return to_expand


#######################################################################
# Obecné utility

def flatten(ary):
    return [x for l in ary for x in l]
