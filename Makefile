VERSION=${shell cat VERSION.txt}
REVISION=${shell bzr revno}

all: build_wbfs
	@echo ==================================================================
	@echo Escribe "sudo make install" para instalar
	@echo Escribe "sudo make uninstall" para desinstalar
	@echo ==================================================================

install:
	cp wiithon /usr/local/bin
	cp wiithon_autodetectar /usr/local/bin
	cp wiithon_autodetectar_lector /usr/local/bin
	cp wbfs /usr/local/bin

	-cp wiithon*.schemas /usr/share/gconf/schemas/

	chmod +x /usr/local/bin/wiithon
	chmod +x /usr/local/bin/wiithon_autodetectar
	chmod +x /usr/local/bin/wiithon_autodetectar_lector
	chmod +x /usr/local/bin/wbfs

	@echo "=================================================================="	
	@echo "Instalado OK, instala manualmente los acciones de nautilus"
	@echo "=================================================================="

uninstall:
	-rm /usr/bin/wiithon
	-rm /usr/bin/wiithon_autodetectar
	-rm /usr/bin/wiithon_autodetectar_lector
	-rm /usr/bin/wbfs
	
	-rm /usr/local/bin/wiithon
	-rm /usr/local/bin/wiithon_autodetectar
	-rm /usr/local/bin/wiithon_autodetectar_lector
	-rm /usr/local/bin/wbfs
	
	-rm /usr/share/gconf/schemas/wiithon*.schemas
	
	@echo "=================================================================="	
	@echo "Desinstalado OK, desinstala las acciones de nautilus manualmente"
	@echo "=================================================================="	

clean: clean_wbfs
	$(RM) *~

clean_wbfs:
	$(MAKE) -C wbfs_src clean
	
build_wbfs:
	$(MAKE) -C wbfs_src
	cp wbfs_src/wbfs .

empaquetar: build_wbfs clean
	$(RM) wiithon_v*_r*.tar.gz
	tar zcvf wiithon_v${VERSION}_r${REVISION}.tar.gz * --exclude="COMMIT.txt"

commit: clean
	bzr commit --file=COMMIT.txt && echo "" > COMMIT.txt
	bzr log > CHANGELOG.txt

status: clean
	bzr status
