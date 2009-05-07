PREFIX=/usr/local

VERSION=${shell cat VERSION.txt}
REVISION=${shell bzr revno}

all: wbfs
	@echo ==================================================================
	@echo Escribe "sudo make install" para instalar
	@echo Escribe "sudo make uninstall" para desinstalar
	@echo ==================================================================

install: wbfs uninstall

	@echo "=================================================================="
	@echo "Antes de instalar, se ha desinstalado"
	@echo "=================================================================="

	mkdir -p $(PREFIX)/share/wiithon
	mkdir -p $(PREFIX)/share/wiithon/recursos/glade
	mkdir -p $(PREFIX)/share/wiithon/recursos/imagenes
	mkdir -p /usr/share/gconf/schemas/

	cp wiithon.py $(PREFIX)/share/wiithon
	cp wiithon_autodetectar.sh $(PREFIX)/share/wiithon
	cp wiithon_autodetectar_lector.sh $(PREFIX)/share/wiithon
	cp wbfs $(PREFIX)/share/wiithon
	cp gui.py $(PREFIX)/share/wiithon
	cp glade_wrapper.py $(PREFIX)/share/wiithon
	cp util.py $(PREFIX)/share/wiithon
	cp core.py $(PREFIX)/share/wiithon
	cp config.py $(PREFIX)/share/wiithon

	cp recursos/glade/*.glade $(PREFIX)/share/wiithon/recursos/glade
	cp recursos/imagenes/*.png $(PREFIX)/share/wiithon/recursos/imagenes

	chmod 755 $(PREFIX)/share/wiithon/wiithon.py
	chmod 755 $(PREFIX)/share/wiithon/wiithon_autodetectar.sh
	chmod 755 $(PREFIX)/share/wiithon/wiithon_autodetectar_lector.sh
	chmod 755 $(PREFIX)/share/wiithon/wbfs
	chmod 755 $(PREFIX)/share/wiithon/gui.py
	chmod 755 $(PREFIX)/share/wiithon/glade_wrapper.py
	chmod 755 $(PREFIX)/share/wiithon/util.py
	chmod 755 $(PREFIX)/share/wiithon/core.py
	chmod 755 $(PREFIX)/share/wiithon/config.py

	chmod 644 $(PREFIX)/share/wiithon/recursos/glade/*.glade
	chmod 644 $(PREFIX)/share/wiithon/recursos/imagenes/*.png
	
	ln -s $(PREFIX)/share/wiithon/wiithon.py $(PREFIX)/bin/wiithon

	@echo "=================================================================="
	@echo "Instalado OK, instala manualmente los acciones de nautilus"
	@echo "=================================================================="

uninstall:
	# Limpiando antiguas instalaciones
	-$(RM) /usr/bin/wiithon
	-$(RM) /usr/bin/wiithon_autodetectar
	-$(RM) /usr/bin/wiithon_autodetectar_lector
	-$(RM) /usr/bin/wbfs

	-$(RM) $(PREFIX)/bin/wiithon_autodetectar
	-$(RM) $(PREFIX)/bin/wiithon_autodetectar_lector
	-$(RM) $(PREFIX)/bin/wbfs

	# viejo acuerdo
	-$(RM) ~/.wiithon_acuerdo

	# Fue cambiado de nombre en el pasado
	-$(RM) $(PREFIX)/share/wiithon/wiithon_autodetectar
	-$(RM) $(PREFIX)/share/wiithon/wiithon_autodetectar_lector

	-$(RM) /usr/share/gconf/schemas/wiithon*.schemas
	-rmdir /usr/share/gconf/schemas/
	
	# Desinstalando la actual versión
	
	-$(RM) $(PREFIX)/bin/wiithon
	-$(RM) $(PREFIX)/share/wiithon/wiithon
	-$(RM) $(PREFIX)/share/wiithon/wiithon_autodetectar.sh
	-$(RM) $(PREFIX)/share/wiithon/wiithon_autodetectar_lector.sh
	-$(RM) $(PREFIX)/share/wiithon/wbfs
	-$(RM) $(PREFIX)/share/wiithon/wiithon.py	
	-$(RM) $(PREFIX)/share/wiithon/util.py	
	-$(RM) $(PREFIX)/share/wiithon/gui.py	
	-$(RM) $(PREFIX)/share/wiithon/glade_wrapper.py	
	-$(RM) $(PREFIX)/share/wiithon/core.py	
	-$(RM) $(PREFIX)/share/wiithon/config.py
	-$(RM) $(PREFIX)/share/wiithon/recursos/glade/*.glade
	-$(RM) $(PREFIX)/share/wiithon/recursos/imagenes/*.png
	
	-rmdir $(PREFIX)/share/wiithon/recursos/glade
	-rmdir $(PREFIX)/share/wiithon/recursos/imagenes
	-rmdir $(PREFIX)/share/wiithon/recursos
	-rmdir $(PREFIX)/share/wiithon

	@echo "=================================================================="
	@echo "Desinstalado OK, desinstala las acciones de nautilus manualmente"
	@echo "=================================================================="

clean: clean_wbfs
	$(RM) *~

clean_wbfs:
	$(MAKE) -C wbfs_src clean
	-$(RM) wbfs

wbfs: /usr/include/openssl/aes.h /usr/include/openssl/md5.h /usr/include/openssl/sha.h
	$(MAKE) -C wbfs_src
	cp wbfs_src/wbfs .

/usr/include/openssl/*.h:
	@echo "You should install \"libssl-dev\" to be able to compile wbfs"
	# FIXME: return por decir algo, pero no está bien
	@return

empaquetar: wbfs clean
	$(RM) wiithon_v*_r*.tar.gz
	# Averiguar como comprimir todo excepto lo que contiene ".bzrignore"
	#tar zcvf wiithon_v${VERSION}_r${REVISION}.tar.gz *

pull:
	bzr pull

commit: clean
	#bzr diff > DIFF.txt
	bzr commit --file="COMMIT.txt" && echo "" > COMMIT.txt
	bzr log --short > CHANGELOG.txt

log:
	bzr log --forward --short
