VERSION=0.95
RELEASE=1

all: compilar

compilar:
	cd wbfs_src/ && make && cd ..

install:
	cp wiithon /usr/bin
	cp wiithon_autodetectar /usr/bin
	cp -L wbfs /usr/bin
	cp wiithon1.schemas /usr/share/gconf/schemas/
	cp wiithon2.schemas /usr/share/gconf/schemas/
	cp wiithon3.schemas /usr/share/gconf/schemas/
	gconf-schemas --register wiithon1.schemas wiithon2.schemas wiithon3.schemas
	@echo "Instalado OK, instala manualmente los schemas de nautilus"

uninstall:
	rm /usr/bin/wiithon
	rm /usr/bin/wiithon_autodetectar
	rm /usr/bin/wbfs
	gconf-schemas --unregister wiithon1.schemas wiithon2.schemas wiithon3.schemas
	rm /usr/share/gconf/schemas/wiithon1.schemas
	rm /usr/share/gconf/schemas/wiithon2.schemas
	rm /usr/share/gconf/schemas/wiithon3.schemas
	@echo "Desinstalado OK, desinstala las acciones de nautilus manualmente"

clean:
	cd wbfs_src/ && make clean && cd ..
	-rm *~

empaquetar: clean
	tar zcvf wiithon_${VERSION}_r${RELEASE}.tar.gz *
