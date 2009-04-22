PREFIX=/usr/local

VERSION=${shell cat VERSION.txt}
REVISION=${shell bzr revno}

all: wbfs
	@echo ==================================================================
	@echo Escribe "sudo make install" para instalar
	@echo Escribe "sudo make uninstall" para desinstalar
	@echo ==================================================================

install:
	cp wiithon $(PREFIX)/bin
	cp wiithon_autodetectar $(PREFIX)/bin
	cp wiithon_autodetectar_lector $(PREFIX)/bin
	cp wbfs $(PREFIX)/bin

	-cp wiithon*.schemas $(PREFIX)/share/gconf/schemas/

	chmod 755 $(PREFIX)/bin/wiithon
	chmod 755 $(PREFIX)/bin/wiithon_autodetectar
	chmod 755 $(PREFIX)/bin/wiithon_autodetectar_lector
	chmod 755 $(PREFIX)/bin/wbfs
	
	-chmod 644 /usr/share/gconf/schemas/wiithon*.schemas

	@echo "=================================================================="
	@echo "Instalado OK, instala manualmente los acciones de nautilus"
	@echo "=================================================================="

uninstall:
	-rm /usr/bin/wiithon
	-rm /usr/bin/wiithon_autodetectar
	-rm /usr/bin/wiithon_autodetectar_lector
	-rm /usr/bin/wbfs

	-rm $(PREFIX)/bin/wiithon
	-rm $(PREFIX)/bin/wiithon_autodetectar
	-rm $(PREFIX)/bin/wiithon_autodetectar_lector
	-rm $(PREFIX)/bin/wbfs

	-rm /usr/share/gconf/schemas/wiithon*.schemas

	@echo "=================================================================="
	@echo "Desinstalado OK, desinstala las acciones de nautilus manualmente"
	@echo "=================================================================="

clean: clean_wbfs
	$(RM) *~

clean_wbfs:
	$(MAKE) -C wbfs_src clean
	-rm wbfs

wbfs: /usr/include/openssl/aes.h /usr/include/openssl/md5.h /usr/include/openssl/sha.h
	$(MAKE) -C wbfs_src
	cp wbfs_src/wbfs .

/usr/include/openssl/*.h:
	@echo "You should install \"libssl-dev\" to be able to compile wbfs"
	# FIXME: return por decir algo, pero no está bien
	@return

empaquetar: wbfs clean
	$(RM) wiithon_v*_r*.tar.gz
	tar zcvf wiithon_v${VERSION}_r${REVISION}.tar.gz * --exclude="COMMIT.txt"

commit: clean
	bzr commit --file=COMMIT.txt && echo "" > COMMIT.txt
	bzr log > CHANGELOG.txt
