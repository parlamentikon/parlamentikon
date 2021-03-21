#import re
#from collections import namedtuple

from datetime import datetime

import numpy as np
import pandas as pd

#from html2text import html2text
#from bs4 import BeautifulSoup, NavigableString

#import os
#import requests
#from time import time
#from urllib.parse import urlparse
#from joblib import Parallel, delayed, cpu_count
#from multiprocessing.pool import ThreadPool

from parlamentikon.Snemovna import *
from parlamentikon.PoslanciOsoby import *
from parlamentikon.Stenozaznamy import *
from parlamentikon.TabulkyStenotexty import *

from parlamentikon.setup_logger import log

# Textová podoba stenozáznamů není součástí oficiálních tabulek PS, vytváříme je web scrapingem.
# Texty se stahují z internetových stránek PS, viz. např. https://www.psp.cz/eknih/2017ps/stenprot/001schuz/s001001.htm


class Stenotexty(TabulkaStenotextyMixin, StenoRecnici, Steno, ZarazeniOsoby, Organy, Osoby, SnemovnaDataFrame):

    def __init__(self, stahni=True, limit=-1, soubezne_stahovani_max=12, soubezne_zpracovani_max=-1, *args, **kwargs):
        log.debug('--> StenoTexty')

        super().__init__(stahni=stahni, *args, **kwargs)

        self.parameters['limit'] = limit
        self.parameters['soubezne_stahovani_max'] = soubezne_stahovani_max
        self.parameters['soubezne_zpracovani_max'] = soubezne_zpracovani_max

        if stahni == True:
            self.stahni_steno_texty()

        self.nacti_steno_texty()

        # Doplneni recnika, který mluvil na konci minulého stenozáznamu (přetahujícího řečníka).
        # Přetahující řečník nemá v aktuálním stenozáznamu identifikátor, ale zpravidla (v 99% případů) byl zmíněn v některém z minulých stenozáznamů (turns).
        # Tento stenozáznam je nutné vyhledat a uložit jeho číslo ('id_turn_surrogate') a číslo řečníka ('id_rec_surrogate').
        # V joinu se 'steno_rec' se pak použije 'id_rec_surrogate' místo 'id_rec' a 'id_turn_surrogate' místo 'id_turn' pro získání informací o osobě etc.
        # Pozor: naopak informace o času proslovu jsou navázány na 'turn'.
        self.tbl['steno_texty'].loc[self.tbl['steno_texty'].id_rec.isna(), 'turn_surrogate'] = np.nan
        self.tbl['steno_texty'].loc[~self.tbl['steno_texty'].id_rec.isna(), 'turn_surrogate'] = self.tbl['steno_texty'].turn
        self.tbl['steno_texty']['turn_surrogate'] = self.tbl['steno_texty'].groupby("schuze")['turn_surrogate'].ffill().astype('Int64')
        self.tbl['steno_texty']['id_rec_surrogate'] = self.tbl['steno_texty']['id_rec']
        self.meta.nastav_hodnotu('turn_surrogate', dict(popis='Číslo stenozáznamu (turn), ve kterém byla nalezena identifikace řečníka.', tabulka='df', vlastni=True))

        self.tbl['steno_texty']['id_rec_surrogate'] = self.tbl['steno_texty'].groupby("schuze")['id_rec_surrogate'].ffill().astype('Int64')
        self.meta.nastav_hodnotu('id_rec_surrogate', dict(popis='Identifikace řečníka na základě zpětmého hledání v stenozáznamech (turn).', tabulka='df', vlastni=True))

        # připoj osobu ze steno_rec ... we simply add id_osoba to places where it's missing
        m = pd.merge(left=self.tbl['steno_texty'], right=self.tbl['steno_recnici'][['schuze', "turn", "aname", 'id_osoba']], left_on=["schuze", "turn_surrogate", "id_rec_surrogate"], right_on=["schuze", "turn", "aname"], how="left")
        ids = m[m.id_osoba_x.eq(m.id_osoba_y)].index
        ne_ids = set(m.index)-set(ids)
        assert m[m.index.isin(ne_ids) & (~m.id_osoba_x.isna())].size / m[m.index.isin(ne_ids)].size < 0.1 # This is a consistency sanity check
        m['id_osoba'] = m['id_osoba_y']
        m['turn'] = m['turn_x']
        self.tbl['steno_texty'] = m.drop(labels=['id_osoba_x', 'id_osoba_y', 'turn_y', 'turn_x', 'aname'], axis=1)

        # Merge steno_recnici
        suffix = "__steno_recnici"
        self.tbl['steno_texty'] = pd.merge(left=self.tbl['steno_texty'], right=self.tbl['steno_recnici'], left_on=["schuze", "turn_surrogate", "id_rec_surrogate"], right_on=['schuze', 'turn', 'aname'], suffixes = ("", suffix), how='left')
        self.tbl['steno_texty'] = self.tbl['steno_texty'].drop(labels=['turn__steno_recnici'], axis=1) # this inconsistency comes from the 'turn-fix'
        self.drop_by_inconsistency(self.tbl['steno_texty'], suffix, 0.1, 'steno_texty', 'steno_recnici', inplace=True)

        # Merge osoby
        suffix = "__osoby"
        self.tbl['steno_texty'] = pd.merge(left=self.tbl['steno_texty'], right=self.tbl['osoby'], on='id_osoba', suffixes = ("", suffix), how='left')
        self.drop_by_inconsistency(self.tbl['steno_texty'], suffix, 0.1, 'steno_texty', 'osoby', inplace=True)

        ## Merge zarazeni_osoby
        zarazeni_osoby = self.tbl['zarazeni_osoby']
        poslanci = zarazeni_osoby[(zarazeni_osoby.do_o.isna()) & (zarazeni_osoby.id_organ==self.snemovna.id_organ) & (zarazeni_osoby.cl_funkce=='členství')] # všichni poslanci
        strany = zarazeni_osoby[(zarazeni_osoby.id_osoba.isin(poslanci.id_osoba)) & (zarazeni_osoby.nazev_typ_organ_cz == "Klub") & (zarazeni_osoby.do_o.isna()) & (zarazeni_osoby.cl_funkce=='členství')]
        self.tbl['steno_texty'] = pd.merge(self.tbl['steno_texty'], strany[['id_osoba', 'zkratka']], on='id_osoba', how="left")

        ## Merge Strana
        organy = self.tbl['organy']
        snemovna_id = organy[organy.nazev_organ_cz=="Poslanecká sněmovna"].sort_values(by="id_organ").iloc[-1].id_organ
        snemovna_od = pd.to_datetime(organy[organy.id_organ == snemovna_id].iloc[0].od_organ)#.tz_localize(self.tzn)
        snemovna_do = pd.to_datetime(organy[organy.id_organ == snemovna_id].iloc[0].do_organ)#.tz_localize(self.tzn)

        snemovna_cond = (zarazeni_osoby.od_o >= snemovna_od) & (zarazeni_osoby.nazev_typ_organ_cz == "Klub") & (zarazeni_osoby.cl_funkce=='členství')
        if pd.isnull(snemovna_do) == False:
            snemovna_cond = snemovna_cond | (zarazeni_osoby.do_o >= snemovna_do)
        s = zarazeni_osoby[snemovna_cond].groupby('id_osoba').size().sort_values()
        prebehlici = s[s > 1]
        #print("prebehlici: ", prebehlici)

        for id_prebehlik in prebehlici.index:
            for idx, row in zarazeni_osoby[ snemovna_cond & (zarazeni_osoby.id_osoba == id_prebehlik)].iterrows():
                od, do, id_organ, zkratka =  row['od_o'], row['do_o'], row['id_organ'], row['zkratka']
                #print(id_prebehlik, od, do, id_organ, zkratka)
                self.tbl['steno_texty'].zkratka.mask((self.tbl['steno_texty'].date >= od) & (self.tbl['steno_texty'].date <= do) & (self.tbl['steno_texty'].id_osoba == id_prebehlik), zkratka, inplace=True)

        to_drop = ['zmena']
        self.tbl['steno_texty'].drop(labels=to_drop, inplace=True, axis=1)

        self.nastav_dataframe(self.tbl['steno_texty'])

        log.debug('<-- StenoTexty')

