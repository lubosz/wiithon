PREFIX=/usr/local

VERSION=${shell cat VERSION.txt}
REVISION=${shell bzr revno}
HOME_EFECTIVO=${shell cat /usr/local/share/wiithon/HOME.conf}
USUARIO=${shell basename $(HOME_EFECTIVO)}
HOME_WIITHON=$(HOME_EFECTIVO)/.wiithon
HOME_WIITHON_BDD=$(HOME_WIITHON)/bdd
HOME_WIITHON_CARATULAS=$(HOME_WIITHON)/caratulas
HOME_WIITHON_DISCOS=$(HOME_WIITHON)/discos
HOME_WIITHON_LOGS=$(HOME_WIITHON)/logs

all: wbfs
	@echo ==================================================================
	@echo "Escribe \"sudo make install_auto\" para instalar Wiithon y sus dependencias (con apt-get)"
	@echo "Escribe \"sudo make install\" para instalar wiithon"
	@echo "Escribe \"sudo make uninstall\" para desinstalar wiithon"
	@echo "Escribe \"sudo make purge\" para desinstalar wiithon completamente"
	@echo "Escribe \"sudo make dependencias\" para instalar las dependencias con apt-get"
	@echo "Escribe \"sudo make run\" para ejecutar en español"
	@echo "Escribe \"sudo make runEN\" para ejecutar en ingles"
	@echo ==================================================================

run: install
	LANGUAGE=es LANG=es_ES.UTF-8 wiithon

runEN: install
	LANGUAGE=en LANG=en_US.UTF-8 wiithon

install_auto: dependencias install

dependencias:
	apt-get install imagemagick wget rar libssl-dev intltool python-gtk2 python-glade2 python-sexy python-sqlalchemy gnome-icon-theme menu

permisos:
	gpasswd -a $(USUARIO) disk
	mkdir -p $(HOME_WIITHON)
	mkdir -p $(HOME_WIITHON_BDD)
	mkdir -p $(HOME_WIITHON_CARATULAS)
	mkdir -p $(HOME_WIITHON_DISCOS)
	mkdir -p $(HOME_WIITHON_LOGS)
	chown $(USUARIO) $(HOME_WIITHON) -R
	
	-$(RM) /usr/share/applications/wiithon_root.desktop
	cp wiithon_usuario.desktop /usr/share/applications/
	@echo "=================================================================="
	@echo "Se han modificado los permisos para que $(USUARIO) pueda r/w en particiones WBFS"
	@echo "Puede que tenga que reiniciar GNOME / KDE para que surga efecto"
	@echo "=================================================================="

install: uninstall wbfs generarMOO
	@echo "=================================================================="
	@echo "Antes de instalar, se ha desinstalado"
	@echo "=================================================================="

	mkdir -p $(PREFIX)/share/wiithon
	mkdir -p $(PREFIX)/share/wiithon/recursos/glade
	mkdir -p $(PREFIX)/share/wiithon/recursos/imagenes

	echo $(HOME) > $(PREFIX)/share/wiithon/HOME.conf

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
	cp preferencias.py $(PREFIX)/share/wiithon
	cp juego.py $(PREFIX)/share/wiithon
	cp animar.py $(PREFIX)/share/wiithon
	
	cp wiithon_root.desktop /usr/share/applications/
	cp wiithon_usuario.desktop /usr/share/applications/

	cp recursos/icons/wiithon.svg /usr/share/pixmaps

	cp po/en/LC_MESSAGES/wiithon.mo /usr/share/locale/en/LC_MESSAGES/wiithon.mo
	cp po/es/LC_MESSAGES/wiithon.mo /usr/share/locale/es/LC_MESSAGES/wiithon.mo

	cp recursos/glade/*.ui $(PREFIX)/share/wiithon/recursos/glade
	cp recursos/imagenes/*.png $(PREFIX)/share/wiithon/recursos/imagenes
	cp recursos/imagenes/cargando/*.png $(PREFIX)/share/wiithon/recursos/imagenes

	chmod 755 $(PREFIX)/share/wiithon/*.py
	chmod 755 $(PREFIX)/share/wiithon/*.sh
	chmod 755 $(PREFIX)/share/wiithon/wbfs

	chmod 644 $(PREFIX)/share/wiithon/recursos/glade/*.ui
	chmod 644 $(PREFIX)/share/wiithon/recursos/imagenes/*.png

	ln -s $(PREFIX)/share/wiithon/wiithon.py $(PREFIX)/bin/wiithon

	@echo "=================================================================="
	@echo "Instalado OK"
	@echo "=================================================================="
	@echo "¿Como ejecutarlo? :"
	@echo "\t1. Por Interfaz gráfico:"
	@echo "\t\t\t- Vaya a su menú de Aplicaciones, y encontrará Wiithon en la sección 'Oficina' (funciona en KDE y GNOME)"
	@echo "\t2. Por consola:"
	@echo "\t\t\t- sudo wiithon"
	@echo "=================================================================="
	@echo "Recuerde: Puede escribir \"sudo make permisos\" para evitar el uso de root"

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
	
	-gconftool --recursive-unset /apps/nautilus-actions/configurations
	-$(RM) /usr/share/gconf/schemas/wiithon*.schemas
	-$(RM) /usr/share/applications/wiithon.desktop

	# Desinstalando la actual versión
		
	-$(RM) $(PREFIX)/bin/wiithon
	-$(RM) $(PREFIX)/share/wiithon/*.py
	-$(RM) $(PREFIX)/share/wiithon/*.sh
	-$(RM) $(PREFIX)/share/wiithon/wbfs
	-$(RM) $(PREFIX)/share/wiithon/recursos/glade/*.ui
	-$(RM) $(PREFIX)/share/wiithon/recursos/imagenes/*.png

	-$(RM) $(PREFIX)/share/wiithon/*.pyc

	-$(RM) /usr/share/locale/en/LC_MESSAGES/wiithon.mo
	-$(RM) /usr/share/locale/es/LC_MESSAGES/wiithon.mo
	
	-$(RM) /usr/share/applications/wiithon_usuario.desktop
	-$(RM) /usr/share/applications/wiithon_root.desktop

	-rmdir $(PREFIX)/share/wiithon/recursos/glade
	-rmdir $(PREFIX)/share/wiithon/recursos/imagenes
	-rmdir $(PREFIX)/share/wiithon/recursos

	@echo "=================================================================="
	@echo "Desinstalado OK"
	@echo "=================================================================="

purge: uninstall
	-$(RM) -R $(HOME_WIITHON)
	-$(RM) $(PREFIX)/share/wiithon/HOME.conf
	-rmdir $(PREFIX)/share/wiithon

	@echo "=================================================================="
	@echo "Desinstalado OK y limpiado cualquier configuración"
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

# REPOSITORIO

pull:
	bzr pull

commit: clean
	bzr commit --file="COMMIT.txt" && echo "" > COMMIT.txt
	bzr log --short > CHANGELOG.txt

log:
	bzr log --forward --short

diff:
	-@bzr diff > DIFF.txt

# No usar, (sino sabes lo que haces)
actualizar:
	bzr pull && sudo make install_auto

# TRADUCCION
# http://faq.pygtk.org/index.py?req=show&file=faq22.002.htp
# http://misdocumentos.net/wiki/linux/locales

# generar PO VACIO a partir de plantilla POT
generarPO: generarPlantilla
	@echo "*** GETTEXT *** Creando POO: es y en"
	LANG=es_ES.UTF-8 msginit -i po/plantilla.pot -o po/es.po --no-translator
	LANG=en_US.UTF-8 msginit -i po/plantilla.pot -o po/en.po --no-translator

# extraer strings del glade
extraerGlade:
	@echo "*** GETTEXT *** Extrayendo strings del glade"
	intltool-extract --type="gettext/glade" recursos/glade/wiithon.ui
	intltool-extract --type="gettext/glade" recursos/glade/alerta.ui

# generar PO, si ya existe, mezcla o sincroniza
actualizarPO: generarPlantilla
	@echo "*** GETTEXT *** Actualizando POO"
	msgmerge -U po/en.po po/plantilla.pot
	msgmerge -U po/es.po po/plantilla.pot

# Generar plantilla POT
generarPlantilla: extraerGlade
	@echo "*** GETTEXT *** Extrayendo strings del código"
	xgettext --language=Python --omit-header --keyword=_ --keyword=N_ --from-code=utf-8 --sort-by-file --package-name="wiithon" --package-version="`cat VERSION.txt`" --msgid-bugs-address=makiolo@gmail.com -o po/plantilla.pot *.py recursos/glade/*.ui.h

# Generar los MOO (compilados binarios de los PO)
generarMOO: actualizarPO
	@echo "*** GETTEXT *** Generando MOO"
	mkdir -p po/en/LC_MESSAGES/
	mkdir -p po/es/LC_MESSAGES/
	msgfmt po/es.po -o po/es/LC_MESSAGES/wiithon.mo
	msgfmt po/en.po -o po/en/LC_MESSAGES/wiithon.mo

# borrar los PO
limpiarPO:
	@echo "*** GETTEXT *** Borrando POO"
	$(RM) po/es.po
	$(RM) po/en.po

# OJO: Borra todas las traducciones
regenerarPO: limpiarPO generarPO generarMOO

