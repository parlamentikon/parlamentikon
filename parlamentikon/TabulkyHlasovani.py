
  # Cesty k tabulkám, viz. https://www.psp.cz/sqw/hp.sqw?k=1302

from glob import glob
import pytz

import pandas as pd

from parlamentikon.utility import *

from parlamentikon.Snemovna import *
from parlamentikon.PoslanciOsoby import Osoby, Organy, Poslanci

from parlamentikon.setup_logger import log


class TabulkaHlasovaniMixin(object):
    def nacti_hlasovani(self):
        # Souhrnné informace o hlasování
        path = f"{self.parameters['data_dir']}/hl{self.volebni_obdobi}s.unl"
        self.paths['hlasovani'] = path
        header = {
            'id_hlasovani': MItem('Int64', 'Identifikátor hlasování'),
            'id_organ': MItem('Int64', 'Identifikátor orgánu, viz Organy:id_organ'),
            'schuze': MItem('Int64', 'Číslo schůze'),
            'cislo': MItem('Int64', 'Číslo hlasování'),
            'bod': MItem('Int64', 'Bod pořadu schůze; je-li menší než 1, pak jde o procedurální hlasování nebo o hlasování k bodům, které v době hlasování neměly přiděleno číslo.'),
            'datum__ORIG': MItem('string', 'Datum hlasování [den]'),
            'cas': MItem('string', 'Čas hlasování'),
            "pro": MItem('Int64', 'Počet hlasujících pro'),
            "proti": MItem('Int64', 'Počet hlasujících proti'),
            "zdrzel": MItem('Int64', 'Počet hlasujících zdržel se, tj. stiskl tlačítko X'),
            "nehlasoval": MItem('Int64', 'Počet přihlášených, kteří nestiskli žádné tlačítko'),
            "prihlaseno": MItem('Int64', 'Počet přihlášených poslanců'),
            "kvorum": MItem('Int64', 'Kvórum, nejmenší počet hlasů k přijetí návrhu'),
            "druh_hlasovani__ORIG": MItem('string', 'Druh hlasování: N - normální, R - ruční (nejsou známy hlasování jednotlivých poslanců)'),
            "vysledek__ORIG": MItem('string', 'Výsledek: A - přijato, R - zamítnuto, jinak zmatečné hlasování'),
            "nazev_dlouhy": MItem('string', 'Dlouhý název bodu hlasování'),
            "nazev_kratky": MItem('string', 'Krátký název bodu hlasování')
        }

        # Doporučené kódování 'cp1250' nefunguje, detekované 'ISO-8859-1' také nefunguje, 'ISO-8859-2' funguje.
        _df = pd.read_csv(path, sep="|", names = header.keys(),  index_col=False, encoding='ISO-8859-2')
        df = pretypuj(_df, header, name='hlasovani')
        self.rozsir_meta(header, tabulka='hlasovani', vlastni=False)

        # Odstraň whitespace z řetězců
        df = strip_all_string_columns(df)

        # Přidej 'datum'
        df['datum'] = pd.to_datetime(df['datum__ORIG'] + ' ' + df['cas'], format='%d.%m.%Y %H:%M')
        df['datum'] = df['datum'].dt.tz_localize(self.tzn)
        self.meta.nastav_hodnotu('datum', dict(popis='Datum hlasování', tabulka='hlasovani', vlastni=True))

        # Přepiš 'cas'
        df['cas'] = df['datum'].dt.time
        self.meta.nastav_hodnotu('cas', dict(popis='Čas hlasování', tabulka='hlasovani', vlastni=False))

        # Interpretuj 'bod pořadu'
        df["bod__KAT"] = df.bod.astype('string').mask(df.bod < 1, 'procedurální nebo bez přiděleného čísla').mask(df.bod >= 1, "normální")
        self.meta.nastav_hodnotu('bod__KAT', dict(popis='Katogorie bodu hlasování', tabulka='hlasovani', vlastni=True))

        # Interpretuj 'výsledek'
        mask = {'A': "přijato", 'R': 'zamítnuto'}
        df["vysledek"] = mask_by_values(df.vysledek__ORIG, mask).astype('string')
        self.meta.nastav_hodnotu('vysledek', dict(popis='Výsledek hlasování', tabulka='hlasovani', vlastni=True))

        # Interpretuj 'druh hlasování'
        mask = {'N': 'normální', 'R': 'ruční'}
        df["druh_hlasovani"] = mask_by_values(df.druh_hlasovani__ORIG, mask).astype('string')
        self.meta.nastav_hodnotu('druh_hlasovani', dict(popis='Druh hlasování', tabulka='hlasovani', vlastni=True))

        self.tbl['hlasovani'], self.tbl['_hlasovani'] = df, _df

class TabulkaZmatecneHlasovaniMixin(object):
    def nacti_zmatecne_hlasovani(self):
        # Hlasování, která byla prohlášena za zmatečné, tj. na jejich výsledek nebyl brán zřetel
        path = f"{self.parameters['data_dir']}/zmatecne.unl"
        self.paths['zmatecne_hlasovani'] = path
        header = {
            "id_hlasovani": MItem("Int64", 'Identifikátor hlasování.')
        }

        _df = pd.read_csv(path, sep="|", names = header.keys(),  index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, name='zmatecne')
        self.rozsir_meta(header, tabulka='zmatecne', vlastni=False)
        self.tbl['zmatecne'], self.tbl['_zmatecne'] = df, _df

class TabulkaZpochybneniHlasovaniMixin(object):
    # Načti tabulku zpochybneni hlasovani (hl_check)
    def nacti_zpochybneni_hlasovani(self):
        path = f"{self.parameters['data_dir']}/hl{self.volebni_obdobi}z.unl"
        self.paths['zpochybneni_hlasovani'] = path
        header = {
            "id_hlasovani": MItem('Int64', 'Identifikátor hlasování, viz Hlasovani:id_hlasovani.'),
            "turn": MItem('Int64', 'Číslo stenozáznamu, ve kterém je první zmínka o zpochybnění hlasování.'),
            "mode": MItem('Int64', 'Typ zpochybnění: 0 - žádost o opakování hlasování - v tomto případě se o této žádosti neprodleně hlasuje a teprve je-li tato žádost přijata, je hlasování opakováno; 1 - pouze sdělení pro stenozáznam, není požadováno opakování hlasování.'),
            "id_h2": MItem('Int64', 'Identifikátor hlasování o žádosti o opakování hlasování, viz hl_hlasovani:id_hlasovani. Zaznamenává se poslední takové, které nebylo zpochybněno.'),
            "id_h3": MItem('Int64', 'Identifikátor opakovaného hlasování, viz hl_hlasovani:id_hlasovani a hl_check:id_hlasovani. Zaznamenává se poslední takové, které nebylo zpochybněno.')
        }

        _df = pd.read_csv(path, sep="|", names = header.keys(),  index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, name='zpochybneni')
        self.rozsir_meta(header, tabulka='zpochybneni', vlastni=False)

        # 0 - žádost o opakování hlasování - v tomto případě se o této žádosti neprodleně hlasuje a teprve je-li tato žádost přijata, je hlasování opakováno;
        # 1 - pouze sdělení pro stenozáznam, není požadováno opakování hlasování.
        maska = {0: "žádost o opakování", 1: "pouze pro stenozáznam"}
        df["mode__KAT"] = mask_by_values(df["mode"], maska).astype('string')
        self.meta.nastav_hodnotu('mode__KAT', dict(popis='Typ zpochybnění', tabulka='zpochybneni', vlastni=True))

        # V tabulce ZpochybneniHlasovani mohou být nekonzistence a duplicity.
        # Pomocí indikátoru 'je_platne' se je pokusíme označit.
        # Jedná se o naši interpretaci dat, která může být mylná.
        platne_zh = df[
            (df.mode__KAT == 'pouze pro stenozáznam') |
            ((df.mode__KAT == 'žádost o opakování') & ~df.id_h2.isna())
        ].sort_values(
            by=['mode__KAT'],
            key= lambda col: sort_column_by_predefined_order(col, ['pouze pro stenozáznam', 'žádost o opakování'], how='tail')
        ).groupby('id_hlasovani').tail(1).sort_index()

        df['je_platne'] = df.index.isin(platne_zh.index)
        self.meta.nastav_hodnotu("Indikátor platného zpochybnění. Za platné zpochybnění určitého hlasování "
                "považujeme takové, které je v tabulce uvedené později, "
                "a 'mode__KAT' je buď s příznakem 'pouze pro stenozáznam', "
                "nebo má příznak 'žádost o opakování', "
                "přičemž o opakování hlasování se hlasovalo (viz ZpochybneniHlasovani:id_h2)",
            dict(popis='Indikátor existence stenozáznamu', tabulka='zpochybneni', vlastni=True))


        self.tbl['zpochybneni'], self.tbl['_zpochybneni'] = df, _df

class TabulkaHlasovaniVazbaStenozaznamMixin(object):
    def nacti_hlasovani_vazba_stenozaznam(self):
        ''' Načte tabulku vazeb hlasovani na stenozaznam.'''
        path = f"{self.parameters['data_dir']}/hl{self.volebni_obdobi}v.unl"
        self.paths['hlasovani_vazba_stenozaznam'] = path
        header = {
            "id_hlasovani": MItem('Int64', 'Identifikátor hlasování, viz hl_hlasovani:id_hlasovani'),
            "turn": MItem('Int64', 'Číslo stenozáznamu'),
            "typ__ORIG": MItem('Int64', 'Typ vazby: 0 - hlasování je v textu explicitně zmíněno a lze tedy vytvořit odkaz přímo na začátek hlasování, 1 - hlasování není v textu explicitně zmíněno, odkaz lze vytvořit pouze na stenozáznam jako celek.')
        }
        _df = pd.read_csv(path, sep="|", names = header.keys(),  index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, name='vazba_stenozaznam')

        self.rozsir_meta(header, tabulka='vazba_stenozaznam', vlastni=False)

        # Interpretuj 'typ'
        df["typ"] = mask_by_values(df.typ__ORIG, {0: "hlasovani zmíněno v stenozáznamu", 1: "hlasování není zmíněno v stenozáznamu"}).astype('string')
        self.meta.nastav_hodnotu('typ', dict(popis='Typ vazby na stenozáznam.', tabulka='vazba_stenozaznam', vlastni=True))
        # Vazba na stenozaznam nemusí být aktuální. Například pro sněmovnu 2017 je tabulka nevyplněná.
        self.tbl['hlasovani_vazba_stenozaznam'], self.tbl['_hlasovani_vazba_stenozaznam'] = df, _df


class TabulkaZpochybneniPoslancemMixin(object):
    def nacti_zpochybneni_poslancem(self):
        # Poslanci, kteří oznámili zpochybnění hlasování
        path = f"{self.parameters['data_dir']}/hl{self.volebni_obdobi}x.unl"
        self.paths['zpochybneni_poslancem'] = path
        header = {
            "id_hlasovani": MItem('Int64', 'Identifikátor hlasování, viz Hlasovani:id_hlasovani a ZpochybneniPoslancem:id_hlasovani, které bylo zpochybněno.'),
            "id_osoba": MItem('Int64', 'Identifikátor poslance, který zpochybnil hlasování; viz Osoby:id_osoba.'),
            "mode": MItem('Int64', 'Typ zpochybnění, viz ZpochybneniHlasovani:mode.')
        }

        _df = pd.read_csv(path, sep="|", names = header.keys(),  index_col=False, encoding='cp1250')
        df = pretypuj(_df, header)
        self.rozsir_meta(header, tabulka='zpochybneni_poslancem', vlastni=False)
        self.tbl['zpochybneni_poslancem'], self.tbl['_zpochybneni_poslancem'] = df, _df


class TabulkaOmluvyMixin(object):
    def nacti_omluvy(self):
        # Tabulka zaznamenává časové ohraničení omluv poslanců z jednání Poslanecké sněmovny.
        # Omluvy poslanců sděluje předsedající na začátku nebo v průběhu jednacího dne.
        # Data z tabulky se použijí pouze k nahrazení výsledku typu '@', tj. pokud výsledek hlasování jednotlivého poslance je nepřihlášen, pak pokud zároveň čas hlasování spadá do časového intervalu omluvy, pak se za výsledek považuje 'M', tj. omluven.
        #Pokud je poslanec omluven a zároveň je přihlášen, pak výsledek jeho hlasování má přednost před omluvou.
        path = f"{self.parameters['data_dir']}/omluvy.unl"
        self.paths['omluvy'] = path
        header = {
            "id_organ": MItem('Int64', 'Identifikátor volebního období, viz Organy:id_organ'),
            "id_poslanec": MItem('Int64', 'Identifikátor poslance, viz Poslanci:id_poslanec'), # Pozor: v tabulce jsou i omluvy z období, kdy už osoba není poslancem
            "den__ORIG": MItem('string', 'Datum omluvy'),
            "od__ORIG": MItem('string', 'Čas začátku omluvy, pokud je null, pak i omluvy:do je null a jedná se o omluvu na celý jednací den.'),
            "do__ORIG": MItem('string', 'Čas konce omluvy, pokud je null, pak i omluvy:od je null a jedná se o omluvu na celý jednací den.')
        }

        _df = pd.read_csv(path, sep="|", names = header,  index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, 'omluvy')
        df.drop_duplicates(keep='first', inplace=True)
        self.rozsir_meta(header, tabulka='omluvy', vlastni=False)

        df['od'] = format_to_datetime_and_report_skips(df, 'od__ORIG', to_format='%H:%M').dt.tz_localize(self.tzn).dt.time
        self.meta.nastav_hodnotu('od', dict(popis='Čas začátku omluvy.', tabulka='omluvy', vlastni=True))
        df['do'] = format_to_datetime_and_report_skips(df, 'do__ORIG', to_format='%H:%M').dt.tz_localize(self.tzn).dt.time
        self.meta.nastav_hodnotu('do', dict(popis='Čas konce omluvy.', tabulka='omluvy', vlastni=True))
        df['den'] = format_to_datetime_and_report_skips(df, 'den__ORIG', to_format='%d.%m.%Y').dt.tz_localize(self.tzn)
        self.meta.nastav_hodnotu('den', dict(popis='Datum omluvy [den].', tabulka='omluvy', vlastni=True))

        # TODO: Přidej sloupec typu 'datum_od', 'datum_do'
        # O začátcích a koncích omluv je možné něco zjistit z tabulky Stentexty, ale nebude to moc spolehlivé.
        #df['datum_od'] = pd.to_datetime(df['den'] + ' ' + df['od'], format='%d.%m.%Y %H:%M')
        #df['datum_do'] = pd.to_datetime(df['den'] + ' ' + df['od'], format='%d.%m.%Y %H:%M')

        self.tbl['omluvy'], self.tbl['_omluvy'] = df, _df



class TabulkaHlasovaniPoslanciMixin(object):
    def nacti_hlasovani_poslanci(self):
        # V souborech uložena jako hlXXXXhN.unl, kde XXXX je reference volebního období a N je číslo části. V 6. a 7. volebním období obsahuje část č. 1 hlasování 1. až 50. schůze, část č. 2 hlasování od 51. schůze.
        paths = glob(f"{self.parameters['data_dir']}/hl{self.volebni_obdobi}h*.unl")
        self.paths['hlasovani_poslanci'] = paths
        header = {
            'id_poslanec': MItem('Int64', 'Identifikátor poslance, viz Poslanci:id_poslanec'),
            'id_hlasovani': MItem('Int64', 'Identifikátor hlasování, viz Hlasovani:id_hlasovani'),
            'vysledek__ORIG': MItem('string',"Hlasování jednotlivého poslance. 'A' - ano, 'B' nebo 'N' - ne, 'C' - zdržel se (stiskl tlačítko X), 'F' - nehlasoval (byl přihlášen, ale nestiskl žádné tlačítko), '@' - nepřihlášen, 'M' - omluven, 'W' - hlasování před složením slibu poslance, 'K' - zdržel se/nehlasoval. Viz úvodní vysvětlení zpracování výsledků hlasování.")
        }

        # Hlasovani poslance může být ve více souborech
        frames = []
        for f in paths:
          frames.append(pd.read_csv(f, sep="|", names = header,  index_col=False, encoding='cp1250'))

        _df = pd.concat(frames, ignore_index=True)
        df = pretypuj(_df, header, name='hlasovani_poslance')
        self.rozsir_meta(header, tabulka='hlasovani_poslance', vlastni=False)

        mask = {'A': 'ano', 'B': 'ne', 'N': 'ne', 'C': 'zdržení se', 'F': 'nehlasování', '@': 'nepřihlášení', 'M': 'omluva', 'W': 'hlasování bez slibu', 'K': 'zdržení/nehlasování'}
        df['vysledek'] = mask_by_values(df.vysledek__ORIG, mask).astype('string')
        self.meta.nastav_hodnotu('vysledek', dict(popis='Hlasování jednotlivého poslance.', tabulka='hlasovani_poslance', vlastni=True))

        self.tbl['hlasovani_poslance'], self.tbl['_hlasovani_poslance'] = df, _df

