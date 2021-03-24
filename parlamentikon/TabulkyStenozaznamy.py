from parlamentikon.Snemovna import *
from parlamentikon.PoslanciOsoby import *
from parlamentikon.Schuze import *

from parlamentikon.setup_logger import log

class TabulkaStenoMixin(object):
    def nacti_steno(self):
        path = f"{self.parameters['data_dir']}/steno.unl"
        self.paths['steno'] = path
        header = {
            'id_steno': MItem('Int64', 'Identifikátor stenozáznamu'),
            'id_organ': MItem('Int64', 'Identifikátor orgánu stenozáznamu (v případě PS je to volební období), viz Organy:id_organ.'),
            'schuze': MItem('Int64', 'Číslo schůze.'),
            'turn': MItem('Int64', 'Číslo stenozáznamu (turn). Pokud číselná řada je neúplná, tj. obsahuje mezery, pak chybějící obsahují záznam z neveřejného jednání. V novějších volebních období se i v těchto případech "stenozáznamy" vytvářejí, ale obsahují pouze informaci o neveřejném jednání.'),
            'od_steno': MItem('string', 'Datum začátku stenozáznamu.'),
            'jd': MItem('Int64', 'Číslo jednacího dne v rámci schůze (používá se např. při konstrukci URL na index stenozáznamu dle dnů).'),
            'od_t': MItem('Int64', 'Čas začátku stenozáznamu v minutách od začátku kalendářního dne; pokud je null či menší než nula, není známo. Tj. převod na čas typu H:M je pomocí H = div(od_t, 60), M = mod(od_t, 60).'),
            'do_t': MItem('Int64', 'Čas konce stenozáznamu v minutách od začátku kalendářního dne; pokud je null či menší než nula, není známo. V některých případech může být od_t == do_t; v některých případech může být i od_t > do_t -- platné pouze v případě, že během stena dojde k změně kalendářního dne (například 23:50 - 00:00).'),
        }

        _df = pd.read_csv(path, sep="|", names = header,  index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, 'steno')
        self.rozsir_meta(header, tabulka='steno', vlastni=False)

        # TODO: zkombinul od_steno a od_t !!!
        # Přidej sloupec 'od_schuze' typu datetime
        df['od_steno'] = pd.to_datetime(df['od_steno'], format='%Y-%m-%d')
        df['od_steno'] = df['od_steno'].dt.tz_localize(self.tzn)

        self.tbl['steno'], self.tbl['_steno'] = df, _df


class TabulkaStenoBodMixin(object):
    def nacti_steno_bod(self):
        path = f"{self.parameters['data_dir']}/steno_bod.unl"
        self.paths['steno_bod'] = path
        header = {
                'id_steno': MItem('Int64', 'Identifikátor stenozáznamu, viz steno:id_steno.'),
                'aname': MItem('Int64', 'Pozice v indexu jednacího dne.'),
                'id_bod': MItem('Int64', 'Identifikace bodu pořadu schůze, viz bod_schuze:id_bod. Je-li null či 0, pak pro daný úsek stenozáznamů není známo číslo bodu (např. každé přerušení schůze znamená při automatickém zpracování neznámé číslo bodu).')
        }

        _df = pd.read_csv(path, sep="|", names = header,  index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, 'steno_bod')
        self.rozsir_meta(header, tabulka='steno_bod', vlastni=False)

        self.tbl['steno_bod'], self.tbl['_steno_bod'] = df, _df


class TabulkaStenoRecMixin(object):
    def nacti_steno_recniky(self):
        path = f"{self.parameters['data_dir']}/rec.unl"
        self.paths['steno_rec'] = path
        header = {
                'id_steno': MItem('Int64', 'Identifikátor stenozáznamu, viz Steno:id_steno.'),
                'id_osoba': MItem('Int64', 'Identifikátor osoby, viz Osoby:id_osoba.'),
                'aname': MItem('Int64', 'Identifikace vystoupení v rámci stenozáznamu.'),
                'id_bod': MItem('Int64', 'Identifikace bodu pořadu schůze, viz bod_schuze:id_bod. Je-li null či 0, pak pro daný úsek stenozáznamů není známo číslo bodu (např. každé přerušení schůze znamená při automatickém zpracování neznámé číslo bodu).'),
                'druh__ORIG': MItem('Int64', 'Druh vystoupení řečníka: 0 či null - neznámo, 1 - nezpracováno, 2 - předsedající (ověřeno), 3 - řečník (ověřeno), 4 - předsedající, 5 - řečník.'),
        }

        _df = pd.read_csv(path, sep="|", names = header,  index_col=False, encoding='cp1250')
        df = pretypuj(_df, header, 'steno_rec')
        self.rozsir_meta(header, tabulka='steno_rec', vlastni=False)

        mask = { None: 'neznámo', 0: 'neznámo', 1: 'nezpracováno', 2: 'předsedající (ověřeno)',
            3: 'řečník (ověřeno)', 4: 'předsedající', 5: 'řečník' }
        df['druh'] = mask_by_values(df.druh__ORIG, mask).astype('string')
        self.meta.nastav_hodnotu('druh', dict(popis='Druh vystoupení řečníka.', tabulka='steno_rec', vlastni=True))

        self.tbl['steno_rec'], self.tbl['_steno_rec'] = df, _df


