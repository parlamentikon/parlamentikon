Parlamentikon
==============================

Co je Parlamentikon?
--------------------
Parlamentikon je knihovna zpřístupňující vybraná data z Poslanecké sněmovny ČR pomocí pandas tabulek. Součástí projektu jsou jupyter notebooky, které ukazují možné příklady použití.

Výstupy z ukázkových notebooků jsou každodenně aktualizované pomocí Github Actions. Lze si je prohlédnout na webu, případně si je lze pustit v prostředí Google Colab.


Kde si lze prohlédnout ukázkové notebooky?
-------------------------------------------
* Analýza hlasování v Poslanecké sněmovně (poslední volební období):
  - [prohlédni notebook](https://parlamentikon.github.io/parlamentikon/Hlasovani.html)
  - [pusť na Google Colab](https://colab.research.google.com/github/parlamentikon/parlamentikon/blob/main/notebooks/Hlasovani.ipynb) (Vyžaduje přihlášení do účtu Google.)


Jaké jsou prerekvizity pro lokální běh?
-----------------------
Nutné:
- python3.7

Doporučené:
- virtualizace postředí python (virtualenv, conda, ...)


Jak lze Parlamentikon použít?
-----------------------------

1. `git clone https://github.com/parlamentikon/parlamentikon.git`
3. `python3 -m venv my-custom-venv && source my-custom-venv/bin/activate`
 - Použijte vhodnou verzi pythonu (>=3.7)
 - Prostředí <i>my-custom-venv</i> pojmenujte dle svého uvážení.
2. `cd parlamentikon`
4. `pip install -r requirements.txt` - Nainstaluje potřebné závislosti knihovny.
4. `pip install .` - Nainstaluje lokálně knihovnu Parlamentikon.
5. import v kódu (python): 
```
from parlamentikon.PoslanciOsoby import Poslanci
p = Poslanci()
p.head()
```

Která data Parlamentikon zpřístupňuje?
--------------------------------------
* [Poslanci a Osoby](https://www.psp.cz/sqw/hp.sqw?k=1301)
* [Hlasování](https://www.psp.cz/sqw/hp.sqw?k=1302)
* [Schůze](https://www.psp.cz/sqw/hp.sqw?k=1308)
* [Stenozáznamy](https://www.psp.cz/sqw/hp.sqw?k=1310)
* Stenotexty (pomocí scrapingu, zatím ve velmi nedokonalém tvaru)


Testování knihovny
------------------
Pokrytí testy je zatím mizivé. Pro každou skupinu tabulek je možné pustit "integrační" notebooky ze složky tests/notebooks.

1. make test

