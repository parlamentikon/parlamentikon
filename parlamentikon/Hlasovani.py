
# Cesty k tabulkám, viz. https://www.psp.cz/sqw/hp.sqw?k=1302

from glob import glob
import pytz

import pandas as pd

from parlamentikon.utility import *

from parlamentikon.Snemovna import *
from parlamentikon.PoslanciOsoby import Osoby, Organy, ZarazeniOsoby, Poslanci
from parlamentikon.TabulkyHlasovani import *

from parlamentikon.setup_logger import log


# Agenda hlasování eviduje hlasování Poslanecké sněmovny, většinou prováděné hlasovacím zařízením. Ze seznamu hlasování jsou vyjmuta hlasování během neveřejných jednání Poslancké sněmovny.
# Pojem přihlášen znamená přihlášen k hlasovacímu zařízení a teprve v tomto stavu je jeho hlasování bráno v potaz. Zdržel se znamená stisknutí tlačítka X během hlasování, nehlasoval znamená nestisknutí žádného tlačítka během hlasování. Za výsledek hlasování poslance se bere naposledy stisknuté tlačítko hlasovacího zařízení během časového intervalu hlasování (20 sekund), neboli, poslanec může během této doby libovolně změnit svoje hlasování.
# Výsledek hlasování je stav výsledků hlasování jednotlivých poslanců na konci časového intervalu hlasování. Tj. pokud se poslanec během časového intervalu hlasování odhlásí od hlasovacího zařízení, je uveden jako nepřihlášen, poslanci se mohou přihlašovat do hlasovacího zařízení i během časového intervalu hlasování.
# Od účinnosti novely jednacího řádu 90/1995 Sb. se nerozlišuje zdržel se a nehlasoval, tj. příslušné počty se sčítají.
# Pokud skončí v průběhu volebního období poslanci mandát, ihned vzniká mandát jeho náhradníkovi, který se ujímá mandátu po složení slibu na první schůzi, které se zúčastní. Mezitím je ve výsledcích hlasování veden jako nepřihlášen (výsledek 'W').
# Upozornění: data omluv se mohou doplňovat se zpožděním a tedy počty omluvených se mohou lišit. Na výsledek hlasování to nemá žádný vliv, během hlasování není seznam omluvených k dispozici a omluvení poslanci jsou vedeni jako nepřihlášen.


class HlasovaniBase(Organy):

    def __init__(self, stahni=True, *args, **kwargs):
        log.debug("--> HlasovaniBase")

        super().__init__(stahni=stahni, *args, **kwargs)

        if stahni == True:
            self.stahni_zip_data(f"hl-{self.volebni_obdobi}ps")

        log.debug("<-- HlasovaniBase")


class Hlasovani(TabulkaHlasovaniMixin, TabulkaZmatecneHlasovaniMixin, TabulkaZpochybneniHlasovaniMixin, TabulkaHlasovaniVazbaStenozaznamMixin, HlasovaniBase):
    def __init__(self, *args, **kwargs):
        log.debug("--> Hlasovani")

        super().__init__(*args, **kwargs)

        self.nacti_hlasovani()
        self.nacti_zmatecne_hlasovani()
        self.nacti_zpochybneni_hlasovani()
        self.nacti_hlasovani_vazba_stenozaznam()

        # Zúžení dat na zvolené volební období. Tohle je asi nejjednodušší způsob.
        min_id = self.tbl['hlasovani'].id_hlasovani.min()
        max_id = self.tbl['hlasovani'].id_hlasovani.max()
        self.tbl['zmatecne'] = self.tbl['zmatecne'][
            (self.tbl['zmatecne'].id_hlasovani >= min_id)
            & (self.tbl['zmatecne'].id_hlasovani <= max_id)
        ]
        self.tbl['zpochybneni'] = self.tbl['zpochybneni'][
            (self.tbl['zpochybneni'].id_hlasovani >= min_id)
            & (self.tbl['zpochybneni'].id_hlasovani <= max_id)
        ]
        self.tbl['hlasovani_vazba_stenozaznam'] = self.tbl['hlasovani_vazba_stenozaznam'][
            (self.tbl['hlasovani_vazba_stenozaznam'].id_hlasovani >= min_id)
            & (self.tbl['hlasovani_vazba_stenozaznam'].id_hlasovani <= max_id)
        ]

        # Přidání indikátorů
        self.tbl['hlasovani']['ma_zpochybneni'] = self.tbl['hlasovani'].id_hlasovani.isin(self.tbl['zpochybneni'].id_hlasovani.unique())
        self.meta.nastav_hodnotu('ma_zpochybneni', dict(popis='Indikátor zpochybnění hlasování', tabulka='df', vlastni=True))

        self.tbl['hlasovani']['je_zmatecne'] = self.tbl['hlasovani'].id_hlasovani.isin(self.tbl['zmatecne'].id_hlasovani.unique())
        self.meta.nastav_hodnotu('je_zmatecne', dict(popis='Indikátor zmatečného hlasování', tabulka='df', vlastni=True))

        # Připojení informací o stenozaznamu. Pozor, nemusí být aktuální. Například pro snemovnu 2017 momentálně (16.2.2021) data chybí.
        self.tbl['hlasovani']['ma_stenozaznam'] = self.tbl['hlasovani'].id_hlasovani.isin(self.tbl['hlasovani_vazba_stenozaznam'].id_hlasovani.unique())
        self.meta.nastav_hodnotu('ma_stenozaznam', dict(popis='Indikátor existence stenozáznamu', tabulka='df', vlastni=True))

        suffix = '__hlasovani_vazba_stenozaznam'
        self.tbl['hlasovani'] = pd.merge(
            left=self.tbl['hlasovani'],
            right=self.tbl['hlasovani_vazba_stenozaznam'],
            on="id_hlasovani",
            how="left",
            suffixes=('', suffix)
        )
        self.drop_by_inconsistency(self.tbl['hlasovani'], suffix, 0.1, 'hlasovani', 'hlasovani_vazba_stenozaznam', inplace=True)

        self.nastav_dataframe(
            self.tbl['hlasovani'],
            odstran=['datum__ORIG', 'druh_hlasovani__ORIG', 'vysledek__ORIG', 'typ__ORIG']
        )
        # Uprav informace, které se přepsaly při načítání tabulek
        self.meta.loc['id_hlasovani', 'tabulka'] = 'hlasovani'

        log.debug("<-- Hlasovani")


class ZmatecneHlasovani(Hlasovani):
    def __init__(self, *args, **kwargs):
        log.debug("--> ZmatecneHlasovani")

        super().__init__(*args, **kwargs)
        self.nacti_zmatecne_hlasovani()

        suffix = "__hlasovani"
        self.tbl['zmatecne'] = pd.merge(left=self.tbl['zmatecne'], right=self.tbl['hlasovani'], on='id_hlasovani', suffixes = ("", suffix), how='left')
        self.tbl['zmatecne'] = self.drop_by_inconsistency(self.tbl['zmatecne'], suffix, 0.1, 'zmatecne', 'hlasovani')

        self.nastav_dataframe(self.tbl['zmatecne'])

        log.debug("<-- ZmatecneHlasovani")


class ZpochybneniHlasovani(Hlasovani):

    def __init__(self, *args, **kwargs):
        log.debug("--> ZpochybneniHlasovani")

        super().__init__(*args, **kwargs)

        self.nacti_zpochybneni_hlasovani()

        suffix = "__hlasovani"
        self.tbl['zpochybneni'] = pd.merge(left=self.tbl['zpochybneni'], right=self.tbl['hlasovani'], on='id_hlasovani', suffixes = ("", suffix), how='left')
        self.tbl['zpochybneni'] = self.drop_by_inconsistency(self.tbl['zpochybneni'], suffix, 0.1, 'zpochybneni', 'hlasovani')

        self.nastav_dataframe(self.tbl['zpochybneni'])

        log.debug("<-- ZpochybneniHlasovani")


class ZpochybneniPoslancem(TabulkaZpochybneniPoslancemMixin, Hlasovani, Organy, Osoby):

    def __init__(self, *args, **kwargs):
        log.debug("--> ZpochybneniPoslancem")

        super().__init__(*args, **kwargs)

        self.nacti_zpochybneni_poslancem()

        # Připojuje se tabulka 'hlasovani', nikoliv 'zpochybneni_hlasovani', protože není možné mapovat řádky 'zpochybneni_hlasovani' na 'zpochybneni_poslancem'. Jedná se zřejmě o nedokonalost datového modelu.
        suffix = "__hlasovani"
        self.tbl['zpochybneni_poslancem'] = pd.merge(left=self.tbl['zpochybneni_poslancem'], right=self.tbl['hlasovani'], on='id_hlasovani', suffixes = ("", suffix), how='left')
        self.drop_by_inconsistency(self.tbl['zpochybneni_poslancem'], suffix, 0.1, 'zpochybneni_poslancem', 'hlasovani', inplace=True)

        # Připoj informace o osobe # TODO: Neměli by se připojovat spíš Poslanci než Osoby?
        suffix = "__osoby"
        self.tbl['zpochybneni_poslancem'] = pd.merge(left=self.tbl['zpochybneni_poslancem'], right=self.tbl['osoby'], on='id_osoba', suffixes = ("", suffix), how='left')
        self.drop_by_inconsistency(self.tbl['zpochybneni_poslancem'], suffix, 0.1, 'zpochybneni_poslancem', 'osoby', inplace=True)

        id_organ_dle_volebniho_obdobi = self.tbl['organy'][(self.tbl['organy'].nazev_organ_cz == 'Poslanecká sněmovna') & (self.tbl['organy'].od_organ.dt.year == self.volebni_obdobi)].iloc[0].id_organ
        self.tbl['zpochybneni_poslancem'] = self.tbl['zpochybneni_poslancem'][self.tbl['zpochybneni_poslancem'].id_organ == id_organ_dle_volebniho_obdobi]

        self.nastav_dataframe(self.tbl['zpochybneni_poslancem'])

        log.debug("<-- ZpochybneniPoslancem")



class Omluvy(TabulkaOmluvyMixin, HlasovaniBase, Poslanci, ZarazeniOsoby, Organy):

    def __init__(self, *args, **kwargs):
        log.debug("--> Omluvy")

        super().__init__(*args, **kwargs)

        self.nacti_omluvy()

        # Připoj informace o poslanci
        suffix = "__poslanci"
        self.tbl['omluvy'] = pd.merge(left=self.tbl['omluvy'], right=self.tbl['poslanci'], on='id_poslanec', suffixes = ("", suffix), how='left')
        self.tbl['omluvy'] = self.drop_by_inconsistency(self.tbl['omluvy'], suffix, 0.1, 'omluvy', 'poslanci')

        # Zúžení na volební období
        self.tbl['omluvy'] = self.tbl['omluvy'][(self.tbl['omluvy'].id_parlament == self.snemovna.id_organ)]

        # Vyznačení poslanců v tabulce omluv
        om = self.tbl['omluvy']
        om['je_poslanec'] = False
        zo = self.tbl['zarazeni_osoby']
        zo_poslanci_snemovna = zo[(zo.id_organ==self.snemovna.id_organ) & (zo.cl_funkce=='členství')]

        for (id_osoba, od_o, do_o), _ in zo_poslanci_snemovna.groupby(['id_osoba', 'od_o', 'do_o'], dropna=False).size().iteritems():
          om.je_poslanec.mask(
            (om.id_osoba == id_osoba)
              & (om.den.dt.date >= od_o.date())
              & ((om.den.dt.date <= do_o.date()) | pd.isna(do_o)),
            True, inplace=True)

        self.meta.nastav_hodnotu('je_poslanec', dict(popis='Příznak, že omlouvající se osoba patří mezi poslance.', tabulka='df', vlastni=True))

        self.nastav_dataframe(self.tbl['omluvy'])

        log.debug("<-- Omluvy")


class HlasovaniPoslanci(TabulkaHlasovaniPoslanciMixin, Hlasovani, Poslanci, ZarazeniOsoby):

    def __init__(self, *args, **kwargs):
        log.debug("--> HlasovaniPoslance")

        super().__init__(*args, **kwargs)

        self.nacti_hlasovani_poslanci()

        # Připoj Poslance. Získáme mimo jiné také 'id_osoba'.
        self.tbl['hlasovani_poslance'] = pd.merge(left=self.tbl['hlasovani_poslance'], right=self.tbl['poslanci'], on="id_poslanec", suffixes=("", "__poslanci"), how='left')
        self.drop_by_inconsistency(self.tbl['hlasovani_poslance'], "__poslanci", 0.1, 'hlasovani_poslance', 'poslanci', inplace=True)
        self.tbl['hlasovani_poslance'] = self.tbl['hlasovani_poslance'][self.tbl['hlasovani_poslance'].id_parlament == self.snemovna.id_organ]

        # Připoj Hlasovani
        hlasovani_columns = ['id_hlasovani', 'schuze', 'cislo', 'bod', 'cas',
            'nazev_dlouhy', 'datum', 'bod__KAT',
            'druh_hlasovani', 'ma_zpochybneni', 'je_zmatecne']
        self.tbl['hlasovani_poslance'] = pd.merge(left=self.tbl['hlasovani_poslance'], right=self.tbl['hlasovani'][hlasovani_columns], on="id_hlasovani", suffixes=("", "__hlasovani"), how='left')
        self.drop_by_inconsistency(self.tbl['hlasovani_poslance'], "__hlasovani", 0.1, 'hlasovani_poslance', 'hlasovani', inplace=True)

        # Ze zarazeni_osoby získáme informace o tom, v jakém poslaneckém klubu byl daný poslanec v den hlasování
        zarazeni_osoby = self.tbl['zarazeni_osoby']

        # Vyber všechny osoby, které byly členy dané poslanecné sněmovny
        id_osoba_all = set(zarazeni_osoby[(zarazeni_osoby.id_organ==self.snemovna.id_organ) & (zarazeni_osoby.cl_funkce=='členství')].id_osoba)
        # Vyber všechna zařazení osob do poslaneckých klubů dané poslanecké sněmovny
        zarazeni_osoby_kluby = zarazeni_osoby[(zarazeni_osoby.id_osoba.isin(id_osoba_all)) & (zarazeni_osoby.nazev_typ_organ_cz == "Klub") & (zarazeni_osoby.cl_funkce=='členství')]\
            .rename(columns={
                'id_organ': 'id_klub',
                'nazev_organ_cz': 'nazev_klub_cz', 'zkratka': 'zkratka_klub',
                'od_o': 'od_klub', 'do_o': 'do_klub'
            })

        # Některé osoby mohli být zařazeny ve více klubech.
        # Pro každou osobu zatím vybereme poslední hodnotu, kterou pro přeběhlíky a nezařazené později upravíme.
        zarazeni_do_klubu = zarazeni_osoby_kluby.groupby('id_osoba').tail(1)

        # Nastav poslanecký klub pro všechny poslance.
        # Hodnota je správně jen pro poslance, kteří byli celou dobu v jediném klubu.
        # Přeběhlíky (poslance ve více klubech) nebo vystoupivší z klubů (nezařazené) budeme muset řešit zvlášť.
        self.tbl['hlasovani_poslance'] = pd.merge(
            self.tbl['hlasovani_poslance'],
            zarazeni_do_klubu[['id_osoba', 'id_klub', 'nazev_klub_cz', 'zkratka_klub']],
            on='id_osoba', how="left", suffixes=('', '__zarazeni_do_klubu')
        )
        self.drop_by_inconsistency(self.tbl['hlasovani_poslance'], "__zarazeni_do_klubu", 0.1, 'hlasovani_poslance', 'zarazeni_do_klubu', inplace=True, silent=True)
        #print(zarazeni_do_klubu.columns)
        #print(self.tbl['hlasovani_poslance'].columns)

        # Pro přeběhlíky a vystoupivší je nutné vybrat řádky se správným údajem o zařazení do klubu.
        s = zarazeni_osoby_kluby.groupby('id_osoba').size().sort_values()
        oprav_zarazeni = s[s > 1]

        for id_osoba in oprav_zarazeni.index:
            for idx, row in zarazeni_osoby_kluby[zarazeni_osoby_kluby.id_osoba == id_osoba].iterrows():
                od_klub, do_klub =  row['od_klub'], row['do_klub']
                id_klub, nazev_klub_cz, zkratka_klub =  row['id_klub'], row['nazev_klub_cz'], row['zkratka_klub']

                # nastav id_klub dle data hlasování (pro prebehliky a vystoupivší)
                self.tbl['hlasovani_poslance'].id_klub.mask(
                    (self.tbl['hlasovani_poslance'].id_osoba == id_osoba)
                      & (self.tbl['hlasovani_poslance'].datum >= od_klub)
                      & ((self.tbl['hlasovani_poslance'].datum <= do_klub) | (pd.isna(do_klub))),
                    id_klub, inplace=True)

                # nastav nazev_klub_cz dle data hlasování (pro prebehliky a vystoupivší)
                self.tbl['hlasovani_poslance'].nazev_klub_cz.mask(
                    (self.tbl['hlasovani_poslance'].id_osoba == id_osoba)
                      & (self.tbl['hlasovani_poslance'].datum >= od_klub)
                      & ((self.tbl['hlasovani_poslance'].datum <= do_klub) | (pd.isna(do_klub))),
                    nazev_klub_cz, inplace=True)

                # nastav zkratka_klub dle data hlasování (pro prebehliky a vystoupivší)
                self.tbl['hlasovani_poslance'].zkratka_klub.mask(
                    (self.tbl['hlasovani_poslance'].id_osoba == id_osoba)
                      & (self.tbl['hlasovani_poslance'].datum >= od_klub)
                      & ((self.tbl['hlasovani_poslance'].datum <= do_klub) | (pd.isna(do_klub))),
                    zkratka_klub, inplace=True)

        self.nastav_dataframe(
            self.tbl['hlasovani_poslance'],
            vyber = [
                'id_hlasovani', 'nazev_dlouhy', 'vysledek', # základní informace o hlasování poslance 
                'id_poslanec', 'id_osoba', 'pred', 'jmeno', 'prijmeni', # základní informace o poslanci
                'id_klub', 'nazev_klub_cz', 'zkratka_klub', #
                'narozeni', 'pohlavi', 'pred', 'za',
                'id_klub', 'nazev_klub_cz', 'zkratka_klub',
                'id_kraj', 'nazev_kraj_cz', 'zkratka_kraj',
                'id_kandidatka', 'nazev_kandidatka_cz', 'zkratka_kandidatka',
                'schuze', 'cislo', 'bod', 'cas', 'datum', 'bod__KAT',
                'druh_hlasovani', 'ma_zpochybneni', 'je_zmatecne'
                'id_organ', 'id_parlament', # informace o PS
            ],
            odstran = [
              'vysledek__ORIG', 'pohlavi__ORIG',
              'od_parlament', 'do_parlament',
              'web', 'ulice', 'obec', 'psc', 'telefon', 'fax', 'psp_telefon', 'email', 'facebook', 'foto', 'zmena', 'umrti', 'adresa', 'sirka', 'delka'
           ]
        )

        log.debug("<-- HlasovaniPoslance")

