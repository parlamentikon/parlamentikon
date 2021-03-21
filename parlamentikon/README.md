<b>Jmenné konvence:</b>
* tabulky a sloupce tabulek česky dle konvence v zdrojových datech
* proměnné, které se semanticky vztahují k dění v poslanecké sněmovně, česky bez diakritiky nebo anglicky
* ostatní proměnné anglicky
* komentáře a vysvětlení česky s diakritikou
* funkce anglicky

Snemovna(object):

poo PoslanciOsobyObecne(Snemovna):
torg TypOrganu(PoslanciOsobyObecne):
org Organy(TypOrganu):
tfce TypFunkce(TypOrganu):
fce Funkce(Organy, TypFunkce):
os Osoby(PoslanciOsobyObecne):
oszar OsobyZarazeni(Funkce, Organy, Osoby):
pos Poslanci(Osoby, Organy):

hlo HlasovaniObecne(Snemovna):
hl Hlasovani(HlasovaniObecne, Organy):
zmhl ZmatecneHlasovani(Hlasovani):
zphl ZpochybneniHlasovani(Hlasovani):
! zphlpos ZpochybneniHlasovaniPoslancem(ZpochybneniHlasovani, Osoby):
! opos OmluvyPoslance(HlasovaniObecne, Poslanci, Organy):
hlpos HlasovaniPoslance(Hlasovani, Poslanci, Organy):

scho SchuzeObecne(Snemovna):
sch Schuze(SchuzeObecne, Organy):
!sbsch  StavBoduSchuze(SchuzeObecne):
bsch BodSchuze(BodStav):


! stzo StenozaznamyObecne(Snemovna):
! stz Stenozaznamy(StenoObecne, Organy):
! bodstz BodStenozaznamu(Steno, Organy):
! recstz RecnikStenozaznamu(Steno, Osoby, BodSchuze):

stt Stenotexty(StenoRec, OsobyZarazeni):

Meta(object):

