Parlamentikon - informace o knihovně
=====================================


Co je knihovna Parlamentikon?
-----------------------------
Knihovna Parlamentikon zpřístupňuje vybraná [data agend](https://www.psp.cz/sqw/hp.sqw?k=1300) z Poslanecké sněmovny ČR pomocí pandas tabulek. Cílem je usnadnit načítání dat, a tím umožnit následnou analýzu.


Prerekvizity pro lokální běh
----------------------------------------
Nutné:
- python3.7 (testováno pro tuto verzi pythonu)

Doporučené:
- virtualizace postředí python (virtualenv, conda, ...)


Instalace
----------

1. `git clone https://github.com/parlamentikon/parlamentikon.git`
3. `python3 -m venv my-custom-venv && source my-custom-venv/bin/activate`
 - Použijte vhodnou verzi pythonu (>=3.7)
 - Prostředí <i>my-custom-venv</i> pojmenujte dle svého uvážení.
2. `cd parlamentikon`
4. `pip install -r requirements.txt` - Nainstaluje potřebné závislosti knihovny.
4. `pip install .` - Nainstaluje lokálně knihovnu Parlamentikon.


Použítí
--------
```python
from parlamentikon.PoslanciOsoby import Poslanci # Importuje třídu
p = Poslanci() # Automaticky stáhne data ze stránek PS ČR a sestaví výslednou pandas tabulku
p.head() # Zobrazí data
```

Struktura souborů
----------------------
- Hlasovani.py
  - Obsahuje třídy zpřístupňující tabulky z [agendy Hlasování](https://www.psp.cz/sqw/hp.sqw?k=1302).
- TabulkyHlasovani.py
  - Obsahuje mixins pro stahování a načítání tabulek z [agendy Hlasování](https://www.psp.cz/sqw/hp.sqw?k=1302).
- ...
- Tabulky<i>NazevAgendy</i>
- <i>NazevAgendy</i>

Struktura tříd
------------------
Třídy zpřístupňující tabulky (např. třídy Poslanci nebo ZmatecneHlasovani) vznikly děděním z pandas tabulky (subclassed pandas dataframe).

Kromě samotných dat obsahují některé speciální atributy a metody (tbl, meta, paths, popis), které by měly ulehčit používání a porozumění datům. Viz příklad pro tabulku Poslanci.

```python
p = Poslanci()
p.tbl # Všechny tabulky, z kterých byla tabulka Poslanci vytvořena
p.paths # Všechny lokální cesty, ze kterých byla načtena data do tabulek p.tbl
p.meta # Informace k sloupcům použitým v tabulce Poslanci
p.popis() # Vypíše informace ke všem sloupcům, které by bylo možné v tabulce Poslanci použít 
```

Jmenné konvence
----------------
Pokoušeli jsme se zachovat jmenné konvence [zdrojových dat](https://www.psp.cz/sqw/hp.sqw?k=1300). Z hlediska konzistence pojmenovávání se nejedná pokaždé o optimální možnost. Výhodou zvoleného přístupu je snadnější srovnání s originálem.

- Tabulky a sloupce tabulek jsou česky dle konvence v zdrojových datech. Jen výjimečně upravujeme pád nebo číslo (ze singuláru do plurálu atp.).
- Proměnné a funkce, které se semanticky vztahují k dění v poslanecké sněmovně, jsou česky bez diakritiky.
- Ostatní proměnné a funkce jsou anglicky.
- Komentáře a vysvětlení v kódu a atributu meta jsou česky s diakritikou.

Testování knihovny
------------------
Pokrytí testy je mizivé. Pro každou skupinu tabulek je možné pustit "integrační" notebooky ze složky tests/notebooks.

1. make test_nb

TODO
------
- třída Stenotexty
  - stahování [komprimovaných dat](https://www.psp.cz/eknih/2017ps/stenprot/zip/)
  - přidat časový parametr (od, do) a umožnit inkrementální stahování a zpracování dat
- testy
