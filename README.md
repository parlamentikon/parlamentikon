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
  - [pusť na Google Colab](https://colab.research.google.com/github/parlamentikon/parlamentikon/blob/main/notebooks/Hlasovani.ipynb)


Jaké jsou prerekvizity pro lokální běh?
-----------------------
Nutné:
- python3

Doporučené:
- virtualizace postředí (virtualenv, conda, ...)


Jak lze Parlamentikon použít?
-----------------------------

1. `git clone https://github.com/parlamentikon/parlamentikon.git`
2. `cd parlamentikon`
3. `python3 -m venv my-custom-venv && source my-custom-venv/bin/activate && pip install wheel && pip install jupyter &&  pip install -r requirements.txt`
4. `python setup .`
5. import v kódu (python): `from parlamentikon.PoslanciOsoby import Poslanci`, etc.


Která data Parlamentikon zpřístupňuje?
--------------------------------------
* Poslanci a Osoby
* Hlasování
* Schůze
* Stenozáznamy
* Stenotexty (ve velmi nedokonalém tvaru)


Testování knihovny
------------------
Pokrytí testy je zatím mizivé. Pro každou skupinu tabulek je možné pustit "integrační" notebooky ze složky tests/notebooks.

1. make test

