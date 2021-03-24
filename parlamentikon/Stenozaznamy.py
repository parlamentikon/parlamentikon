import pandas as pd

from parlamentikon.Snemovna import SnemovnaZipDataMixin, SnemovnaDataFrame
from parlamentikon.PoslanciOsoby import Osoby, Organy
#from parlamentikon.Schuze import *
from parlamentikon.TabulkyStenozaznamy import TabulkaStenoMixin, TabulkaStenoBodMixin, TabulkaStenoRecMixin
from parlamentikon.setup_logger import log

# Stenozáznamy jsou těsnopisecké záznamy jednání Poslanecké sněmovny a jejích orgánů. V novějších volebních období obsahují časový úsek řádově 10 minut (případně mimo doby přerušení a podobně). Jsou číslovány v číselné řadě od začátku schůze.

class StenoBase(Organy, SnemovnaZipDataMixin, SnemovnaDataFrame):
    def __init__(self, stahni=True, *args, **kwargs):
        log.debug("--> StenoBase")
        super().__init__(stahni=stahni, *args, **kwargs)
        if stahni == True:
            self.stahni_zip_data("steno")
        log.debug("<-- StenoBase")

# Tabulka steno
# Obsahuje záznamy o jednotlivých stenozáznamech (turnech). Položky od_t a do_t nemusí ve všech případech obsahovat správná data, zvláště v případech písařských chyb a obvykle se v dohledné době opraví.

class Steno(TabulkaStenoMixin, StenoBase):
    def __init__(self, *args, **kwargs):
        log.debug('--> Steno')

        super().__init__(*args, **kwargs)

        self.nacti_steno()

        if self.volebni_obdobi != -1:
            self.tbl['steno'] = self.tbl['steno'][self.tbl['steno'].id_organ == self.snemovna.id_organ]

        self.nastav_dataframe(self.tbl['steno'])


# Tabulka steno_bod
# Obsahuje záznamy o začátku či pokračování projednávání bodu schůze. Nelze úplně předpokládat, že text stenozáznamu mezi dvěma po sobě následujícími začátky projednávání bodů pořadu schůze budou obsahovat pouze jednání o prvním bodu, tj. projednávání bodu může skončit a poté může následovat procedurální jednání či vystoupení mimo body pořadu schůze.

class StenoBod(TabulkaStenoBodMixin, Steno):
    def __init__(self, *args, **kwargs):
        log.debug('--> StenoBod')

        super().__init__(*args, **kwargs)

        self.nacti_steno_bod()

        # Merge steno
        suffix = "__steno"
        self.tbl['steno_bod'] = pd.merge(left=self.tbl['steno_bod'], right=self.tbl['steno'], on='id_steno', suffixes = ("", suffix), how='left')
        self.drop_by_inconsistency(self.tbl['steno_bod'], suffix, 0.1, "steno_bod", "steno")

        if self.volebni_obdobi != -1:
            self.tbl['steno_bod'] = self.tbl['steno_bod'][self.tbl['steno_bod'].id_organ == self.snemovna.id_organ]

        self.nastav_dataframe(self.tbl['steno_bod'])

        log.debug('<-- StenoBod')


# Tabulka rec
# Obsahuje záznamy o vystoupení řečníka.
# Obvykle se ve vystoupení střídá předsedající a řečník, v některých případech (např. při schvalování pozměňovacích návrhů ve třetím čtení vystupují po předsedajícím zpravodaj a zástupce navrhovatele).
# Zvláštní situace nastává např. v okamžiku střídání předsedajících schůze či pokud po sobě následují vystoupení dvou poslanců, kteří mohou být v daný okamžik předsedajícími schůze (předseda, místopředseda a poslanec určený řízením ustavující schůze do okamžiku zvolení předsedy). V položce druh je pak nastavena role řečníka.
# Pokud je druh == 4, tj. předsedající, nemusí to automaticky znamenat, že v rámci jeho vystoupení se bude jednat pouze o řízení schůze - ačkoliv by řídící schůze se měl vyvarovat projevů jiných než k řízení schůze, může se stát, že pokud to nikdo nerozporuje, může vystoupit i s jiným projevem (např. za situace, kdy není k dispozici žádný místopředseda či předseda PS, který by za něj převzal řízení schůze).
# Záznamy v druh typu ověřeno jsou zkontrolovány na základě automatického vyhledání záznamů o vystoupení, které neodpovídají jejich obvyklému řazení.


class Stenorec(TabulkaStenoRecMixin, Steno, Osoby):

    def __init__(self, *args, **kwargs):
        log.debug('--> Stenorec')

        super(Stenorec, self).__init__(*args, **kwargs)

        self.nacti_steno_recniky()

        # Merge steno
        suffix = "__steno"
        self.tbl['steno_rec'] = pd.merge(left=self.tbl['steno_rec'], right=self.tbl['steno'], on='id_steno', suffixes = ("", suffix), how='left')
        self.drop_by_inconsistency(self.tbl['steno_rec'], suffix, 0.1, "steno_rec", "steno", inplace=True)

        if self.volebni_obdobi != -1:
            self.tbl['steno_rec'] = self.tbl['steno_rec'][self.tbl['steno_rec'].id_organ == self.snemovna.id_organ]

        # Merge osoby
        suffix = "__osoby"
        self.tbl['steno_rec'] = pd.merge(left=self.tbl['steno_rec'], right=self.tbl['osoby'], on='id_osoba', suffixes = ("", suffix), how='left')
        self.drop_by_inconsistency(self.tbl['steno_rec'], suffix, 0.1, 'steno_rec', 'osoby', inplace=True)

        # Merge bod schuze
        #suffix = "__bod_schuze"
        #self.steno_rec = pd.merge(left=self.steno_rec, right=self.bod_schuze, on='id_bod', suffixes = ("", suffix), how='left')
        #self.steno_rec = self.drop_by_inconsistency(self.steno_rec, suffix, 0.1, 'steno_rec', 'bod_schuze')

        self.nastav_dataframe(self.tbl['steno_rec'])

        log.debug('<-- Stenorec')

