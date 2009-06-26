PREFIX=/usr/local

EMAIL="makiolo@gmail.com"
VERSION=${shell cat VERSION}
REVISION=${shell bzr revno}
HOME_EFECTIVO=${shell cat $(PREFIX)/share/wiithon/HOME.conf}
USUARIO=${shell basename $(HOME_EFECTIVO)}
HOME_WIITHON=$(HOME_EFECTIVO)/.wiithon
HOME_WIITHON_BDD=$(HOME_WIITHON)/bdd
HOME_WIITHON_CARATULAS=$(HOME_WIITHON)/caratulas
HOME_WIITHON_DISCOS=$(HOME_WIITHON)/discos
HOME_WIITHON_LOGS=$(HOME_WIITHON)/logs

all:
	@echo ==================================================================
	@echo "Escribe \"sudo make install_auto\" para instalar Wiithon y sus dependencias (con apt-get)"
	@echo ""
	@echo "Escribe \"sudo make uninstall\" para desinstalar wiithon"
	@echo "Escribe \"sudo make dependencias\" para instalar las dependencias con apt-get"
	@echo "Escribe \"sudo make install\" para instalar wiithon en espacio de root"
	@echo ""
	@echo "Escribe \"sudo make permisos\" para evitar que wiithon funcione como root"
	@echo ""
	@echo "Escribe \"sudo make purge\" para desinstalar wiithon completamente"
	@echo ""
	@echo "Escribe \"sudo make run\" para instalar & autoejecutar en español"
	@echo "Escribe \"sudo make runEN\" para instalar & autoejecutar en ingles"
	@echo ==================================================================

run: install
	LANGUAGE=es LANG=es_ES.UTF-8 wiithon

runEN: install
	LANGUAGE=en LANG=en_US.UTF-8 wiithon

install_auto: uninstall dependencias install

dependencias:
	apt-get install imagemagick wget rar intltool python-gtk2 python-glade2 python-sexy python-sqlalchemy gnome-icon-theme menu
	@echo "=================================================================="
	@echo "Instaladas dependencias"
	@echo "=================================================================="

permisos:
	gpasswd -a $(USUARIO) disk
	mkdir -p $(HOME_WIITHON)
	@mkdir -p $(HOME_WIITHON_BDD)
	@mkdir -p $(HOME_WIITHON_CARATULAS)
	@mkdir -p $(HOME_WIITHON_DISCOS)
	@mkdir -p $(HOME_WIITHON_LOGS)
	@echo "Corrigiendo permisos de $(HOME_WIITHON)"
	@chown $(USUARIO) $(HOME_WIITHON) -R

	@echo "Quitando wiithon como root del menu"
	-@$(RM) /usr/share/applications/wiithon_root.desktop
	@echo "Poniendo wiithon como usuario en el menu"
	@cp wiithon_usuario.desktop /usr/share/applications/

# FIXME: alguna forma de expandir todos los moo
install: wiithon_wrapper/wiithon_wrapper ./po/locale/da_DK/LC_MESSAGES/wiithon.mo ./po/locale/fi_FI/LC_MESSAGES/wiithon.mo ./po/locale/tr_TR/LC_MESSAGES/wiithon.mo ./po/locale/ru_RU/LC_MESSAGES/wiithon.mo ./po/locale/ko_KR/LC_MESSAGES/wiithon.mo ./po/locale/it/LC_MESSAGES/wiithon.mo ./po/locale/sv_SE/LC_MESSAGES/wiithon.mo ./po/locale/es/LC_MESSAGES/wiithon.mo ./po/locale/pt_PT/LC_MESSAGES/wiithon.mo ./po/locale/en/LC_MESSAGES/wiithon.mo ./po/locale/nl_NL/LC_MESSAGES/wiithon.mo ./po/locale/nb_NO/LC_MESSAGES/wiithon.mo ./po/locale/ja_JP/LC_MESSAGES/wiithon.mo ./po/locale/fr/LC_MESSAGES/wiithon.mo ./po/locale/pt_BR/LC_MESSAGES/wiithon.mo ./po/locale/de/LC_MESSAGES/wiithon.mo

	mkdir -p $(PREFIX)/share/wiithon
	mkdir -p $(PREFIX)/share/wiithon/recursos/glade
	mkdir -p $(PREFIX)/share/wiithon/recursos/imagenes

	echo $(HOME) > $(PREFIX)/share/wiithon/HOME.conf

	cp wiithon_wrapper/wiithon_wrapper $(PREFIX)/share/wiithon
	cp wiithon.py $(PREFIX)/share/wiithon
	
	cp wiithon_autodetectar.sh $(PREFIX)/share/wiithon
	cp wiithon_autodetectar_lector.sh $(PREFIX)/share/wiithon
	
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

	cp recursos/icons/wiithon.png /usr/share/pixmaps
	cp recursos/icons/wiithon.svg /usr/share/pixmaps

	cp -R po/locale/ /usr/share/

	cp recursos/glade/*.ui $(PREFIX)/share/wiithon/recursos/glade
	cp recursos/imagenes/*.png $(PREFIX)/share/wiithon/recursos/imagenes
	cp recursos/imagenes/cargando/*.png $(PREFIX)/share/wiithon/recursos/imagenes

	chmod 755 $(PREFIX)/share/wiithon/*.py
	chmod 755 $(PREFIX)/share/wiithon/*.sh
	chmod 755 $(PREFIX)/share/wiithon/wiithon_wrapper

	chmod 644 $(PREFIX)/share/wiithon/recursos/glade/*.ui
	chmod 644 $(PREFIX)/share/wiithon/recursos/imagenes/*.png

	-ln -sf $(PREFIX)/share/wiithon/wiithon.py $(PREFIX)/bin/wiithon
	-ln -sf $(PREFIX)/share/wiithon/wiithon_wrapper $(PREFIX)/bin/wiithon_wrapper

	@echo "=================================================================="
	@echo "Instalado OK"
	@echo "=================================================================="
	@echo "¿Como ejecutarlo? :"
	@echo "    1. Por Interfaz gráfico:"
	@echo "        - Vaya a su menú de Aplicaciones, y encontrará Wiithon en la sección 'Oficina' (funciona en KDE y GNOME)"
	@echo "    2. Por consola:"
	@echo "        - sudo wiithon"
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
	-$(RM) $(PREFIX)/share/wiithon/wbfs

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
	
	# Desinstalo los locales por "find"
	#-$(RM) /usr/share/locale/en/LC_MESSAGES/wiithon.mo
	#-$(RM) /usr/share/locale/es/LC_MESSAGES/wiithon.mo

	# Desinstalando la actual versión

	-$(RM) $(PREFIX)/bin/wiithon
	-$(RM) $(PREFIX)/bin/wiithon_wrapper
	
	-$(RM) $(PREFIX)/share/wiithon/*.py
	-$(RM) $(PREFIX)/share/wiithon/*.sh
	-$(RM) $(PREFIX)/share/wiithon/wiithon_wrapper
	-$(RM) $(PREFIX)/share/wiithon/recursos/glade/*.ui
	-$(RM) $(PREFIX)/share/wiithon/recursos/imagenes/*.png

	-$(RM) $(PREFIX)/share/wiithon/*.pyc
	
	-@find /usr/share/locale -name wiithon.mo | xargs rm

	-$(RM) /usr/share/applications/wiithon_usuario.desktop
	-$(RM) /usr/share/applications/wiithon_root.desktop
	
	-$(RM) /usr/share/pixmaps/wiithon.png
	-$(RM) /usr/share/pixmaps/wiithon.svg

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

clean: clean_wiithon_wrapper clean_gettext
	$(RM) *.pyc
	$(RM) *~
	$(RM) po/*~

clean_gettext:
	-@find po/locale/ -name wiithon.mo | xargs rm

clean_wiithon_wrapper:
	$(MAKE) -C wiithon_wrapper clean

wiithon_wrapper/wiithon_wrapper: wiithon_wrapper/*.c wiithon_wrapper/*.h wiithon_wrapper/libwbfs/*.c wiithon_wrapper/libwbfs/*.h 
	$(MAKE) -C wiithon_wrapper

# REPOSITORIO
pull:
	bzr pull

commit: clean
	@if [ `grep -n fuzzy po/*.po | wc -l` -eq 0 ]; then bzr commit --file="COMMIT" && echo "" > COMMIT; else echo "Hay fuzzy en los archivos po, resuelvelo, y repite esta operación"; fi;

log:
	bzr log --forward --short

diff:
	-@bzr diff

# No usar, (sino sabes lo que haces)
actualizar:
	bzr pull && sudo make install_auto

# TRADUCCION
# http://faq.pygtk.org/index.py?req=show&file=faq22.002.htp
# http://misdocumentos.net/wiki/linux/locales

# Generar plantilla POT
po/plantilla.pot: recursos/glade/*.ui.h *.py
	@echo "*** GETTEXT *** Extrayendo strings del código"
	xgettext --language=Python --no-wrap --no-location --sort-output --omit-header --keyword=_ --keyword=N_ --from-code=utf-8 --package-name="wiithon" --package-version="$(VERSION)" --msgid-bugs-address=$(EMAIL) -o po/plantilla.pot $^

# extraer strings del glade
recursos/glade/%.ui.h: recursos/glade/%.ui
	intltool-extract --type="gettext/glade" $<

# generar PO, si ya existe, mezcla o sincroniza
po/%.po: po/plantilla.pot
	# He desactivado fuzzy con -N
	# tambien he quitado los comentarios con --no-location
	msgmerge -U -N --no-wrap --no-location $@ $(filter %.pot, $^)
	touch $@

# generar MO
po/locale/%/LC_MESSAGES/wiithon.mo: po/%.po
	# FIXME: Crea po/locale/pt_BR/LC_MESSAGES/wiithon
	# debería crear: po/locale/pt_BR/LC_MESSAGES/
	# lo parcheo con el rmdir
	mkdir -p $(basename $@)
	msgfmt $< -o $@
	rmdir $(basename $@)

# generar PO VACIO a partir de plantilla POT
initPO: po/plantilla.pot
	@echo "*** GETTEXT *** Creando PO"
	
	# Vamos comentando los idiomas que se pretende traducir para evitar borrados
	
	# Castellano
	#msginit -i po/plantilla.pot -o po/es.po --no-translator
	# Inglés
	#msginit -i po/plantilla.pot -o po/en.po --no-translator
	# brasileño
	#msginit -i po/plantilla.pot -o po/pt_BR.po --no-translator
	# portugues
	msginit -i po/plantilla.pot -o po/pt_PT.po --no-translator
	# alemán
	msginit -i po/plantilla.pot -o po/de.po --no-translator
	# francés
	msginit -i po/plantilla.pot -o po/fr.po --no-translator
	# italiano
	msginit -i po/plantilla.pot -o po/it.po --no-translator
	# danish da_DK
	msginit -i po/plantilla.pot -o po/da_DK.po --no-translator
	# dutch nl_NL
	msginit -i po/plantilla.pot -o po/nl_NL.po --no-translator
	# finnish fi_FI
	msginit -i po/plantilla.pot -o po/fi_FI.po --no-translator
	# japanese ja_JP
	msginit -i po/plantilla.pot -o po/ja_JP.po --no-translator
	# korean ko_KR
	msginit -i po/plantilla.pot -o po/ko_KR.po --no-translator
	# norwegian nb_NO
	msginit -i po/plantilla.pot -o po/nb_NO.po --no-translator
	# russian ru_RU
	msginit -i po/plantilla.pot -o po/ru_RU.po --no-translator
	# swedish sv_SE
	msginit -i po/plantilla.pot -o po/sv_SE.po --no-translator
	# turkish tr_TR
	msginit -i po/plantilla.pot -o po/tr_TR.po --no-translator

