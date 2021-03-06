Parlamentikon
==============================

Co je Parlamentikon?
--------------------
Parlamentikon je knihovna zpřístupňující  vybraná [data agend](https://www.psp.cz/sqw/hp.sqw?k=1300) z Poslanecké sněmovny ČR pomocí pandas tabulek. Cílem je usnadnit načítání dat, a tím umožnit následnou analýzu.

Součástí projektu jsou jupyter notebooky, které ukazují možné příklady použití.

Výstupy z ukázkových notebooků jsou každodenně aktualizované pomocí Github Actions. Lze si je prohlédnout online, případně si lze notebooky pustit v prostředí Google Colab.

Detailnější informace ke knihovně viz. [parlamentikon/README.md](parlamentikon/README.md).


Kde si lze prohlédnout ukázkové notebooky?
-------------------------------------------
* Zastoupení žen v Poslanecké sněmovně ČR: Jak se vyvíjí zastoupení žen napříč různými sněmovnami? Co z toho vyplývá pro budoucnost?
  - [prohlédni notebook](https://parlamentikon.github.io/parlamentikon/Zastoupeni_zen_v_PS.html)
  - <a href="https://colab.research.google.com/github/parlamentikon/parlamentikon/blob/main/notebooks/Zastoupeni_zen_v_PS.ipynb" target="_blank" rel="noopener noreferrer">spusť na GColab</a>
  - [kód](notebooks/Zastoupeni_zen_v_PS.ipynb)
* Podobnost hlasování: Jak se podobá hlasování jednotlivých poslanců a poslankyň? Které strany hlasují podobně?
  - [prohlédni notebook](https://parlamentikon.github.io/parlamentikon/Podobnost_hlasovani.html)
  - <a href="https://colab.research.google.com/github/parlamentikon/parlamentikon/blob/main/notebooks/Podobnost_hlasovani.ipynb" target="_blank" rel="noopener noreferrer">spusť na GColab</a>
  - [kód](notebooks/Podobnost_hlasovani.ipynb)
* Jednomyslnost hlasováni: Při kterých hlasováních byla největší shoda? Při kterých nejmenší?
  - [prohlédni notebook](https://parlamentikon.github.io/parlamentikon/Jednomyslnost_hlasovani.html)
  - <a href="https://colab.research.google.com/github/parlamentikon/parlamentikon/blob/main/notebooks/Jednomyslnost_hlasovani.ipynb" target="_blank" rel="noopener noreferrer">spusť na GColab</a>
  - [kód](notebooks/Jednomyslnost_hlasovani.ipynb)
* Omluvy: Kdo se omlouval ze schůzí PS nejvíce? Kdo nejméně?
  - [prohlédni notebook](https://parlamentikon.github.io/parlamentikon/Omluvy.html)
  - <a href="https://colab.research.google.com/github/parlamentikon/parlamentikon/blob/main/notebooks/Omluvy.ipynb" target="_blank" rel="noopener noreferrer">spusť na GColab</a>
  - [kód](notebooks/Omluvy.ipynb)
* Hlasování: Kdy proběhlo nejvíce hlasování? Jak se v PS hlasuje?
  - [prohlédni notebook](https://parlamentikon.github.io/parlamentikon/Hlasovani.html)
  - <a href="https://colab.research.google.com/github/parlamentikon/parlamentikon/blob/main/notebooks/Hlasovani.ipynb" target="_blank" rel="noopener noreferrer">spusť na GColab</a>
  - [kód](notebooks/Hlasovani.ipynb)




Která data Parlamentikon zpřístupňuje?
--------------------------------------
* [Poslanci a Osoby](https://www.psp.cz/sqw/hp.sqw?k=1301)
* [Hlasování](https://www.psp.cz/sqw/hp.sqw?k=1302)
* [Schůze](https://www.psp.cz/sqw/hp.sqw?k=1308)
* [StenoZáznamy](https://www.psp.cz/sqw/hp.sqw?k=1310)
* [StenoTexty](https://www.psp.cz/eknih/2017ps/stenprot/index.htm): Data se stahují pomocí scrapingu. Zatím ve velmi nedokonalém stavu.


Příklady navazující datové analýzy
-----------------------------------
![Podobnost hlasování dle poslaneckého klubu](docs/img/Podobnost_hlasovani_dle_klubu.png)


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
