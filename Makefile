PREFIX=/usr/local

VERSION=${shell cat VERSION.txt}
REVISION=${shell bzr revno}

all: wbfs
	@echo ==================================================================
	@echo Escribe "sudo make run" para ejecutar
	@echo Escribe "sudo make install" para instalar
	@echo Escribe "sudo make uninstall" para desinstalar
	@echo ==================================================================

run: install
	sudo wiithon
	
runEN: install
	sudo LANG=en_US.UTF-8 wiithon

install: uninstall wbfs generarPO

	@echo "=================================================================="
	@echo "Antes de instalar, se ha desinstalado"
	@echo "=================================================================="

	mkdir -p $(PREFIX)/share/wiithon
	mkdir -p $(PREFIX)/share/wiithon/recursos/glade
	mkdir -p $(PREFIX)/share/wiithon/recursos/imagenes

	cp wiithon.py $(PREFIX)/share/wiithon
	cp wiithon_autodetectar.sh $(PREFIX)/share/wiithon
	cp wiithon_autodetectar_lector.sh $(PREFIX)/share/wiithon
	cp wbfs $(PREFIX)/share/wiithon
	cp cli.py $(PREFIX)/share/wiithon
	cp gui.py $(PREFIX)/share/wiithon
	cp builder_wrapper.py $(PREFIX)/share/wiithon
	cp util.py $(PREFIX)/share/wiithon
	cp core.py $(PREFIX)/share/wiithon
	cp config.py $(PREFIX)/share/wiithon
	cp pool.py $(PREFIX)/share/wiithon
	cp trabajo.py $(PREFIX)/share/wiithon
	cp mensaje.py $(PREFIX)/share/wiithon

	cp po/en/LC_MESSAGES/wiithon.mo /usr/share/locale/en/LC_MESSAGES/wiithon.mo
	cp po/es/LC_MESSAGES/wiithon.mo /usr/share/locale/es/LC_MESSAGES/wiithon.mo

	cp recursos/glade/*.ui $(PREFIX)/share/wiithon/recursos/glade
	cp recursos/imagenes/*.png $(PREFIX)/share/wiithon/recursos/imagenes

	chmod 755 $(PREFIX)/share/wiithon/wiithon.py
	chmod 755 $(PREFIX)/share/wiithon/wiithon_autodetectar.sh
	chmod 755 $(PREFIX)/share/wiithon/wiithon_autodetectar_lector.sh
	chmod 755 $(PREFIX)/share/wiithon/wbfs
	chmod 755 $(PREFIX)/share/wiithon/cli.py
	chmod 755 $(PREFIX)/share/wiithon/gui.py
	chmod 755 $(PREFIX)/share/wiithon/builder_wrapper.py
	chmod 755 $(PREFIX)/share/wiithon/util.py
	chmod 755 $(PREFIX)/share/wiithon/core.py
	chmod 755 $(PREFIX)/share/wiithon/config.py
	chmod 755 $(PREFIX)/share/wiithon/pool.py

	chmod 644 $(PREFIX)/share/wiithon/recursos/glade/*.ui
	chmod 644 $(PREFIX)/share/wiithon/recursos/imagenes/*.png
	
	ln -s $(PREFIX)/share/wiithon/wiithon.py $(PREFIX)/bin/wiithon

	@echo "=================================================================="
	@echo "Instalado OK"
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
	
	-$(RM) $(PREFIX)/share/wiithon/glade_wrapper.py
	
	-$(RM) $(PREFIX)/share/wiithon/recursos/glade/*.xml
	-$(RM) $(PREFIX)/share/wiithon/recursos/glade/*.glade

	-$(RM) $(PREFIX)/share/wiithon/.acuerdo
	-$(RM) ~/.wiithon_acuerdo

	-$(RM) $(PREFIX)/share/wiithon/wiithon
	-$(RM) $(PREFIX)/share/wiithon/wiithon_autodetectar
	-$(RM) $(PREFIX)/share/wiithon/wiithon_autodetectar_lector

	-$(RM) /usr/share/gconf/schemas/wiithon*.schemas
	-rmdir /usr/share/gconf/schemas/
	
	# Desinstalando la actual versión
	
	-$(RM) $(PREFIX)/bin/wiithon
	-$(RM) $(PREFIX)/share/wiithon/wiithon_autodetectar.sh
	-$(RM) $(PREFIX)/share/wiithon/wiithon_autodetectar_lector.sh
	-$(RM) $(PREFIX)/share/wiithon/wbfs
	-$(RM) $(PREFIX)/share/wiithon/wiithon.py	
	-$(RM) $(PREFIX)/share/wiithon/util.py	
	-$(RM) $(PREFIX)/share/wiithon/cli.py	
	-$(RM) $(PREFIX)/share/wiithon/gui.py
	-$(RM) $(PREFIX)/share/wiithon/builder_wrapper.py
	-$(RM) $(PREFIX)/share/wiithon/core.py	
	-$(RM) $(PREFIX)/share/wiithon/config.py
	-$(RM) $(PREFIX)/share/wiithon/pool.py
	-$(RM) $(PREFIX)/share/wiithon/trabajo.py
	-$(RM) $(PREFIX)/share/wiithon/mensaje.py
	-$(RM) $(PREFIX)/share/wiithon/recursos/glade/*.ui
	-$(RM) $(PREFIX)/share/wiithon/recursos/imagenes/*.png
	
	-$(RM) $(PREFIX)/share/wiithon/*.pyc
	
	-$(RM) /usr/share/locale/en/LC_MESSAGES/wiithon.mo
	-$(RM) /usr/share/locale/es/LC_MESSAGES/wiithon.mo
	
	-rmdir $(PREFIX)/share/wiithon/recursos/glade
	-rmdir $(PREFIX)/share/wiithon/recursos/imagenes
	-rmdir $(PREFIX)/share/wiithon/recursos
	-rmdir $(PREFIX)/share/wiithon

	@echo "=================================================================="
	@echo "Desinstalado OK"
	@echo "=================================================================="

clean: clean_wbfs
	$(RM) *.pyc
	$(RM) *~

clean_wbfs:
	$(MAKE) -C wbfs_src clean
	-$(RM) wbfs

wbfs: /usr/include/openssl/aes.h /usr/include/openssl/md5.h /usr/include/openssl/sha.h
	$(MAKE) -C wbfs_src
	cp wbfs_src/wbfs .

/usr/include/openssl/*.h:
	@echo "Deberías instalar \"libssl-dev\" para poder compilar wbfs"
	@return

empaquetar: wbfs clean
	$(RM) wiithon_v*_r*.tar.gz
	# Averiguar como comprimir todo excepto lo que contiene ".bzrignore"
	#tar zcvf wiithon_v${VERSION}_r${REVISION}.tar.gz *.py *.sh

# REPOSITORIO

pull:
	bzr pull

commit: regenerarPO clean diff
	bzr commit --file="COMMIT.txt" && echo "" > COMMIT.txt
	bzr log --short > CHANGELOG.txt

log:
	bzr log --forward --short

diff:
	-@bzr diff > DIFF.txt

# TRADUCCION
# http://faq.pygtk.org/index.py?req=show&file=faq22.002.htp
# generar PO VACIO a partir de plantilla POT
po/en.po: generarPlantilla
	@echo "*** GETTEXT *** Creando POO: en_US"
	@LANG=en_US.UTF-8 msginit -i po/plantilla.pot -o po/en.po --no-translator

po/es.po: generarPlantilla
	@echo "*** GETTEXT *** Creando POO: es_ES"
	@LANG=es_ES.UTF-8 msginit -i po/plantilla.pot -o po/es.po --no-translator
	
# extraer strings del glade
extraerGlade:
	@echo "*** GETTEXT *** Extrayendo strings del glade"
	@intltool-extract --type="gettext/glade" recursos/glade/wiithon.ui
	@intltool-extract --type="gettext/glade" recursos/glade/alerta.ui
	
# Generar plantilla POT
generarPlantilla: extraerGlade
	@echo "*** GETTEXT *** Extrayendo strings del código"
	@xgettext --language=Python --keyword=_ --keyword=N_ --from-code=utf-8 --sort-by-file --package-name="wiithon" --package-version="`cat VERSION.txt`" --msgid-bugs-address=makiolo@gmail.com -o po/plantilla.pot *.py recursos/glade/*.ui.h
	
# generar PO, si ya existe, mezcla o sincroniza
actualizarPO: generarPlantilla
	@echo "*** GETTEXT *** Actualizando POO"
	@msgmerge -U po/en.po po/plantilla.pot
	@msgmerge -U po/es.po po/plantilla.pot

# Generar los MOO (compilados binadores de los PO)
generarPO: actualizarPO
	@echo "*** GETTEXT *** Generando MOO"
	@mkdir -p po/en/LC_MESSAGES/
	@mkdir -p po/es/LC_MESSAGES/
	@msgfmt po/es.po -o po/es/LC_MESSAGES/wiithon.mo
	@msgfmt po/en.po -o po/en/LC_MESSAGES/wiithon.mo

# borrar Todos los PO y POT
limpiarPO:
	@echo "*** GETTEXT *** Borrando POO , POT y MOO"
	@$(RM) po/es.po
	@$(RM) po/en.po
	@$(RM) po/plantilla.pot
	@$(RM) po/es/LC_MESSAGES/wiithon.mo
	@$(RM) po/en/LC_MESSAGES/wiithon.mo

# Se le llama antes del commit
regenerarPO: limpiarPO po/en.po po/es.po generarPO
