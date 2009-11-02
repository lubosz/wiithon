PREFIX=/usr/local
EMAIL="makiolo@gmail.com"
VERSION=${shell ./doc/VERSION}
REVISION=${shell bzr revno}
ARCH=${shell uname -m}
INSTALL_PKG=apt-get install

all: compile

help:
	@echo ==================================================================
	@echo "Escribe \"make\" para compilar todo"
	@echo ""
	@echo "Escribe \"sudo make install\" solo instala"
	@echo "Escribe \"sudo make install_auto\" para instalar Wiithon y sus dependencias (con apt-get)"
	@echo ""
	@echo "Escribe \"sudo make uninstall\" para desinstalar wiithon"
	@echo "Escribe \"sudo make purge\" para desinstalar wiithon completamente"
	@echo "Escribe \"sudo make dependencias\" para instalar las dependencias con apt-get"
	@echo ""
	@echo "Escribe \"make run LANGUAGE=XX\" para instalar & autoejecutar en un idioma como es, en, pt_BR ..."
	@echo ==================================================================

run: install
	LANGUAGE=$(LANGUAGE) wiithon

install_auto: dependencias compile install

permisos:
	gpasswd -a ${SUDO_USER} disk

dependencias: permisos
	$(INSTALL_PKG) libc6 libc6-dev intltool imagemagick python-gtk2 python-glade2 python-sexy python-sqlalchemy gnome-icon-theme g++
	-@$(INSTALL_PKG) libc6-dev-i386 libc6-i386
	@echo "=================================================================="
	@echo "Install depends OK"
	@echo "=================================================================="

compile: ./po/locale/da_DK/LC_MESSAGES/wiithon.mo ./po/locale/fi_FI/LC_MESSAGES/wiithon.mo ./po/locale/tr_TR/LC_MESSAGES/wiithon.mo ./po/locale/ru_RU/LC_MESSAGES/wiithon.mo ./po/locale/ko_KR/LC_MESSAGES/wiithon.mo ./po/locale/it/LC_MESSAGES/wiithon.mo ./po/locale/sv_SE/LC_MESSAGES/wiithon.mo ./po/locale/es/LC_MESSAGES/wiithon.mo ./po/locale/pt_PT/LC_MESSAGES/wiithon.mo ./po/locale/en/LC_MESSAGES/wiithon.mo ./po/locale/nl_NL/LC_MESSAGES/wiithon.mo ./po/locale/nb_NO/LC_MESSAGES/wiithon.mo ./po/locale/ja_JP/LC_MESSAGES/wiithon.mo ./po/locale/fr/LC_MESSAGES/wiithon.mo ./po/locale/pt_BR/LC_MESSAGES/wiithon.mo ./po/locale/de/LC_MESSAGES/wiithon.mo ./po/locale/es_CA/LC_MESSAGES/wiithon.mo unrar-nonfree/unrar libwbfs_binding/wiithon_wrapper
	@echo "=================================================================="
	@echo "Compile OK"
	@echo "=================================================================="

making_directories:
	@mkdir -p $(DESTDIR)/usr/share/pixmaps
	@mkdir -p $(DESTDIR)/usr/lib
	@mkdir -p $(DESTDIR)/usr/share/applications
	@mkdir -p $(DESTDIR)$(PREFIX)/bin
	@mkdir -p $(DESTDIR)$(PREFIX)/lib
	@mkdir -p $(DESTDIR)$(PREFIX)/lib32
	@mkdir -p $(DESTDIR)$(PREFIX)/share/wiithon
	@mkdir -p $(DESTDIR)$(PREFIX)/share/wiithon/recursos/glade
	@mkdir -p $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes
	@mkdir -p $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/accesorio
	@mkdir -p $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/caratulas
	@mkdir -p $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/discos
	
recicled_old_wiithon: making_directories
	-@mv -f ~/.wiithon/caratulas/*.png $(PREFIX)/share/wiithon/recursos/imagenes/caratulas
	-@mv -f ~/.wiithon/discos/*.png $(PREFIX)/share/wiithon/recursos/imagenes/discos
	
copy_archives: making_directories
	cp libwbfs_binding/wiithon_wrapper $(DESTDIR)$(PREFIX)/share/wiithon/
	cp unrar-nonfree/unrar $(DESTDIR)$(PREFIX)/share/wiithon/
	
	cp *.py $(DESTDIR)$(PREFIX)/share/wiithon
	cp libwbfs_binding/libwbfs/libwbfs.so $(DESTDIR)$(PREFIX)/lib/

	cp wiithon_autodetectar.sh $(DESTDIR)$(PREFIX)/share/wiithon
	cp wiithon_autodetectar_lector.sh $(DESTDIR)$(PREFIX)/share/wiithon
	cp wiithon_autodetectar_fat32.sh $(DESTDIR)$(PREFIX)/share/wiithon
	
	cp wiithon_usuario.desktop $(DESTDIR)/usr/share/applications/

	cp recursos/icons/wiithon.png $(DESTDIR)/usr/share/pixmaps
	cp recursos/icons/wiithon.svg $(DESTDIR)/usr/share/pixmaps

	cp -R po/locale/ $(DESTDIR)/usr/share/

	cp recursos/glade/*.ui $(DESTDIR)$(PREFIX)/share/wiithon/recursos/glade
	cp recursos/imagenes/*.png $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes
	cp recursos/imagenes/accesorio/*.jpg $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/accesorio
	
	cp recursos/caratulas_fix/*.png $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/caratulas
	cp recursos/discos_fix/*.png $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/discos
	
set_permisses:
	chmod 755 $(DESTDIR)$(PREFIX)/share/wiithon/*.py
	chmod 755 $(DESTDIR)$(PREFIX)/share/wiithon/*.sh
	chmod 755 $(DESTDIR)$(PREFIX)/share/wiithon/wiithon_wrapper
	chmod 755 $(DESTDIR)$(PREFIX)/share/wiithon/unrar

	chmod 644 $(DESTDIR)$(PREFIX)/share/wiithon/recursos/glade/*.ui
	chmod 644 $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/*.png
	 
	chmod 777 $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/caratulas
	chmod 777 $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/discos

postinst:
ifeq ($(ARCH), x86_64)
	ln -sf $(PREFIX)/lib/libwbfs.so /usr/lib32
else
	ln -sf $(PREFIX)/lib/libwbfs.so /usr/lib
endif
	-ln -sf $(PREFIX)/share/wiithon/wiithon.py $(PREFIX)/bin/wiithon
	-ln -sf $(PREFIX)/share/wiithon/wiithon_wrapper $(PREFIX)/bin/wiithon_wrapper

install: uninstall recicled_old_wiithon copy_archives set_permisses postinst
	@echo "=================================================================="
	@echo "Wiithon Install OK"
	@echo "=================================================================="

install4ppa: copy_archives set_permisses
	@echo "=================================================================="
	@echo "Wiithon Install for PPA OK"
	@echo "=================================================================="

generate_changelog:
	@ln -sf $(shell pwd)/recursos/bazaar-plugins/gnulog.py ~/.bazaar/plugins/gnulog.py
	bzr log -v --log-format 'gnu' > debian/changelog
	@$(RM) ~/.bazaar/plugins/gnulog.py

deb: generate_changelog
	debuild -b -uc -us -tc

#
# Only need first time
#
#ppa-new: generate_changelog
#	debuild -S -sa -k0xB8F0176A -I -i --lintian-opts -Ivi
#	mv ../wiithon_$(VERSION).tar.gz ../wiithon_$(VERSION).orig.tar.gz
#	debuild -S -sk -k0xB8F0176A -I -i --lintian-opts -Ivi
#

ppa-inc: generate_changelog
	debuild -S -sd -k0xB8F0176A -I -i --lintian-opts -Ivi
	
ppa-upload: ppa-inc
	dput ppa:wii.sceners.linux/wiithon ../wiithon_$(VERSION)_source.changes

uninstall:
	@echo "Uninstall ..."
	
	-$(RM) -R ~/.wiithon/caratulas/
	-$(RM) -R ~/.wiithon/discos/
	-$(RM) ~/.wiithon/bdd/juegos.db
	-$(RM) ~/.wiithon_acuerdo
	-$(RM) $(PREFIX)/share/wiithon/.acuerdo
	
	-$(RM) /usr/bin/wiithon
	-$(RM) /usr/bin/wiithon_autodetectar
	-$(RM) /usr/bin/wiithon_autodetectar_lector
	-@$(RM) /usr/bin/wbfs

	-$(RM) $(PREFIX)/bin/wiithon_autodetectar
	-$(RM) $(PREFIX)/bin/wiithon_autodetectar_lector
	-$(RM) $(PREFIX)/bin/wbfs
	-$(RM) $(PREFIX)/share/wiithon/wbfs

	-$(RM) $(PREFIX)/share/wiithon/glade_wrapper.py

	-$(RM) $(PREFIX)/share/wiithon/recursos/glade/*.xml
	-$(RM) $(PREFIX)/share/wiithon/recursos/glade/*.glade

	-$(RM) $(PREFIX)/share/wiithon/wiithon
	-$(RM) $(PREFIX)/share/wiithon/wiithon_autodetectar
	-$(RM) $(PREFIX)/share/wiithon/wiithon_autodetectar_lector

	-@gconftool --recursive-unset /apps/nautilus-actions/configurations
	-@$(RM) /usr/share/gconf/schemas/wiithon*.schemas

	-$(RM) $(PREFIX)/bin/wiithon
	-$(RM) $(PREFIX)/bin/wiithon_wrapper
	
	-$(RM) $(PREFIX)/share/wiithon/unrar
	-$(RM) $(PREFIX)/share/wiithon/*.py
	-$(RM) $(PREFIX)/share/wiithon/*.sh
	-$(RM) $(PREFIX)/share/wiithon/recursos/glade/*.ui
	-$(RM) $(PREFIX)/share/wiithon/recursos/imagenes/*.png
	-$(RM) $(PREFIX)/share/wiithon/recursos/imagenes/accesorio/*.jpg
	
	-$(RM) $(PREFIX)/share/wiithon/wiithon_wrapper
	-$(RM) /usr/lib/libwbfs.so
	-$(RM) /usr/lib32/libwbfs.so
	-$(RM) $(PREFIX)/lib/libwbfs.so

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
	-$(RM) /usr/share/locale/es_CA/LC_MESSAGES/wiithon.mo

	-$(RM) /usr/share/applications/wiithon_usuario.desktop
	-$(RM) /usr/share/applications/wiithon_root.desktop
	
	-$(RM) /usr/share/pixmaps/wiithon.png
	-$(RM) /usr/share/pixmaps/wiithon.svg
	
	-$(RM) $(PREFIX)/share/wiithon/HOME.conf
	
	@echo "=================================================================="
	@echo "Wiithon Uninstall OK"
	@echo "=================================================================="

purge: uninstall

	-$(RM) -R ~/.wiithon

	-$(RM) $(PREFIX)/share/wiithon/recursos/imagenes/caratulas/*.png
	-$(RM) $(PREFIX)/share/wiithon/recursos/imagenes/discos/*.png
	-rmdir $(PREFIX)/share/wiithon/recursos/imagenes/caratulas
	-rmdir $(PREFIX)/share/wiithon/recursos/imagenes/discos
	-rmdir $(PREFIX)/share/wiithon/recursos/imagenes
	-rmdir $(PREFIX)/share/wiithon/recursos/glade
	-rmdir $(PREFIX)/share/wiithon/recursos
	-rmdir $(PREFIX)/share/wiithon
	@echo "=================================================================="
	@echo "Uninstall OK & all clean (purge covers & disc-art ...)"
	@echo "=================================================================="

update: pull install log
	@echo "=================================================================="
	@echo "Updated to $(VERSION)
	@echo "=================================================================="

clean: clean_libwbfs_binding clean_gettext clean_unrar
	$(RM) *.pyc
	$(RM) *~
	$(RM) po/*~
	$(RM) po/plantilla.pot

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
	-$(RM) po/locale/es_CA/LC_MESSAGES/wiithon.mo

clean_unrar:
	$(MAKE) -C unrar-nonfree clean
	
clean_libwbfs_binding:
	$(MAKE) -C libwbfs_binding clean

libwbfs_binding/wiithon_wrapper: libwbfs_binding/*.c libwbfs_binding/libwbfs/*.c libwbfs_binding/libwbfs/*.h 
	$(MAKE) -C libwbfs_binding

unrar-nonfree/unrar: unrar-nonfree/*.cpp unrar-nonfree/*.hpp
	$(MAKE) -C unrar-nonfree

pull:
	bzr pull

commit: clean compile
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
	xgettext --language=Python --no-wrap --no-location --sort-output --omit-header --keyword=_ --keyword=N_ --from-code=utf-8 --package-name="wiithon" --package-version="$(VERSION)" --msgid-bugs-address=$(EMAIL) -o po/plantilla.pot $^ 2> /dev/null

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
	# alemán
	#msginit -i po/plantilla.pot -o po/de.po --no-translator
	# francés
	#msginit -i po/plantilla.pot -o po/fr.po --no-translator
	# italiano
	#msginit -i po/plantilla.pot -o po/it.po --no-translator
	# catalan es_CA
	#msginit -i po/plantilla.pot -o po/es_CA.po --no-translator
	# portugues
	msginit -i po/plantilla.pot -o po/pt_PT.po --no-translator
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

