all: test test_nb

.PHONY: test test%

test:
	python -m unittest discover -s tests

TEST_NB_DIR = tests/notebooks

test_nb: test_nb_hlasovani test_nb_poslanci_osoby test_nb_schuze test_nb_stenozaznamy test_nb_stenotexty

test_nb_poslanci_osoby:
	cd $(TEST_NB_DIR) && jupyter nbconvert --to notebook --execute "PoslanciOsoby - popis.ipynb" --stdout 1>/dev/null

test_nb_hlasovani:
	cd $(TEST_NB_DIR) && jupyter nbconvert --to notebook --execute "Hlasovani - popis.ipynb" --stdout 1>/dev/null

test_nb_schuze:
	cd $(TEST_NB_DIR) && jupyter nbconvert --to notebook --execute Schuze\ -\ popis.ipynb --stdout 1>/dev/null

test_nb_stenozaznamy:
	cd $(TEST_NB_DIR) && jupyter nbconvert --to notebook --execute Stenozaznamy\ -\ popis.ipynb --stdout 1>/dev/null

test_nb_stenotexty:
	cd $(TEST_NB_DIR) && jupyter nbconvert --to notebook --execute Stenotexty\ -\ popis.ipynb --stdout 1>/dev/null

