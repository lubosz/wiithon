VERSION=${shell cat VERSION}
REVISION=${shell bzr revno}

all: install

install:
	cp wiithon /usr/bin
	cp wiithon_autodetectar /usr/bin
	cp -L wbfs /usr/bin
	-@cp wiithon*.schemas /usr/share/gconf/schemas/
	@echo "Instalado OK, instala manualmente los schemas de nautilus"

uninstall:
	rm /usr/bin/wiithon
	rm /usr/bin/wiithon_autodetectar
	rm /usr/bin/wbfs
	-@rm /usr/share/gconf/schemas/wiithon*.schemas
	@echo "Desinstalado OK, desinstala las acciones de nautilus manualmente"

limpiar:
	-@find -iname "*~" | xargs rm
	-@rm wiithon_v${VERSION}_r${REVISION}.tar.gz

limpiar_wbfs:
	cd wbfs_src && make clean && cd ..
	-@find -iname "*.o" | xargs rm

compilar_wbfs:
	cd wbfs_src && make && cd ..


empaquetar: compilar_wbfs limpiar
	tar zcvf wiithon_v${VERSION}_r${REVISION}.tar.gz *

