
# Tabulky Poslanci a Osoby

from os import path

import pandas as pd
import numpy as np

from parlamentikon.utility import *
from parlamentikon.Snemovna import *
from parlamentikon.setup_logger import log


class TabulkaTypOrganMixin(object):
    def nacti_typ_organ(self):
        path = f"{self.parameters['data_dir']}/typ_organu.unl"
        header = {
            'id_typ_organ': MItem('Int64', 'Identifikátor typu orgánu'),
            'typ_id_typ_organ': MItem('Int64', 'Identifikátor nadřazeného typu orgánu (TypOrgan:id_typ_organ), pokud je null či nevyplněno, pak nemá nadřazený typ'),
            'nazev_typ_organ_cz': MItem('string', 'Název typu orgánu v češtině'),
            'nazev_typ_organ_en': MItem('string', 'Název typu orgánu v angličtině'),
            'typ_organ_obecny': MItem('Int64', 'Obecný typ orgánu, pokud je vyplněný, odpovídá záznamu v TypOrgan:id_typ_organ. Pomocí tohoto sloupce lze najít např. všechny výbory v různých typech zastupitelských sborů.'),
            'priorita': MItem('Int64', 'Priorita při výpisu')
        }
        _df = pd.read_csv(path, sep="|", names = header.keys(), index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, name='typ_organ')
        self.rozsir_meta(header, tabulka='typ_organ', vlastni=False)
        self.tbl['typ_organ'], self.tbl['_typ_organ'] = df, _df


class TabulkaOrganyMixin(object):
    def nacti_organy(self):
        path = f"{self.parameters['data_dir']}/organy.unl"
        header = {
            "id_organ": MItem('Int64', 'Identifikátor orgánu'),
            "organ_id_organ": MItem('Int64', 'Identifikátor nadřazeného orgánu, viz Organy:id_organ'),
            "id_typ_organ": MItem('Int64', 'Typ orgánu, viz TypOrgan:id_typ_organ'),
            "zkratka": MItem('string', 'Zkratka orgánu, bez diakritiky, v některých připadech se zkratka při zobrazení nahrazuje jiným názvem'),
            "nazev_organ_cz": MItem("string", 'Název orgánu v češtině'),
            "nazev_organ_en": MItem("string", 'Název orgánu v angličtině'),
            "od_organ": MItem('string', 'Ustavení orgánu'),
            "do_organ": MItem('string', 'Ukončení orgánu'),
            "priorita": MItem('Int64', 'Priorita výpisu orgánů'),
            "cl_organ_base": MItem('Int64', 'Pokud je nastaveno na 1, pak při výpisu členů se nezobrazují záznamy v tabulkce zarazeni kde cl_funkce == 0. Toto chování odpovídá tomu, že v některých orgánech nejsou členové a teprve z nich se volí funkcionáři, ale přímo se volí do určité funkce.')
        }
        _df = pd.read_csv(path, sep="|", names = header.keys(), index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, name='organy')
        self.rozsir_meta(header, tabulka='organy', vlastni=False)
        df['od_organ'] = format_to_datetime_and_report_skips(df, 'od_organ', '%d.%m.%Y').dt.tz_localize(self.tzn)
        df['do_organ'] = format_to_datetime_and_report_skips(df, 'do_organ', '%d.%m.%Y').dt.tz_localize(self.tzn)
        self.tbl['organy'], self.tbl['_organy'] = df, _df

class TabulkaTypFunkceMixin(object):
    def nacti_typ_funkce(self):
        path = f"{self.parameters['data_dir']}/typ_funkce.unl"
        header = {
            'id_typ_funkce': MItem('Int64', 'Identifikator typu funkce'),
            'id_typ_organ': MItem('Int64', 'Identifikátor typu orgánu, viz TypOrgan:id_typ_organ'),
            'typ_funkce_cz': MItem('string', 'Název typu funkce v češtině'),
            'typ_funkce_en': MItem('string', 'Název typu funkce v angličtině'),
            'priorita': MItem('Int64', 'Priorita při výpisu'),
            'typ_funkce_obecny__ORIG': MItem('Int64', 'Obecný typ funkce, 1 - předseda, 2 - místopředseda, 3 - ověřovatel, jiné hodnoty se nepoužívají.')

        }

        _df = pd.read_csv(path, sep="|", names = header.keys(), index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, name='typ_funkce')
        self.rozsir_meta(header, tabulka='typ_funkce', vlastni=False)

        mask = {1: "předseda", 2: "místopředseda", 3: "ověřovatel"}
        df['typ_funkce_obecny'] = mask_by_values(df.typ_funkce_obecny__ORIG, mask).astype('string')
        self.meta.nastav_hodnotu('typ_funkce_obecny', dict(popis='Obecný typ funkce.', tabulka='typ_funkce', vlastni=True))

        self.tbl['typ_funkce'], self.tbl['_typ_funkce'] = df, _df


class TabulkaFunkceMixin(object):
    def nacti_funkce(self):
        path = f"{self.parameters['data_dir']}/funkce.unl"
        header = {
            "id_funkce": MItem('Int64', 'Identifikátor funkce, používá se v ZarazeniOsoby:id_fo'),
            "id_organ": MItem('Int64', 'Identifikátor orgánu, viz Organy:id_organ'),
            "id_typ_funkce": MItem('Int64', 'Typ funkce, viz typ_funkce:id_typ_funkce'),
            "nazev_funkce_cz": MItem('string', 'Název funkce, pouze pro interní použití'),
            "priorita": MItem('Int64', 'Priorita výpisu')
        }

        _df = pd.read_csv(path, sep="|", names = header.keys(), index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, name='funkce')
        self.rozsir_meta(header, tabulka='funkce', vlastni=False)

        self.tbl['funkce'], self.tbl['_funkce'] = df, _df

    def vyber_platne_funkce(self):
        if self.volebni_obdobi != -1:
            self.tbl['funkce'] = self.tbl['funkce'][self.tbl['funkce'].id_organ.isin(self.tbl['organy'].id_organ)]



class TabulkaOsobyMixin(object):
    def nacti_osoby(self):
        # Obsahuje jména osob, které jsou zařazeni v orgánech.
        # Vzhledem k tomu, že k jednoznačnému rozlišení osob často není dostatek informací, je možné, že ne všechny záznamy odkazují na jedinečné osoby, tj. některé osoby jsou v tabulce vícekrát.
        path = f"{self.parameters['data_dir']}/osoby.unl"
        header = {
            "id_osoba": MItem("Int64", 'Identifikátor osoby'),
            "pred": MItem('string', 'Titul pred jmenem'),
            "prijmeni": MItem('string', 'Příjmení, v některých případech obsahuje i dodatek typu "st.", "ml."'),
            "jmeno": MItem('string', 'Jméno'),
            "za": MItem('string', 'Titul za jménem'),
            "narozeni": MItem('string', 'Datum narození, pokud neznámo, pak 1.1.1900.'),
            'pohlavi__ORIG': MItem('string', 'Pohlaví, "M" jako muž, ostatní hodnoty žena'),
            "zmena": MItem('string', 'Datum posledni změny'),
            "umrti": MItem('string', 'Datum úmrtí')
        }
        _df = pd.read_csv(path, sep="|", names = header.keys(), index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, 'osoby')
        self.rozsir_meta(header, tabulka='osoby', vlastni=False)

        df["pohlavi"] = mask_by_values(df.pohlavi__ORIG, {'M': "muž", 'Z': 'žena', 'Ž': 'žena'}).astype('string')
        self.meta.nastav_hodnotu('pohlavi', dict(popis='Pohlaví.', tabulka='osoby', vlastni=True))

        # Parsuj narození, meta informace není třeba přidávat, jsou v hlavičce
        #df['narozeni'] = pd.to_datetime(df['narozeni'], format="%d.%m.%Y", errors='coerce').dt.tz_localize(self.tzn)
        df['narozeni'] = format_to_datetime_and_report_skips(df, 'narozeni', to_format="%d.%m.%Y").dt.tz_localize(self.tzn)
        df['narozeni'] = df.narozeni.mask(df.narozeni.dt.strftime("%d.%m.%Y") == '01.01.1900', pd.NaT)

        # Parsuj úmrtí, meta informace není třeba přidávat, jsou v hlavičce
        df['umrti'] = format_to_datetime_and_report_skips(df, 'umrti', to_format="%d.%m.%Y").dt.tz_localize(self.tzn)
        df['umrti'] = df.umrti.mask(df.umrti.dt.strftime("%d.%m.%Y") == '01.01.1900', pd.NaT)
        # Parsuj datum poslední změny záznamu, meta informace není třeba přidávat, jsou v hlavičce
        df['zmena'] = format_to_datetime_and_report_skips(df, 'zmena', to_format="%d.%m.%Y").dt.tz_localize(self.tzn)

        self.tbl['osoby'], self.tbl['_osoby'] = df, _df

class TabulkaOsobaExtraMixin(object):
    def nacti_osoba_extra(self):
    # Tabulka obsahuje vazby na externí systémy. Je-li typ = 1, pak jde o vazbu na evidenci senátorů na senat.cz
        path = f"{self.parameters['data_dir']}/osoba_extra.unl"
        header = {
            'id_osoba': MItem('Int64', 'Identifikátor osoby, viz Osoba:id_osoba'),
            'id_organ': MItem('Int64', 'Identifikátor orgánu, viz Organy:id_organ'),
            'typ': MItem('Int64', 'Typ záznamu, viz výše. [??? Asi chtěli napsat níže ...]'),
            'obvod': MItem('Int64', 'Je-li typ = 1, pak jde o číslo senátního obvodu.'),
            'strana': MItem('string', 'Je-li typ = 1, pak jde o název volební strany/hnutí či označení nezávislého kandidáta'),
            'id_external': MItem('Int64', 'Je-li typ = 1, pak je to identifikátor senátora na senat.cz')
        }

        _df = pd.read_csv(path, sep="|", names = header.keys(), index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, 'osoba_extra')
        self.rozsir_meta(header, tabulka='osoba_extra', vlastni=False)
        self.tbl['osoba_extra'], self.tbl['_osoba_extra'] = df, _df


class TabulkaZarazeniOsobyMixin(object):
    def nacti_zarazeni_osoby(self):
        path = f"{self.parameters['data_dir']}/zarazeni.unl"
        header = {
            'id_osoba': MItem('Int64', 'Identifikátor osoby, viz Osoby:id_osoba'),
            'id_of': MItem('Int64', 'Identifikátor orgánu či funkce: pokud je zároveň nastaveno zarazeni:cl_funkce == 0, pak id_o odpovídá Organy:id_organ, pokud cl_funkce == 1, pak odpovídá Funkce:id_funkce.'),
            'cl_funkce__ORIG': MItem('Int64', 'Status členství nebo funce: pokud je rovno 0, pak jde o členství, pokud 1, pak jde o funkci.'),
            'od_o': MItem('string', 'Zařazení od. [year to hour]'),
            'do_o':  MItem('string', 'Zařazení do. [year to hour]'),
            'od_f': MItem('string', 'Mandát od. Nemusí být vyplněno a pokud je vyplněno, pak určuje datum vzniku mandátu a ZarazeniOsoby:od_o obsahuje datum volby. [date]'),
            'do_f': MItem('string', 'Mandát do. Nemusí být vyplněno a pokud je vyplněno, určuje datum konce mandátu a ZarazeniOsoby:do_o obsahuje datum ukončení zařazení. [date]')
        }
        _df = pd.read_csv(path, sep="|", names = header.keys(), index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, 'zarazeni_osoby')
        self.rozsir_meta(header, tabulka='zarazeni_osoby', vlastni=False)

        df['od_o'] = format_to_datetime_and_report_skips(df, 'od_o', '%Y-%m-%d %H').dt.tz_localize(self.tzn)
        # Fix known errors
        ids = df[(df.do_o == '0205-06-09 00') & (df.id_osoba == 349) & (df.id_of == 853)].index
        #print(ids)
        df.at[ids, 'do_o']  = '2005-06-09 00'

        df['do_o'] = format_to_datetime_and_report_skips(df, 'do_o', '%Y-%m-%d %H').dt.tz_localize(self.tzn)
        df['od_f'] = format_to_datetime_and_report_skips(df, 'od_f', '%d.%m.%Y').dt.tz_localize(self.tzn)
        df['do_f'] = format_to_datetime_and_report_skips(df, 'do_f', '%d.%m.%Y').dt.tz_localize(self.tzn)

        mask = {0: 'členství', 1: 'funkce'}
        df['cl_funkce'] = mask_by_values(df.cl_funkce__ORIG, mask).astype('string')
        self.meta.nastav_hodnotu('cl_funkce', dict(popis='Status členství nebo funkce.', tabulka='zarazeni_osoby', vlastni=True))
        self.tbl['zarazeni_osoby'], self.tbl['_zarazeni_osoby'] = df, _df

class TabulkaPoslanciMixin(object):
        # Další informace o poslanci vzhledem k volebnímu období: kontaktní údaje, adresa regionální kanceláře a podobně.
        # Některé údaje jsou pouze v aktuálním volebním období.
    def nacti_poslance(self):
        path = f"{self.parameters['data_dir']}/poslanec.unl"
        header = {
            "id_poslanec": MItem('Int64', 'Identifikátor poslance'),
            "id_osoba": MItem('Int64', 'Identifikátor osoby, viz Osoby:id_osoba'),
            "id_kraj": MItem('Int64', 'Volební kraj, viz Organy:id_organ'),
            "id_kandidatka": MItem('Int64', 'Volební strana/hnutí, viz Organy:id_organ, pouze odkazuje na stranu/hnutí, za kterou byl zvolen a nemusí mít souvislost s členstvím v poslaneckém klubu.'),
            "id_organ":  MItem('Int64', 'Volební období, viz Organy:id_organ'),
            "web": MItem('string', 'URL vlastních stránek poslance'),
            "ulice": MItem('string', 'Adresa regionální kanceláře, ulice.'),
            "obec": MItem('string', 'Adresa regionální kanceláře, obec.'),
            "psc": MItem('string', 'Adresa regionální kanceláře, PSČ.'),
            "email": MItem('string', 'E-mailová adresa poslance, případně obecná posta@psp.cz.'),
            "telefon": MItem('string', 'Adresa regionální kanceláře, telefon.'),
            "fax": MItem('string', 'Adresa regionální kanceláře, fax.'),
            "psp_telefon": MItem('string', 'Telefonní číslo do kanceláře v budovách PS.'),
            "facebook": MItem('string', 'URL stránky služby Facebook.'),
            "foto": MItem('Int64', 'Pokud je rovno 1, pak existuje fotografie poslance.')
        }

        _df = pd.read_csv(path, sep="|", names = header.keys(), index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, 'poslanci')
        self.rozsir_meta(header, tabulka='poslanci', vlastni=False)
        self.tbl['poslanci'], self.tbl['_poslanci'] = df, _df

class TabulkaPoslanciPkgpsMixin(object):
    def nacti_poslanci_pkgps(self):
        # Obsahuje GPS souřadnice regionálních kanceláří poslanců.
        path = f"{self.parameters['data_dir']}/pkgps.unl"
        header = {
            'id_poslanec': MItem('Int64', 'Identifikátor poslance, viz Poslanci:id_poslanec'),
            'adresa': MItem('string', 'Adresa kanceláře, jednotlivé položky jsou odděleny středníkem'),
            'sirka': MItem('string', 'Severní šířka, WGS 84, formát GG.AABBCCC, GG = stupně, AA - minuty, BB - vteřiny, CCC - tisíciny vteřin'),
            'delka': MItem('string', 'Východní délka, WGS 84, formát GG.AABBCCC, GG = stupně, AA - minuty, BB - vteřiny, CCC - tisíciny vteřin')
        }
        _df = pd.read_csv(path, sep="|", names = header.keys(), index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, 'poslanci_pkgps')
        self.rozsir_meta(header, tabulka='poslanci_pkgps', vlastni=False)
        self.tbl['poslanci_pkgps'], self.tbl['_poslanci_pkgps'] = df, _df

