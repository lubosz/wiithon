# Makefile funcional, aunque este mal hecho xD

all:
	$(MAKE) -C libwbfs
	gcc -Ilibwbfs -Llibwbfs -lwbfs wiithon_wrapper.c -o build_wiithon_wrapper/wiithon_wrapper

clean:
	$(MAKE) -C libwbfs clean
	$(RM) build_wiithon_wrapper/wiithon_wrapper
