PREFIX=/usr/local

EMAIL="makiolo@gmail.com"
VERSION=${shell cat VERSION}
REVISION=${shell bzr revno}

PREFIX_RECURSOS_IMAGENES_CARATULAS=$(PREFIX)/share/wiithon/recursos/imagenes/caratulas
PREFIX_RECURSOS_IMAGENES_DISCOS=$(PREFIX)/share/wiithon/recursos/imagenes/discos

INSTALL_PKG=apt-get install

all: compilar

ayuda: help

help:
	@echo ==================================================================
	@echo "Escribe \"sudo make install\" solo instala"
	@echo "Escribe \"sudo make install_auto\" para instalar Wiithon y sus dependencias (con apt-get)"
	@echo ""
	@echo "Escribe \"sudo make uninstall\" para desinstalar wiithon"
	@echo "Escribe \"sudo make purge\" para desinstalar wiithon completamente"
	@echo "Escribe \"sudo make dependencias\" para instalar las dependencias con apt-get"
	@echo ""
	@echo "Escribe \"sudo make run LANGUAGE=XX\" para instalar & autoejecutar en un idioma como es, en, pt_BR ..."
	@echo ==================================================================

run: install
	LANGUAGE=$(LANGUAGE) wiithon

install_auto: uninstall dependencias install

dependencies: dependencias

dependencias:
	$(INSTALL_PKG) intltool imagemagick python-gtk2 python-glade2 python-sexy python-sqlalchemy gnome-icon-theme
	-@$(INSTALL_PKG) libc6-dev-i386
	@echo "=================================================================="
	@echo "Install depends"
	@echo "=================================================================="
#
#permissions_fix:
#	gpasswd -a $(USER) disk
#	@echo "=================================================================="
#	@echo "Fix permissions for WBFS. If dont detect, reboot GNOME / KDE"
#	@echo "=================================================================="
#

compilar: libwbfs_binding/wiithon_wrapper ./po/locale/da_DK/LC_MESSAGES/wiithon.mo ./po/locale/fi_FI/LC_MESSAGES/wiithon.mo ./po/locale/tr_TR/LC_MESSAGES/wiithon.mo ./po/locale/ru_RU/LC_MESSAGES/wiithon.mo ./po/locale/ko_KR/LC_MESSAGES/wiithon.mo ./po/locale/it/LC_MESSAGES/wiithon.mo ./po/locale/sv_SE/LC_MESSAGES/wiithon.mo ./po/locale/es/LC_MESSAGES/wiithon.mo ./po/locale/pt_PT/LC_MESSAGES/wiithon.mo ./po/locale/en/LC_MESSAGES/wiithon.mo ./po/locale/nl_NL/LC_MESSAGES/wiithon.mo ./po/locale/nb_NO/LC_MESSAGES/wiithon.mo ./po/locale/ja_JP/LC_MESSAGES/wiithon.mo ./po/locale/fr/LC_MESSAGES/wiithon.mo ./po/locale/pt_BR/LC_MESSAGES/wiithon.mo ./po/locale/de/LC_MESSAGES/wiithon.mo

install:
	mkdir -p $(PREFIX)/share/wiithon
	mkdir -p $(PREFIX)/share/wiithon/recursos/glade
	mkdir -p $(PREFIX)/share/wiithon/recursos/imagenes
	
	cp libwbfs_binding/wiithon_wrapper $(PREFIX)/share/wiithon
	cp libwbfs_binding/wiithon_wrapper $(PREFIX)/share/wiithon
	
	cp wiithon.py $(PREFIX)/share/wiithon
	cp libwbfs_binding/libwbfs/libwbfs.so /usr/lib
	
	cp wiithon_autodetectar.sh $(PREFIX)/share/wiithon
	cp wiithon_autodetectar_lector.sh $(PREFIX)/share/wiithon
	cp wiithon_autodetectar_fat32.sh $(PREFIX)/share/wiithon
	
	cp *.py $(PREFIX)/share/wiithon

	cp wiithon_usuario.desktop /usr/share/applications/

	cp recursos/icons/wiithon.png /usr/share/pixmaps
	cp recursos/icons/wiithon.svg /usr/share/pixmaps

	cp -R po/locale/ /usr/share/

	cp recursos/glade/*.ui $(PREFIX)/share/wiithon/recursos/glade
	cp recursos/imagenes/*.png $(PREFIX)/share/wiithon/recursos/imagenes
	
	mkdir -p $(PREFIX_RECURSOS_IMAGENES_CARATULAS)
	mkdir -p $(PREFIX_RECURSOS_IMAGENES_DISCOS)
	
	cp caratulas_fix/*.png $(PREFIX_RECURSOS_IMAGENES_CARATULAS)
	cp discos_fix/*.png $(PREFIX_RECURSOS_IMAGENES_DISCOS)

	chmod 755 $(PREFIX)/share/wiithon/*.py
	chmod 755 $(PREFIX)/share/wiithon/*.sh
	chmod 755 $(PREFIX)/share/wiithon/wiithon_wrapper

	chmod 644 $(PREFIX)/share/wiithon/recursos/glade/*.ui
	chmod 644 $(PREFIX)/share/wiithon/recursos/imagenes/*.png
	 
	chmod 777 $(PREFIX_RECURSOS_IMAGENES_CARATULAS)
	chmod 777 $(PREFIX_RECURSOS_IMAGENES_DISCOS)

	-ln -sf $(PREFIX)/share/wiithon/wiithon.py $(PREFIX)/bin/wiithon
	-ln -sf $(PREFIX)/share/wiithon/wiithon_wrapper $(PREFIX)/bin/wiithon_wrapper

	@echo "=================================================================="
	@echo "Wiithon Install OK"
	@echo "=================================================================="

uninstall:
	@echo "Limpiando posibles instalaciones antiguas"
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
	
	-$(RM) $(PREFIX_RECURSOS_IMAGENES_CARATULAS)/index.html*
	-$(RM) $(PREFIX_RECURSOS_IMAGENES_DISCOS)/index.html*
	-$(RM) $(PREFIX_RECURSOS_IMAGENES_CARATULAS)/*.png.1
	-$(RM) $(PREFIX_RECURSOS_IMAGENES_DISCOS)/*.png.1
	-$(RM) $(HOME_WIITHON_BDD)/*.db

	-$(RM) $(PREFIX)/share/wiithon/.acuerdo
	-$(RM) ~/.wiithon_acuerdo

	-$(RM) $(PREFIX)/share/wiithon/wiithon
	-$(RM) $(PREFIX)/share/wiithon/wiithon_autodetectar
	-$(RM) $(PREFIX)/share/wiithon/wiithon_autodetectar_lector

	-gconftool --recursive-unset /apps/nautilus-actions/configurations
	-$(RM) /usr/share/gconf/schemas/wiithon*.schemas
	-$(RM) /usr/share/applications/wiithon.desktop

	@echo "Limpiando instalacion actual"

	-$(RM) $(PREFIX)/bin/wiithon
	-$(RM) $(PREFIX)/bin/wiithon_wrapper
	
	-$(RM) $(PREFIX)/share/wiithon/*.py
	-$(RM) $(PREFIX)/share/wiithon/*.sh
	-$(RM) $(PREFIX)/share/wiithon/recursos/glade/*.ui
	-$(RM) $(PREFIX)/share/wiithon/recursos/imagenes/*.png
	
	-$(RM) $(PREFIX)/share/wiithon/wiithon_wrapper
	-$(RM) /usr/lib/libwbfs.so

	-$(RM) $(PREFIX)/share/wiithon/*.pyc
	
	-$(RM) /usr/share/locale/en/LC_MESSAGES/wiithon.mo
	-$(RM) /usr/share/locale/es/LC_MESSAGES/wiithon.mo
	-$(RM) /usr/share/locale/da_DK/LC_MESSAGES/wiithon.mo
	-$(RM) /usr/share/locale/fi_FI/LC_MESSAGES/wiithon.mo
	-$(RM) /usr/share/locale/it/LC_MESSAGES/wiithon.mo
	-$(RM) /usr/share/locale/ko_KR/LC_MESSAGES/wiithon.mo
	-$(RM) /usr/share/locale/nl_NL/LC_MESSAGES/wiithon.mo
	-$(RM) /usr/share/locale/pt_PT/LC_MESSAGES/wiithon.mo
	-$(RM) /usr/share/locale/sv_SE/LC_MESSAGES/wiithon.mo
	-$(RM) /usr/share/locale/de/LC_MESSAGES/wiithon.mo
	-$(RM) /usr/share/locale/fr/LC_MESSAGES/wiithon.mo
	-$(RM) /usr/share/locale/ja_JP/LC_MESSAGES/wiithon.mo
	-$(RM) /usr/share/locale/nb_NO/LC_MESSAGES/wiithon.mo
	-$(RM) /usr/share/locale/pt_BR/LC_MESSAGES/wiithon.mo
	-$(RM) /usr/share/locale/ru_RU/LC_MESSAGES/wiithon.mo
	-$(RM) /usr/share/locale/tr_TR/LC_MESSAGES/wiithon.mo

	-$(RM) /usr/share/applications/wiithon_usuario.desktop
	-$(RM) /usr/share/applications/wiithon_root.desktop
	
	-$(RM) /usr/share/pixmaps/wiithon.png
	-$(RM) /usr/share/pixmaps/wiithon.svg
	
	-$(RM) $(PREFIX)/share/wiithon/HOME.conf

	-rmdir $(PREFIX)/share/wiithon/recursos/glade
	
	@echo "=================================================================="
	@echo "Wiithon Uninstall OK"
	@echo "=================================================================="

purge: uninstall
	-$(RM) $(PREFIX_RECURSOS_IMAGENES_CARATULAS)/*.png
	-$(RM) $(PREFIX_RECURSOS_IMAGENES_DISCOS)/*.png
	-rmdir $(PREFIX_RECURSOS_IMAGENES_CARATULAS)
	-rmdir $(PREFIX_RECURSOS_IMAGENES_DISCOS)
	-rmdir $(PREFIX)/share/wiithon/recursos/imagenes
	-rmdir $(PREFIX)/share/wiithon/recursos
	-rmdir $(PREFIX)/share/wiithon
	-$(RM) -R $(HOME_WIITHON)
	@echo "=================================================================="
	@echo "Uninstall OK & all clean (purge covers, bdd ...)"
	@echo "=================================================================="

actualizar: uninstall pull install log
	@echo "=================================================================="
	@echo "Updated to $(VERSION) rev$(REVISION)"
	@echo "=================================================================="

clean: clean_libwbfs_binding clean_gettext
	$(RM) *.pyc
	$(RM) *~
	$(RM) po/*~
	touch po/*.pot

clean_gettext:
	-$(RM) po/locale/en/LC_MESSAGES/wiithon.mo
	-$(RM) po/locale/es/LC_MESSAGES/wiithon.mo
	-$(RM) po/locale/da_DK/LC_MESSAGES/wiithon.mo
	-$(RM) po/locale/fi_FI/LC_MESSAGES/wiithon.mo
	-$(RM) po/locale/it/LC_MESSAGES/wiithon.mo
	-$(RM) po/locale/ko_KR/LC_MESSAGES/wiithon.mo
	-$(RM) po/locale/nl_NL/LC_MESSAGES/wiithon.mo
	-$(RM) po/locale/pt_PT/LC_MESSAGES/wiithon.mo
	-$(RM) po/locale/sv_SE/LC_MESSAGES/wiithon.mo
	-$(RM) po/locale/de/LC_MESSAGES/wiithon.mo
	-$(RM) po/locale/fr/LC_MESSAGES/wiithon.mo
	-$(RM) po/locale/ja_JP/LC_MESSAGES/wiithon.mo
	-$(RM) po/locale/nb_NO/LC_MESSAGES/wiithon.mo
	-$(RM) po/locale/pt_BR/LC_MESSAGES/wiithon.mo
	-$(RM) po/locale/ru_RU/LC_MESSAGES/wiithon.mo
	-$(RM) po/locale/tr_TR/LC_MESSAGES/wiithon.mo
	
clean_libwbfs_binding:
	$(MAKE) -C libwbfs_binding clean

libwbfs_binding/wiithon_wrapper: libwbfs_binding/*.c libwbfs_binding/libwbfs/*.c libwbfs_binding/libwbfs/*.h 
	$(MAKE) -C libwbfs_binding

pull:
	bzr pull
	chown `whoami`\: * -R

commit: clean
	bzr commit --file="COMMIT" && echo "" > COMMIT

log:
	bzr log --forward --short

diff:
	-@bzr diff

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
# He desactivado fuzzy con -N
# tambien he quitado los comentarios con --no-location
po/%.po: po/plantilla.pot
	msgmerge -U -N --no-wrap --no-location $@ $(filter %.pot, $^)
	@touch $@

# generar MO
# FIXME: Crea po/locale/pt_BR/LC_MESSAGES/wiithon
# debería crear: po/locale/pt_BR/LC_MESSAGES/
# lo parcheo con el rmdir
po/locale/%/LC_MESSAGES/wiithon.mo: po/%.po
	@mkdir -p $(basename $@)
	msgfmt $< -o $@
	@rmdir $(basename $@)

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

