
import pandas as pd

from parlamentikon.utility import *
from parlamentikon.Helpers import MItem
from parlamentikon.Snemovna import SnemovnaZipDataMixin, SnemovnaDataFrame
from parlamentikon.PoslanciOsoby import Organy
from parlamentikon.TabulkySchuze import TabulkaSchuzeMixin, TabulkaSchuzeStavMixin, TabulkaBodSchuzeMixin, TabulkaBodStavMixin
from parlamentikon.setup_logger import log


class SchuzeBase(Organy, SnemovnaZipDataMixin, SnemovnaDataFrame):
    def __init__(self, stahni=True, *args, **kwargs):
        log.debug("--> SchuzeBase")
        super().__init__(stahni=stahni, *args, **kwargs)
        if stahni == True:
            self.stahni_zip_data("schuze")
        log.debug("<-- SchuzeBase")


class Schuze(TabulkaSchuzeMixin, TabulkaSchuzeStavMixin, SchuzeBase):
    def __init__(self, *args, **kwargs):
        log.debug('--> Schuze')

        super().__init__(*args, **kwargs)

        self.nacti_schuze()
        self.nacti_schuze_stav()

        # Zúžení na dané volební období
        if ('id_organ' in self.snemovna) and (self.snemovna.id_organ != -1):
            self.tbl['schuze'] = self.tbl['schuze'][self.tbl['schuze'].id_org == self.snemovna.id_organ]

        # Připoj informace o stavu schůze
        suffix = "__schuze_stav"
        self.tbl['schuze'] = pd.merge(left=self.tbl['schuze'], right=self.tbl['schuze_stav'], on='id_schuze', suffixes = ("", suffix), how='left')
        self.drop_by_inconsistency(self.tbl['schuze'], suffix, 0.1, 'schuze', 'schuze_stav', inplace=True)

        self.nastav_dataframe(
            self.tbl['schuze'],
            odstran=['pozvanka__ORIG', 'stav__ORIG', 'typ__ORIG']
        )

        log.debug('<-- Schuze')


class BodSchuze(TabulkaBodSchuzeMixin, TabulkaBodStavMixin, SchuzeBase):
    def __init__(self, *args, **kwargs):
        log.debug('--> BodSchuze')

        super().__init__(*args, **kwargs)

        self.nacti_bod_schuze()
        self.nacti_bod_stav()

        # TODO: Zúžení na dané volební období

        # Připoj informace o stavu bodu
        suffix = "__bod_stav"
        self.tbl['bod_schuze'] = pd.merge(left=self.tbl['bod_schuze'], right=self.tbl['bod_stav'], on='id_bod_stav', suffixes = ("", suffix), how='left')
        self.drop_by_inconsistency(self.tbl['bod_schuze'], suffix, 0.1, 'bod_schuze', 'bod_stav', inplace=True)

        self.nastav_dataframe(self.tbl['bod_schuze'])

        log.debug('<-- BodSchuze')

