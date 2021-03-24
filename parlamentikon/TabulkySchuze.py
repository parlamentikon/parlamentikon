
import pandas as pd

from parlamentikon.utility import pretypuj, mask_by_values, format_to_datetime_and_report_skips
from parlamentikon.Helpers import MItem

#from parlamentikon.Snemovna import *
#from parlamentikon.PoslanciOsoby import *

from parlamentikon.setup_logger import log

# Informace k tabulkám, viz. https://www.psp.cz/sqw/hp.sqw?k=1308

class TabulkaSchuzeMixin(object):
    def nacti_schuze(self):
        # Obsahuje záznamy o schůzích.
        # Pro každou schůzi jsou v tabulce nejvýše dva záznamy, jeden vztahující se k návrhu pořadu, druhý ke schválenému pořadu.
        # I v případě neschválení pořadu schůze jsou dva záznamy, viz schuze:pozvanka a schuze_stav:stav.
        path = f"{self.parameters['data_dir']}/schuze.unl"
        self.paths['schuze'] = path
        header = {
          'id_schuze': MItem('Int64', 'Identifikátor schůze, není to primární klíč, je nutno používat i položku schuze:pozvanka. Záznamy schůzí stejného orgánu a stejného čísla (tj. schuze:id_org a schuze:schuze), mají stejné schuze:id_schuze a liší se pouze v schuze:pozvanka.'),
          'id_org': MItem('Int64', 'Identifikátor orgánu, viz Organy:id_org.'),
          'schuze': MItem('Int64', 'Číslo schůze.'),
          'od_schuze': MItem('string', 'Předpokládaný začátek schůze; viz též tabulka schuze_stav'),
          'do_schuze': MItem('string', 'Konec schůze. V případě schuze:pozvanka == 1 se nevyplňuje.'),
          'aktualizace': MItem('string', 'Datum a čas poslední aktualizace.'),
          'pozvanka__ORIG': MItem('Int64', 'Druh záznamu: null - schválený pořad, 1 - navržený pořad.')
        }

        _df = pd.read_csv(path, sep="|", names = header,  index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, 'schuze')
        self.rozsir_meta(header, tabulka='schuze', vlastni=False)

        # Oprava známých chybných hodnot (očividných překlepů)
        #df.at[768, 'od_schuze'] = "2020-05-31 09:00"

        # Přidej sloupec 'od_schuze' typu datetime
        df['od_schuze'] = format_to_datetime_and_report_skips(df, 'od_schuze', to_format='%Y-%m-%d %H:%M')
        df['od_schuze'] = df['od_schuze'].dt.tz_localize(self.tzn)


        # Přidej sloupec 'do_schuze' typu datetime
        df['do_schuze'] = format_to_datetime_and_report_skips(df, 'do_schuze', to_format='%Y-%m-%d %H:%M')
        df['do_schuze'] = df['do_schuze'].dt.tz_localize(self.tzn)

        mask = {None: 'schválený pořad', 1: 'navržený pořad'}
        df['pozvanka'] = mask_by_values(df.pozvanka__ORIG, mask).astype('string')
        self.meta.nastav_hodnotu('pozvanka', dict(popis='Druh záznamu: [schválený pořad; navržený pořad].', tabulka='schuze', vlastni=True))

        self.tbl['schuze'], self.tbl['_schuze'] = df, _df

class TabulkaSchuzeStavMixin(object):
   def nacti_schuze_stav(self):
        path = f"{self.parameters['data_dir']}/schuze_stav.unl"
        self.paths['schuze_stav'] = path
        header = {
            'id_schuze': MItem('Int64', 'Identifikátor schůze, viz Schuze:id_schuze.'),
            'stav__ORIG': MItem('Int64', 'Stav schůze: 1 - OK, 2 - pořad schůze nebyl schválen a schůze byla ukončena.'),
            'typ__ORIG': MItem('Int64', 'Typ schůze: 1 - řádná, 2 - mimořádná (navržená skupinou poslanců). Dle jednacího řádu nelze měnit navržený pořad mimořádné schůze.'),
            'text_dt': MItem('string', 'Zvláštní určení začátku schůze: pokud je vyplněno, použije se namísto Schuze:od_schuze.'),
            'text_st': MItem('string', 'Text stavu schůze, obvykle informace o přerušení.'),
            'tm_line': MItem('string', 'Podobné jako SchuzeStav:text_st, pouze psáno na začátku s velkým písmenem a ukončeno tečkou.')
        }

        _df = pd.read_csv(path, sep="|", names = header,  index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, 'schuze_stav')
        self.rozsir_meta(header, tabulka='schuze_stav', vlastni=False)

        mask = {1:"OK", 2:"pořad neschválen, schůze ukončena"}
        df['stav'] = mask_by_values(df.stav__ORIG, mask).astype('string')
        self.meta.nastav_hodnotu('stav', dict(popis='Stav schůze: [OK; pořad schůze nebyl schválen a schůze byla ukončena].', tabulka='schuze_stav', vlastni=True))

        mask = {1: "řádná", 2: "mimořádná"}
        df['typ'] = mask_by_values(df.typ__ORIG, mask).astype('string')
        self.meta.nastav_hodnotu('typ', dict(popis='Typ schůze. Typ schůze: [řádná; mimořádná (navržená skupinou poslanců)]. Dle jednacího řádu nelze měnit navržený pořad mimořádné schůze.', tabulka='schuze_stav', vlastni=True))

        self.tbl['schuze_stav'], self.tbl['_schuze_stav'] = df, _df


class TabulkaBodStavMixin(object):
    def nacti_bod_stav(self):
        path = f"{self.parameters['data_dir']}/bod_stav.unl"
        self.paths['bod_stav'] = path
        header = {
            'id_bod_stav': MItem('Int64', 'Typ stavu bodu schůze: typ 3 - neprojednatelný znamená vyřazen z pořadu či neprojednatelný z důvodu legislativního procesu.'),
            'popis': MItem('string', 'Popis stavu bodu.')
        }

        _df = pd.read_csv(path, sep="|", names = header,  index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, 'bod_stav')
        self.rozsir_meta(header, tabulka='bod_stav', vlastni=False)

        df['id_bod_stav__KAT'] = df.id_bod_stav.astype(str).mask(df.id_bod_stav == 3, 'neprojednatelný')
        self.meta.nastav_hodnotu('id_bod_stav__KAT', dict(popis='Typ stavu bodu schůze.', tabulka='bod_stav', vlastni=True))

        self.tbl['bod_stav'], self.tbl['_bod_stav'] = df, _df


# Obsahuje záznamy o bodech pořadu schůze. Body typu odpověď na písemnou interpelaci (bod_schuze:id_typ == 6) se obvykle nezobrazují, viz dále.
#Při zobrazení bodu se použijí položky bod_schuze:uplny_naz. Pokud je bod_schuze:id_tisk nebo bod_schuze:id_sd vyplněno, pak se dále použije bod_schuze:uplny_kon, případně text závislý na bod_schuze.id_typ. Poté následuje bod_schuze:poznamka.
class TabulkaBodSchuzeMixin(object):
    def nacti_bod_schuze(self):
        path = f"{self.parameters['data_dir']}/bod_schuze.unl"
        self.paths['bod_schuze'] = path
        header = {
            'id_bod': MItem('Int64', 'Identifikátor bodu pořadu schůze, není to primární klíč, je nutno používat i položku bod_schuze:pozvanka. Záznamy se stejným id_bod odkazují na stejný bod, i když číslo bodu může být rozdílné (během schvalování pořadu schůze se pořadí bodů může změnit).'),
            'id_schuze': MItem('Int64', 'Identifikátor schůze, viz Schuze:id_schuze a též schuze:pozvanka.'),
            'id_tisk': MItem('Int64', 'Identifikátor tisku, pokud se bod k němu vztahuje. V tomto případě lze využít bod_schuze:uplny_kon.'),
            'id_typ': MItem('Int64', 'Typ bodu, resp. typ projednávání. Kromě bod_schuze:id_typ == 6, se jedná o typ stavu, viz stavy:id_typ a tabulka níže. Je-li bod_schuze:id_typ == 6, jedná se o jednotlivou odpověď na písemnou interpelaci a tento záznam se obykle nezobrazuje (navíc má stejné id_bodu jako bod odpovědi na písemné interpelace a může mít různé číslo bodu).'),
            'bod': MItem('Int64', 'Číslo bodu. Pokud je menší než jedna, pak se při výpisu číslo bodu nezobrazuje.'),
            'uplny_naz': MItem('string', 'Úplný název bodu.'),
            'uplny_kon': MItem('string', 'Koncovka názvu bodu s identifikací čísla tisku nebo čísla sněmovního dokumentu, pokud jsou používány, viz BodSchuze:id_tisk a BodSchuze:id_sd.'),
            'poznamka': MItem('string', 'Poznámka k bodu - obvykle obsahuje informaci o pevném zařazení bodu.'),
            'id_bod_stav': MItem('Int64', 'Stav bodu pořadu, viz BodStav:id_bod_stav. U bodů návrhu pořadu se nepoužije.'),
            'pozvanka': MItem('Int64', 'Rozlišení záznamu, viz Schuze:pozvanka'),
            'rj':  MItem('Int64', 'Režim dle par. 90, odst. 2 jednacího řádu.'),
            'pozn2': MItem('string', 'Poznámka k bodu, zkrácený zápis'),
            'druh_bodu': MItem('Int64', 'Druh bodu: 0 nebo null: normální, 1: odpovědi na ústní interpelace, 2: odpovědi na písemné interpelace, 3: volební bod'),
            'id_sd': MItem('Int64', 'Identifikátor sněmovního dokumentu, viz sd_dokument:id_dokument. Pokud není null, při výpisu se zobrazuje BodSchuze:uplny_kon.'),
            'zkratka': MItem('string', 'Zkrácený název bodu, neoficiální.')
        }

        _df = pd.read_csv(path, sep="|", names = header,  index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, 'bod_schuze')
        self.rozsir_meta(header, tabulka='bod_schuze', vlastni=False)

        self.tbl['bod_schuze'], self.tbl['_bod_schuze'] = df, _df

