import re
from collections import namedtuple

#import numpy as np
import pandas as pd

from html2text import html2text
from bs4 import BeautifulSoup, NavigableString

import os
import requests
from time import time
from pathlib import Path
from urllib.parse import urlparse
from joblib import Parallel, delayed, cpu_count

from parlamentikon.Helpers import MItem
from parlamentikon.utility import pretypuj, flatten

from parlamentikon.setup_logger import log

Rec = namedtuple("Rec", ['id_rec', 'id_osoba'])
Promluva = namedtuple('Promluva', ["text", "recnik", "rid", "cas_od", "cas_do"])
Cas = namedtuple('Cas', ['typ', 'hodina', 'minuta'])

class TabulkaStenotextyMixin(object):
    def nacti_steno_texty(self):
        header = {
            'text': MItem('string', 'Text promluvy s odstraněnými poznámkami (tj. bez textu v závorkách atp.)'),
            'text_s_poznamkami': MItem('string', 'Text promluvy včetně poznámek'),
            'schuze': MItem('Int64', 'Číslo schůze.'),
            'turn': MItem('Int64', 'Číslo stenozáznamu v rámci schůze.'),
            'id_osoba': MItem('Int64', 'Identifikátor osoby, viz Osoby:id_osoba.'),
            "id_rec": MItem('Int64', 'Identifikátor řečníka, viz StenoRecnici: id_rec'),
            'poznamka': MItem('string', 'Poznámka extrahovaá ze stenozáznamu.'),
            'je_poznamka': MItem('bool', 'Příznak, že celá promluva je poznámka.'),
            'cas': MItem('string', "Čas extrahovaný ze stenozáznamu."),
            'typ_casu': MItem('string', 'Typ času extrahovaného ze stenozáznamu [začátek, přerušení pokračování, ukončení, obecný].'),
            "date": MItem('string', 'Datum extrahované ze stenozáznamu.'),
            'hlasovani': MItem('Int64', 'Identifikátor hlasování (pole).'),
            'cislo_hlasovani': MItem('Int64', 'Číslo hlasování (pole).'),
        }
        path = f"{self.parameters['data_dir']}/steno_texty-{self.volebni_obdobi}.pkl"
        df = pd.read_pickle(path)
        self.rozsir_meta(header, tabulka='steno_texty', vlastni=False)

        self.tbl['steno_texty'], self.tbl['_steno_texty'] = df, df

    def stahni_steno_texty(self):
        path = f"{self.parameters['data_dir']}/steno_texty-{self.volebni_obdobi}.pkl"
        # scraping z webu
        self.stahni_html_data()
        # parsování html
        results, args = self.zpracuj_steno_texty()
        # tvorba pandas tabulky
        _steno_texty = self.results2df(results, args)
        # ulož lokálně výslednou tabulku
        _steno_texty.to_pickle(path)

    def results2df(self, results, args):
        texty = []
        texty_s_poznamkami = []
        schuze = []
        turns = []
        id_osoby = []
        id_reci = []
        poznamky = []
        je_poznamka = []
        cas = []
        typ_casu = []
        dates = []
        hlasovani = []
        cisla_hlasovani = []
        for result, arg in zip(results,  args):
            for r in result:
                id_osoba, id_rec = None, None
                if len(r['meta']['recnici']) > 0:
                    if r['meta']['recnici'][0].id_osoba != None:
                        id_osoba = int(r['meta']['recnici'][0].id_osoba)

                    if r['meta']['recnici'][0].id_rec != None:
                        id_rec = int(r['meta']['recnici'][0].id_rec)

                text = r['text']

                if len(r['meta']['poznamky']) > 0:
                    poznamka = r['meta']['poznamky']
                else:
                    poznamka = None

                if len(r['meta']['je_poznamka']) > 0:
                    je_poznamka_item = r['meta']['je_poznamka'][0]
                else:
                    je_poznamka_item = False

                if len(r['meta']['cas']) > 0:
                    c = f"{r['meta']['cas'][0].hodina}:{r['meta']['cas'][0].minuta}"
                    tc = r['meta']['cas'][0].typ
                else:
                    c, tc = None, None

                texty.append(r['text'])
                texty_s_poznamkami.append(r['meta']['text_s_poznamkami'])
                schuze.append(arg['schuze'])
                turns.append(arg['turn'])
                id_osoby.append(id_osoba)
                id_reci.append(id_rec)
                poznamky.append(poznamka)
                je_poznamka.append(je_poznamka_item)
                cas.append(c)
                typ_casu.append(tc)
                dates.append(r['meta']['date'])
                hlasovani.append(r['meta']['hlasovani'])
                cisla_hlasovani.append(r['meta']['cislo_hlasovani'])

        df = pd.DataFrame({'text': texty, 'text_s_poznamkami': texty_s_poznamkami, 'schuze': schuze, 'turn': turns, 'id_osoba': id_osoby, "id_rec": id_reci, 'poznamka': poznamky, 'je_poznamka': je_poznamka, 'cas': cas, 'typ_casu': typ_casu, "date": dates, 'hlasovani': hlasovani, 'cisla_hlasovani': cisla_hlasovani})

        return df

    def cesta(self, schuze, turn):
        return f"www.psp.cz/eknih/{self.volebni_obdobi}ps/stenprot/{schuze:03d}schuz/s{schuze:03d}{turn:03d}.htm"

    def zpracuj_steno_texty(self):
        args = [{
            "path": self.parameters['data_dir'] + '/' + self.cesta(item[0], item[1]),
            "schuze": item[0],
            "turn": item[1]
        } for item in self.tbl['steno'].groupby(['schuze', 'turn']).groups.keys()]# Do we need some kind of sort here?

        if ('limit' in self.parameters) and (self.parameters['limit'] != -1):
            args = args[:self.parameters['limit']]

        paths = [item['path'] for item in args]

        log.info(f"K zpracování: {len(paths)} souborů.")
        #n_jobs = max([12, 3*cpu_count()])
        #results = Parallel(n_jobs=-1, verbose=1, backend="threading")(delayed(self.zpracuj_stenozaznam)(item) for item in paths)
        results = Parallel(n_jobs=self.parameters['soubezne_zpracovani_max'], verbose=1, backend="threading")(delayed(self.zpracuj_stenozaznam)(item) for item in paths)

        return results, args

    def stahni_html_data(self):
        args = [["https://" + self.cesta(item[0], item[1]), self.parameters['data_dir'] ] for item in self.tbl['steno'].groupby(['schuze', 'turn']).groups.keys()]

        if ('limit' in self.parameters) and (self.parameters['limit'] != -1):
            args = args[:self.parameters['limit']]

        log.info(f"K stažení: {len(args)} souborů.")
        #n_jobs = max([12, 3*cpu_count()])
        #n_jobs = max([self.parameters['soubezne_stahovani_max'], 3*cpu_count()])
        n_jobs = self.parameters['soubezne_stahovani_max']
        Parallel(n_jobs=n_jobs, verbose=1, backend="threading")(delayed(self.stahni_url)(item) for item in args)

    def stahni_url(self, arg):
        url, dir_prefix = arg
        u = urlparse(url)
        n = u.netloc
        p = u.path
        filename = os.path.basename(p)
        d = os.path.dirname(p)
        dirname = dir_prefix + '/' + n + d
        path = dirname + '/' + filename
        #log.debug(f"path: '{path}'")
        Path(dirname).mkdir(parents=True, exist_ok=True)
        r = requests.get(url, stream = True)
        with open(path, 'wb') as f:
            for ch in r:
                f.write(ch)

    def load_soup(self, filename):
        data = open(filename, 'r', encoding='cp1250').read()
        return BeautifulSoup(data, 'html5lib') # Další varianty: 'lxml', 'html.parser'

    def polish(self, text):
        text = text.strip()
        text = re.sub(r'\n', ' ', text)
        text = re.sub(r'[ ]+', r' ', text)
        return text

    # * (poznámka) **
    def je_poznamka(self, tag):
        return re.match('^\s*\**\s*(\(.*?\))\s*\**\s*$', tag.string) != None

    # Musím vás poprosit o klid. (V sále je hluk.)
    def najdi_poznamky(self, tag):
        return re.findall('\((.*?)\)', tag.string)

    # (9.20 hodin)
    def najdi_cas(self, tag):
        s = tag.string
        if self.je_poznamka(tag):
            # čas zahájení
            m = re.match(r'.*zaháj.*[^0-9]+([0-9]{1,2})\s*[.:]\s*([0-9]{2}).*hod', s)
            if m:
                return Cas('zahájení', m.groups()[0], m.groups()[1])

            # čas přerušení
            m = re.match(r'.*přer.*[^0-9]+([0-9]{1,2})\s*[.:]\s*([0-9]{2}).*hod', s)
            if m:
                return Cas('přerušení', m.groups()[0], m.groups()[1])

            # čas pokračování
            m = re.match(r'.*pokrač.*[^0-9]+([0-9]{1,2})\s*[.:]\s*([0-9]{2}).*hod', s)
            if m:
                return Cas('pokračování', m.groups()[0], m.groups()[1])

            # čas ukončení
            m = re.match(r'.*konč.*[^0-9]+([0-9]{1,2})\s*[.:]\s*([0-9]{2}).*hod', s)
            if m:
                return Cas('ukončení', m.groups()[0], m.groups()[1])

            # obecná časová značka
            m = re.match(r'.*[^0-9]+([0-9]{1,2})\s*[.:]\s*([0-9]{2}).*hod', s)
            if m:
                return Cas('obecně', m.groups()[0], m.groups()[1])

        return None

    # id=r6  & href=https://www.psp.cz/sqw/detail.sqw?id=6452 ...
    # někdy se stane, že není možné identifikovat řečníka, ačkoliv lze určit id řeči
    def najdi_recnika(self, tag):
        if (tag.name == 'a') and tag.attrs and  tag.attrs.get('id') and (re.match(r'^r[0-9]+$', tag.attrs.get('id'))):
            id_rec = re.match(r'^r([0-9]+)$', tag.attrs.get('id')).groups()[0]
            id_osoba = None
            if tag.attrs.get('href'):
                m = re.match(r'\/sqw\/detail.sqw\?id\=([0-9]+)$', tag.attrs.get('href'))
                if m:
                    id_osoba = m.groups()[0]
            return Rec(id_rec=id_rec, id_osoba=id_osoba)
        return None

    #https://www.psp.cz/sqw/historie.sqw?T=922&O=8
    def najdi_tisk(self, tag):
        if (tag.name == 'a') and tag.attrs.get('href'):
            m = re.match(r'\/sqw\/historie.sqw\?T\=([0-9]+)\&O=([0-9])+$', tag.attrs.get('href'))
            if m:
                return m.groups()[0], m.groups()[1]
        return None

    # https://www.psp.cz/sqw/hlasy.sqw?G=74037
    def najdi_hlasovani(self, tag):
        if (tag.name == 'a') and tag.attrs.get('id') and (re.match(r'^h[0-9]+$', tag.attrs.get('id'))):
            hid = re.match(r'^h([0-9]+)$', tag.attrs.get('id')).groups()[0]
            G = None
            if tag.attrs.get('href'):
                m = re.match(r'\/sqw\/hlasy.sqw\?G\=([0-9]+)$', tag.attrs.get('href'))
                if m:
                    G = m.groups()[0]
            return hid, G
        return None

    def rozloz_tag(self, tag, text, meta):
        for child in tag.contents:
            if (child == None) or (child.string == None):
                continue
            for fce, klic in [
                [self.najdi_cas, 'cas'],
                [self.najdi_recnika, 'recnici'],
                [self.najdi_tisk, 'tisky'],
                [self.najdi_hlasovani, 'hlasovani'],
                [self.je_poznamka, 'je_poznamka'],
                [self.najdi_poznamky, 'poznamky']
            ]:
                ret = fce(child)
                if ret:
                    if (klic == 'hlasovani') and len(ret) > 0:
                        hid, G = ret
                        meta['cislo_hlasovani'].append(hid)
                        meta['hlasovani'].append(G)
                        continue
                    meta[klic].append(ret)

                # Promluvy jsou uvozeny jmény řečníků, která je nutné odstranit.
                # Děláme to tady hodně neohrabaně tak, že nastavíme příznak pro odstranění.
                # Samotné odstranění se provádí až ve volající funkci, protože se potřebujeme zbavit ':', která není součástí aktuálního tagu.
                if (klic == 'recnici') and (len(meta['recnici']) > 0) and (len(meta['odstran']) == 0):
                    meta['odstran'].append(self.polish(html2text(child.string)) + ' : ')

                # V jedné promluvě může být víc poznámek
                if (klic == 'poznamky') and (len(meta['poznamky']) > 0):
                    meta['poznamky'] = flatten(meta['poznamky'])

            if type(child) == NavigableString:
                t = html2text(child.string)
                text.append(t)
            else:
                self.rozloz_tag(child, text, meta)
        return

    def rozloz_paragraf(self, tag):
        meta = {"recnici": [], "hlasovani": [], 'cislo_hlasovani': [], "tisky": [], "poznamky": [], "je_poznamka": [], "cas": [], "odstran": [], "text_bez_poznamek": None}
        lines = []

        if tag is None:
            return '', meta

        # analyzuj vnořené tagy
        self.rozloz_tag(tag, lines, meta)
        #log.debug(f"LINES: {lines}")

        text = self.polish(' '.join(lines))

        if (len(meta['recnici']) > 0) and (len(meta['odstran']) > 0):
            for o in meta['odstran']:
                text = re.sub(o, '', text)

        meta['text_s_poznamkami'] = text
        text = re.sub(r"\((.*?)\)", '', text)

        meta['cislo_hlasovani'] = None if len(meta['cislo_hlasovani']) == 0 else meta['cislo_hlasovani'][0]
        meta['hlasovani'] = None if len(meta['hlasovani']) == 0 else meta['hlasovani'][0]

        return {"text": text, "meta": meta}

    def get_date(self, body):
        date_tag = body.find("p", class_='date')
        if date_tag is None:
            return
        return date_tag.string.extract()


    def parse_date(self, date):
        months_all = """led únor břez dub květ června července srp zář říj list prosin"""
        mo_beg = months_all.split()
        assert len(mo_beg) == 12

        toks = date.split()
        assert len(toks) == 4
        raw_day, raw_mo, raw_year = toks[1:]

        dt = raw_day.split('.')
        assert len(dt) == 2
        assert dt[1] == ""
        day = int(dt[0])
        assert 0 < day <= 31

        mo = None
        for i, prefix in enumerate(mo_beg):
            if raw_mo.startswith(prefix):
                mo = i + 1
                break
        assert not mo is None
        assert 1 <= mo <= 12

        year = int(raw_year)
        assert 2040 >= year >= 2000

        return "%d-%02d-%02d" % (year, mo, day)

    def zpracuj_stenozaznam(self, filename):
        if not os.path.exists(filename):
            log.error(f"Soubor {filename} neexistuje, přeskakuji.")
            return None

        basename = os.path.basename(filename).split('.')[0]
        soup = self.load_soup(filename)
        body = soup.find("div", id='body')

        if not body:
            log.error(f"V souboru '{filename}' chybí tag 'body', přeskakuji.")
            return None

        date = self.parse_date(self.get_date(body))
        date = pd.to_datetime(date, format="%Y-%m-%d")
        date = date.tz_localize(self.tzn)

        # for every turn [i.e. stenozaznam] we have with a new speaker list
        last_recnik = None

        rows = []
        for p in body.find_all('p', align=['justify']): # TODO: některé časové údaje jsou s align: center
            row = self.rozloz_paragraf(p)
            row['meta']['date'] = pd.to_datetime(date, format="%Y-%m-%d")
            row['meta']['date'] = row['meta']['date']

            if len(row['meta']['text_s_poznamkami']) == 0: # Check this...
                continue

            if len(row['meta']['recnici']) > 0:
                last_recnik = row['meta']['recnici'][0]
            elif last_recnik != None:
                # Fill in missing speakers for paragraphs.
                # Does not solve missing speakers on turn beginnings, we will have to deal with that separately later.
                row['meta']['recnici'].append(last_recnik)

            rows.append(row)
            #log.debug(f"ROW: {row}")
        return rows



