python:
	find|grep -E ".py$$"|xargs python2 -m py_compile	

cmodules: 
	python2 setup.py build_ext --inplace --force

translations:
	python2 setup.py msgfmt

all:
	python2 setup.py build_ext --inplace --force
	find|grep -E ".py$$"|xargs python2 -m py_compile	


clean:
	find|grep -E ".pyc$$|.pyo$$"|xargs rm

cleanall:
	find|grep -E ".pyc$$|.pyo$$|.so$$|.pyd$$"|xargs rm
