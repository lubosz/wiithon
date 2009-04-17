VERSION=${shell cat VERSION}
REVISION=${shell bzr revno}

all: install

install:
	cp wiithon /usr/bin
	cp wiithon_autodetectar /usr/bin
	cp wbfs /usr/bin
	-@cp wiithon*.schemas /usr/share/gconf/schemas/
	
	chmod +x /usr/bin/wiithon
	chmod +x /usr/bin/wiithon_autodetectar
	chmod +x /usr/bin/wbfs
	
	@echo "Instalado OK, instala manualmente los schemas de nautilus"

uninstall:
	rm /usr/bin/wiithon
	rm /usr/bin/wiithon_autodetectar
	rm /usr/bin/wbfs
	-@rm /usr/share/gconf/schemas/wiithon*.schemas
	@echo "Desinstalado OK, desinstala las acciones de nautilus manualmente"

limpiar:
	-@find -iname "*~" | xargs rm
	-@rm wiithon_v*_r*.tar.gz

limpiar_wbfs:
	cd wbfs_src && make clean && cd ..
	-@find -iname "*.o" | xargs rm

compilar_wbfs:
	cd wbfs_src && make && mv wbfs .. && rm *.o && rm negentig && rm scrub && cd ..

empaquetar: compilar_wbfs limpiar
	tar zcvf wiithon_v${VERSION}_r${REVISION}.tar.gz *

commit:
	bzr commit --file=COMMIT && echo "" > COMMIT
