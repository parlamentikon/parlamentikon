
# Poslanci a Osoby
# Agenda eviduje osoby, jejich zařazení do orgánů a jejich funkce v orgánech a orgány jako takové.
# Informace viz https://www.psp.cz/sqw/hp.sqw?k=1301.

from os import path

import pandas as pd
import numpy as np

from parlamentikon.utility import *
from parlamentikon.Snemovna import *
from parlamentikon.TabulkyPoslanciOsoby import *
from parlamentikon.setup_logger import log


class PoslanciOsobyBase(SnemovnaZipDataMixin, SnemovnaDataFrame):
    """Obecná třída pro dceřiné třídy (Osoby, Organy, Poslanci, etc.)"""

    def __init__(self, stahni=True, *args, **kwargs):
        log.debug("--> PoslanciOsobyBase")

        super().__init__(*args, **kwargs)

        if stahni == True:
            self.stahni_zip_data("poslanci")

        log.debug("<-- PoslanciOsobyBase")

class TypOrgan(TabulkaTypOrganMixin, PoslanciOsobyBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nacti_typ_organ()
        self.nastav_dataframe(
            self.tbl['typ_organ'],
            odstran=['priorita'],
            vyber=['id_typ_organ', 'nazev_typ_organ_cz', 'nazev_typ_organ_en'])


class Organy(TabulkaOrganyMixin, TypOrgan):
    def __init__(self, *args, **kwargs):
        log.debug("--> Organy")
        super().__init__(*args, **kwargs)

        self.nacti_organy()

        # Připoj Typu orgánu
        suffix = "__typ_organ"
        self.tbl['organy'] = pd.merge(left=self.tbl['organy'], right=self.tbl['typ_organ'], on="id_typ_organ", suffixes=("",suffix), how='left')
        # Odstraň nedůležité sloupce 'priorita', protože se vzájemně vylučují a nejspíš k ničemu nejsou.
        # Tímto se vyhneme varování funkce 'drop_by_inconsistency.
        self.tbl['organy'].drop(columns=["priorita", "priorita__typ_organ"], inplace=True)
        self.tbl['organy'] = self.drop_by_inconsistency(self.tbl['organy'], suffix, 0.1, 'organy', 'typ_organ')

        # Nastav volební období, pokud chybí
        if self.volebni_obdobi == None:
            self.volebni_obdobi = self._posledni_snemovna().od_organ.year
            log.debug(f"Nastavuji začátek volebního období na: {self.volebni_obdobi}.")

        if self.volebni_obdobi != -1:
            x = self.tbl['organy'][
                (self.tbl['organy'].nazev_organ_cz == 'Poslanecká sněmovna')
                & (self.tbl['organy'].od_organ.dt.year == self.volebni_obdobi)
            ]
            if len(x) == 1:
                self.snemovna = x.iloc[0]
            else:
                log.error('Bylo nalezeno více sněmoven pro dané volební období!')
                raise ValueError

        self.tbl['organy'] = self.vyber_platne_organy()
        self.nastav_dataframe(self.tbl['organy'])

        log.debug("<-- Organy")

    def vyber_platne_organy(self, df=None):
        if df == None:
            df = self.tbl['organy']
        if self.volebni_obdobi == -1:
            return df

        ids_snemovnich_organu = expand_hierarchy(df, 'id_organ', 'organ_id_organ', [self.snemovna.id_organ])

        # TODO: Kdy použít od_f místo od_o, resp. do_f místo do_o?
        interval_start = df.od_organ\
            .mask(df.od_organ.isna(), self.snemovna.od_organ)\
            .mask(~df.od_organ.isna(), np.maximum(df.od_organ, self.snemovna.od_organ))

        # Pozorování: volebni_obdobi_od není nikdy NaT => interval_start není nikdy NaT
        if pd.isna(self.snemovna.do_organ): # příznak posledního volebního období
            podminka_interval = (
                (interval_start.dt.date <= df.do_organ.dt.date) # Nutná podmínka pro True: (interval_start != NaT, splněno vždy) a (do_organ != NaT)
                |  df.do_organ.isna() # Nutná podmínka pro True: (interval_start != NaT, splněno vždy) a (do_organ == NaT)
            )
        else: # Pozorování: předchozí volební období => interval_end není nikdy NaT
            interval_end = df.do_organ\
                .mask(df.do_organ.isna(), self.snemovna.do_organ)\
                .mask(~df.do_organ.isna(), np.minimum(df.do_organ, self.snemovna.do_organ))
            podminka_interval = (interval_start.dt.date <= interval_end.dt.date)

        ids_jinych_snemoven = []

        x = self._predchozi_snemovna()
        if x is not None:
            ids_jinych_snemoven.append(x.id_organ)

        x = self._nasledujici_snemovna()
        if x is not None:
            ids_jinych_snemoven.append(x.id_organ)

        #ids_jinych_snemovnich_organu = find_children_ids(ids_jinych_snemoven, 'id_organ', df, 'organ_id_organ', ids_jinych_snemoven, 0)
        ids_jinych_snemovnich_organu = expand_hierarchy(df, 'id_organ', 'organ_id_organ', ids_jinych_snemoven)
        podminka_nepatri_do_jine_snemovny = ~df.id_organ.isin(ids_jinych_snemovnich_organu)

        df = df[
            (df.id_organ.isin(ids_snemovnich_organu) == True)
            | (podminka_interval & podminka_nepatri_do_jine_snemovny)
        ]

        return df

    def _posledni_snemovna(self):
        """Pomocná funkce, vrací data poslední sněmovny"""
        p =  self.tbl['organy'][(self.tbl['organy'].nazev_organ_cz == 'Poslanecká sněmovna') & (self.tbl['organy'].do_organ.isna())].sort_values(by=["od_organ"])
        if len(p) == 1:
            return p.iloc[0]
        else:
            return None

    def _predchozi_snemovna(self, id_organ=None):
        """Pomocná funkce, vrací data předchozí sněmovny"""

        # Pokud nebylo zadáno id_orgánu, implicitně vezmi id_organ dané sněmovny.
        if id_organ == None:
            id_organ = self.snemovna.id_organ

        snemovny = self.tbl['organy'][self.tbl['organy'].nazev_organ_cz == 'Poslanecká sněmovna'].sort_values(by="do_organ").copy()
        snemovny['id_predchozi_snemovny'] = snemovny.id_organ.shift(1)
        idx = snemovny[snemovny.id_organ == id_organ].iloc[0].id_predchozi_snemovny
        p = snemovny[snemovny.id_organ == idx]

        assert len(p) <= 1

        if len(p) == 1:
          return p.iloc[0]
        else:
          return None

    def _nasledujici_snemovna(self, id_organ=None):
        """Pomocná funkce, vrací data následující sněmovny"""

        # Pokud nebylo zadáno id_orgánu, implicitně vezmi id_organ dané sněmovny.
        if id_organ == None:
            id_organ = self.snemovna.id_organ

        snemovny = self.tbl['organy'][self.tbl['organy'].nazev_organ_cz == 'Poslanecká sněmovna'].sort_values(by="do_organ").copy()
        snemovny['id_nasledujici_snemovny'] = snemovny.id_organ.shift(-1)
        idx = snemovny[snemovny.id_organ == id_organ].iloc[0].id_nasledujici_snemovny
        p = snemovny[snemovny.id_organ == idx]

        assert len(p) <= 1

        if len(p) == 1:
          return p.iloc[0]
        else:
          return None


# Tabulka definuje typ funkce v orgánu - pro každý typ orgánu jsou definovány typy funkcí. Texty názvů typu funkce se používají při výpisu namísto textů v Funkce:nazev_funkce_LL .
# Třída TypFunkce nebere v úvahu závislost na volebnim obdobi, protože tu je možné získat až pomocí dceřinných tříd (ZarazeniOsoby).
class TypFunkce(TabulkaTypFunkceMixin, TypOrgan):
    def __init__(self, *args, **kwargs):
        log.debug("--> TypFunkce")
        super().__init__(*args, **kwargs)

        self.nacti_typ_funkce()

        # Připoj Typu orgánu
        suffix="__typ_organ"
        self.tbl['typ_funkce'] = pd.merge(
            left=self.tbl['typ_funkce'],
            right=self.tbl['typ_organ'],
            on="id_typ_organ",
            suffixes=("", suffix),
            how='left'
        )
        # Odstraň nedůležité sloupce 'priorita', protože se vzájemně vylučují a nejspíš ani k ničemu nejsou.
        # Tímto se vyhneme varování v 'drop_by_inconsistency'.
        self.tbl['typ_funkce'].drop(columns=["priorita", "priorita__typ_organ"], inplace=True)
        self.tbl['typ_funkce'] = self.drop_by_inconsistency(self.tbl['typ_funkce'], suffix, 0.1, t1_name='typ_funkce', t2_name='typ_organ', t1_on='id_typ_organ', t2_on='id_typ_organ')

        self.nastav_dataframe(
            self.tbl['typ_funkce'],
            vyber=['id_typ_funkce', 'typ_funkce_cz', 'typ_funkce_en', 'typ_funkce_obecny'],
            odstran=['typ_funkce_obecny__ORIG']
        )

        log.debug("<-- TypFunkce")


class Funkce(TabulkaFunkceMixin, Organy, TypFunkce):
    def __init__(self, *args, **kwargs):
        log.debug("--> Funkce")
        super().__init__(*args, **kwargs)

        self.nacti_funkce()

        # Zúžení
        self.vyber_platne_funkce()

        # Připoj Orgány
        suffix = "__organy"
        self.tbl['funkce'] = pd.merge(
            left=self.tbl['funkce'],
            right=self.tbl['organy'],
            on='id_organ',
            suffixes=("", suffix),
            how='left'
        )
        self.tbl['funkce'] =  self.drop_by_inconsistency(self.tbl['funkce'], suffix, 0.1, 'funkce', 'organy')

        # Připoj Typ funkce
        suffix = "__typ_funkce"
        self.tbl['funkce'] = pd.merge(left=self.tbl['funkce'], right=self.tbl['typ_funkce'], on="id_typ_funkce", suffixes=("", suffix), how='left')

        # Fix the knows inconsistency in data
        x = self.tbl['funkce']
        idx = x[(x.id_typ_organ == 42) & (x.id_typ_organ__typ_funkce == 15)].index
        log.debug(f"Řešení známé nekonzistence v datech: Upřednostňuji sloupce z tabulky 'funkce' před 'typ_funkce' pro {len(idx)} hodnot.")
        to_update = ['id_typ_organ', 'typ_id_typ_organ', 'nazev_typ_organ_cz', 'nazev_typ_organ_en', 'typ_organ_obecny']
        for i in to_update:
            x.at[idx, i + '__typ_funkce'] = x.loc[idx][i]

        self.tbl['funkce'] = self.drop_by_inconsistency(self.tbl['funkce'], suffix, 0.1, 'funkce', 'typ_funkce', t1_on='id_typ_funkce', t2_on='id_typ_funkce')

        if self.volebni_obdobi != -1:
            assert len(self.tbl['funkce'][self.tbl['funkce'].id_organ.isna()]) == 0

        self.nastav_dataframe(self.tbl['funkce'])

        log.debug("<-- Funkce")

    def vyber_platne_funkce(self):
        if self.volebni_obdobi != -1:
            self.tbl['funkce'] = self.tbl['funkce'][self.tbl['funkce'].id_organ.isin(self.tbl['organy'].id_organ)]


class Osoby(TabulkaOsobaExtraMixin, TabulkaOsobyMixin, PoslanciOsobyBase):
    def __init__(self, *args, **kwargs):
        log.debug("--> Osoby")
        super(Osoby, self).__init__(*args, **kwargs)

        self.nacti_osoby()
        self.nacti_osoba_extra()

        #suffix='__osoba_extra'
        #self.tbl['osoby'] = pd.merge(left=self.tbl['osoby'], right=self.tbl['osoba_extra'], on="id_osoba", how="left", suffixes=('', suffix))
        #self.drop_by_inconsistency(self.tbl['osoby'], suffix, 0.1, 'hlasovani', 'osoba_extra', inplace=True)

        self.nastav_dataframe(self.tbl['osoby'])

        log.debug("<-- Osoby")


class ZarazeniOsoby(TabulkaZarazeniOsobyMixin, Funkce, Organy, Osoby):
    def __init__(self, *args, **kwargs):
        log.debug("--> ZarazeniOsoby")

        super().__init__(*args, **kwargs)

        self.nacti_zarazeni_osoby()

        # Připoj Osoby
        suffix = "__osoby"
        self.tbl['zarazeni_osoby'] = pd.merge(left=self.tbl['zarazeni_osoby'], right=self.tbl['osoby'], on='id_osoba', suffixes = ("", suffix), how='left')
        self.tbl['zarazeni_osoby'] = self.drop_by_inconsistency(self.tbl['zarazeni_osoby'], suffix, 0.1, 'zarazeni_osoby', 'osoby')

        # Připoj Organy
        suffix = "__organy"
        sub1 = self.tbl['zarazeni_osoby'][self.tbl['zarazeni_osoby'].cl_funkce == 'členství'].reset_index()
        if self.volebni_obdobi == -1:
            m1 = pd.merge(left=sub1, right=self.tbl['organy'], left_on='id_of', right_on='id_organ', suffixes=("", suffix), how='left')
        else:
            # Pozor, how='left' nestačí, 'inner' se podílí na zúžení na danou sněmovnu
            m1 = pd.merge(left=sub1, right=self.tbl['organy'], left_on='id_of', right_on='id_organ', suffixes=("", suffix), how='inner')
        m1 = self.drop_by_inconsistency(m1, suffix, 0.1, 'zarazeni_osoby', 'organy')

        # Připoj Funkce
        sub2 = self.tbl['zarazeni_osoby'][self.tbl['zarazeni_osoby'].cl_funkce == 'funkce'].reset_index()
        if self.volebni_obdobi == -1:
            m2 = pd.merge(left=sub2, right=self.tbl['funkce'], left_on='id_of', right_on='id_funkce', suffixes=("", suffix), how='left')
        else:
            # Pozor, how='left' nestačí, 'inner' se podílí na zúžení na danou sněmovnu
            m2 = pd.merge(left=sub2, right=self.tbl['funkce'], left_on='id_of', right_on='id_funkce', suffixes=("", suffix), how='inner')
        m2 = self.drop_by_inconsistency(m2, suffix, 0.1, 'zarazeni_osoby', 'funkce')

        self.tbl['zarazeni_osoby'] = pd.concat([m1, m2], axis=0, ignore_index=True).set_index('index').sort_index()

        # Zúžení na dané volební období
        self.vyber_platne_zarazeni_osoby()

        self.nastav_dataframe(self.tbl['zarazeni_osoby'])

        log.debug("<-- ZarazeniOsoby")

    def vyber_platne_zarazeni_osoby(self):
        if self.volebni_obdobi != -1:
            interval_start = self.tbl['zarazeni_osoby'].od_o\
                .mask(self.tbl['zarazeni_osoby'].od_o.isna(), self.snemovna.od_organ)\
                .mask(~self.tbl['zarazeni_osoby'].od_o.isna(), np.maximum(self.tbl['zarazeni_osoby'].od_o, self.snemovna.od_organ))

            # Pozorování: volebni_obdobi_od není nikdy NaT => interval_start není nikdy NaT
            if pd.isna(self.snemovna.do_organ): # příznak posledního volebního období
                podminka_interval = (
                    (interval_start.dt.date <= self.tbl['zarazeni_osoby'].do_o.dt.date) # Nutná podmínka pro True: (interval_start != NaT, splněno vždy) a (do_o != NaT)
                    |  (self.tbl['zarazeni_osoby'].do_o.isna()) # Nutná podmínka pro True: (interval_start != NaT, splněno vždy) a (do_o == NaT)
                )
            else: # Pozorování: předchozí volební období => interval_end není nikdy NaT
                interval_end = self.tbl['zarazeni_osoby'].do_o\
                    .mask(self.tbl['zarazeni_osoby'].do_o.isna(), self.snemovna.do_organ)\
                    .mask(~self.tbl['zarazeni_osoby'].do_o.isna(), np.minimum(self.tbl['zarazeni_osoby'].do_o, self.snemovna.do_organ))
                podminka_interval = (interval_start.dt.date <= interval_end.dt.date)

            self.tbl['zarazeni_osoby'] = self.tbl['zarazeni_osoby'][podminka_interval]


class Poslanci(TabulkaPoslanciPkgpsMixin, TabulkaPoslanciMixin, ZarazeniOsoby, Organy):
    def __init__(self, *args, **kwargs):
        log.debug("--> Poslanci")

        super().__init__(*args, **kwargs)

        self.nacti_poslanci_pkgps()
        self.nacti_poslance()

        # Zúžení na dané volební období
        if self.volebni_obdobi != -1:
            self.tbl['poslanci'] = self.tbl['poslanci'][self.tbl['poslanci'].id_organ == self.snemovna.id_organ]

        # Připojení informace o osobě, např. jméno a příjmení
        suffix = "__osoby"
        self.tbl['poslanci'] = pd.merge(left=self.tbl['poslanci'], right=self.tbl['osoby'], on='id_osoba', suffixes = ("", suffix), how='left')
        self.tbl['poslanci'] = self.drop_by_inconsistency(self.tbl['poslanci'], suffix, 0.1, 'poslanci', 'osoby')

        # Připoj informace o kanceláři
        suffix = "__poslanci_pkgps"
        self.tbl['poslanci'] = pd.merge(left=self.tbl['poslanci'], right=self.tbl['poslanci_pkgps'], on='id_poslanec', suffixes = ("", suffix), how='left')
        self.drop_by_inconsistency(self.tbl['poslanci'], suffix, 0.1, 'poslanci', 'poslanci_pkgps', inplace=True)

        # Připoj informace o kandidátce
        suffix = "__organy"
        self.tbl['poslanci'] = pd.merge(left=self.tbl['poslanci'], right=self.tbl['organy'][["id_organ", "nazev_organ_cz", "zkratka"]], left_on='id_kandidatka', right_on='id_organ', suffixes = ("", suffix), how='left')
        self.tbl['poslanci'].drop(columns=['id_organ__organy'], inplace=True)
        self.tbl['poslanci'].rename(columns={'nazev_organ_cz': 'nazev_kandidatka_cz', 'zkratka': 'zkratka_kandidatka'}, inplace=True)
        self.drop_by_inconsistency(self.tbl['poslanci'], suffix, 0.1, 'poslanci', 'organy', t1_on='id_organ', t2_on='id_kandidatka', inplace=True)
        self.meta.nastav_hodnotu('nazev_kandidatka_cz', {"popis": 'Název strany, za kterou poslanec kandidoval, viz Organy:nazev_organ_cz', 'tabulka': 'df', 'vlastni': True})
        self.meta.nastav_hodnotu('zkratka_kandidatka', {"popis": 'Zkratka strany, za kterou poslanec kandidoval, viz Organy:nazev_organ_cz', 'tabulka': 'df', 'vlastni': True})

        # Připoj informace o kraji
        suffix = "__organy"
        self.tbl['poslanci'] = pd.merge(left=self.tbl['poslanci'], right=self.tbl['organy'][["id_organ", "nazev_organ_cz", "zkratka"]], left_on='id_kraj', right_on='id_organ', suffixes = ("", suffix), how='left')
        self.tbl['poslanci'].drop(columns=['id_organ__organy'], inplace=True)
        self.tbl['poslanci'].rename(columns={'nazev_organ_cz': 'nazev_kraj_cz', 'zkratka': 'zkratka_kraj'}, inplace=True)
        self.drop_by_inconsistency(self.tbl['poslanci'], suffix, 0.1, 'poslanci', 'organy', t1_on='id_kraj', t2_on='id_organ', inplace=True)
        self.meta.nastav_hodnotu('nazev_kraj_cz', {"popis": 'Název kraje, za který poslanec kandidoval, viz Organy:nazev_organ_cz', 'tabulka': 'df', 'vlastni': True})
        self.meta.nastav_hodnotu('zkratka_kraj', {"popis": 'Zkratka kraje, za který poslanec kandidoval, viz Organy:nazev_organ_cz', 'tabulka': 'df', 'vlastni': True})

        # Pripoj data nastoupení do parlamentu, příp. odstoupení z parlamentu
        parlament = self.tbl['zarazeni_osoby'][(self.tbl['zarazeni_osoby'].id_osoba.isin(self.tbl['poslanci'].id_osoba)) & (self.tbl['zarazeni_osoby'].nazev_typ_organ_cz == "Parlament") & (self.tbl['zarazeni_osoby'].cl_funkce=='členství')].copy()
        #parlament = parlament.sort_values(['id_osoba', 'od_o']).groupby('id_osoba').tail(1).reset_index()
        parlament = parlament.sort_values(['id_osoba', 'od_o']).groupby('id_osoba').tail(1).reset_index()
        parlament.rename(columns={'id_organ': 'id_parlament', 'od_o': 'od_parlament', 'do_o': 'do_parlament'}, inplace=True)
        self.tbl['poslanci'] = pd.merge(self.tbl['poslanci'], parlament[['id_osoba', 'id_parlament', 'od_parlament', 'do_parlament']], on='id_osoba', how="left")
        self.tbl['poslanci'] = self.drop_by_inconsistency(self.tbl['poslanci'], suffix, 0.1, 'poslanci', 'zarazeni_osoby')
        self.meta.nastav_hodnotu('id_parlament', {"popis": 'Identifikátor parlamentu, jehož byli poslanci členy, viz Organy:id_organ', 'tabulka': 'df', 'vlastni': True})
        self.meta.nastav_hodnotu('od_parlament', {"popis": 'Datum začátku zařazení poslanců do parlamentu, viz Organy:od_o', 'tabulka': 'df', 'vlastni': True})
        self.meta.nastav_hodnotu('do_parlament', {"popis": 'Datum konce zařazení poslanců do parlamentu, viz Organy:do_o', 'tabulka': 'df', 'vlastni': True})

        # Připoj informace o posledním poslaneckém klubu z 'zarazeni_osoby'.
        kluby = self.tbl['zarazeni_osoby'][(self.tbl['zarazeni_osoby'].id_osoba.isin(self.tbl['poslanci'].id_osoba)) & (self.tbl['zarazeni_osoby'].nazev_typ_organ_cz == "Klub") & (self.tbl['zarazeni_osoby'].cl_funkce=='členství')].copy()
        kluby = kluby.sort_values(['id_osoba', 'od_o']).groupby('id_osoba').tail(1).reset_index()
        kluby.rename(columns={'id_organ': 'id_klub', 'nazev_organ_cz': 'nazev_klub_cz', 'zkratka': 'zkratka_klub', 'od_o': 'od_klub', 'do_o': 'do_klub'}, inplace=True)
        self.tbl['poslanci'] = pd.merge(self.tbl['poslanci'], kluby[['id_osoba', 'id_klub', 'nazev_klub_cz', 'zkratka_klub', 'od_klub', 'do_klub']], on='id_osoba', how="left")
        self.tbl['poslanci'] = self.drop_by_inconsistency(self.tbl['poslanci'], suffix, 0.1, 'poslanci', 'zarazeni_osoby')
        self.meta.nastav_hodnotu('id_klub', {"popis": 'Identifikátor posledního klubu, do něhož byli poslanci zařazeni, viz Organy:id_organ', 'tabulka': 'df', 'vlastni': True})
        self.meta.nastav_hodnotu('nazev_klub_cz', {"popis": 'Název posledního klubu, do něhož byli poslanci zařazeni, viz Organy:nazev_organ_cz', 'tabulka': 'df', 'vlastni': True})
        self.meta.nastav_hodnotu('zkratka_klub', {"popis": 'Zkratka posledního klubu, do něhož byli poslanci zařazeni, viz Organy:zkratka', 'tabulka': 'df', 'vlastni': True})
        self.meta.nastav_hodnotu('od_klub', {"popis": 'Datum začátku zařazení poslanců do posledního klubu, viz Organy:od_o', 'tabulka': 'df', 'vlastni': True})
        self.meta.nastav_hodnotu('do_klub', {"popis": 'Datum konce zařazení poslanců do posledního klubu, viz Organy:do_o', 'tabulka': 'df', 'vlastni': True})

        self.nastav_dataframe(
            self.tbl['poslanci'],
            odstran=['pohlavi__ORIG']
        )

        log.debug("<-- Poslanci")

