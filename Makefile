EMAIL="makiolo@gmail.com"
PREFIX=/usr
REV_ACTUAL=${shell bzr revno}
REV_NEXT=$(shell python -c "print $(REV_ACTUAL)+1")
VERSION_ACTUAL=${shell python doc/VERSION $(REV_ACTUAL)}
VERSION_NEXT=${shell python doc/VERSION $(REV_NEXT)}
ARCH=${shell uname -m}
INSTALL_PKG=apt-get install

all: compile

ayuda: help
help:
	@echo
	@echo ==================================================================
	@echo "step 1: \"make\""
	@echo "step 2: \"sudo make install\""
	@echo ""
	@echo "Other options:"
	@echo ""
	@echo "Type: \"sudo make install_auto\" for install automatically"
	@echo ""
	@echo "Type: \"sudo make uninstall\" for uninstall"
	@echo "Type: \"sudo make purge\" for full uninstall (covers, disc-art ...)"
	@echo ==================================================================

runEN:
	LANGUAGE=en wiithon

install_auto: dependencias compile install permisos

dependencias:
	$(INSTALL_PKG) libc6 libc6-dev intltool imagemagick python-gtk2 python-glade2 python-sexy python-sqlalchemy gnome-icon-theme g++
	-@$(INSTALL_PKG) libc6-dev-i386 libc6-i386
	@echo "=================================================================="
	@echo "Install depends OK"
	@echo "=================================================================="

fuzzyies:
	-@grep -n fuzzy po/*.po

da_DK: po/locale/da_DK/LC_MESSAGES/wiithon.mo
fi_FI: po/locale/fi_FI/LC_MESSAGES/wiithon.mo
tr_TR: po/locale/tr_TR/LC_MESSAGES/wiithon.mo
ru_RU: po/locale/ru_RU/LC_MESSAGES/wiithon.mo
ko_KR: po/locale/ko_KR/LC_MESSAGES/wiithon.mo
it: po/locale/it/LC_MESSAGES/wiithon.mo
sv_SE: po/locale/sv_SE/LC_MESSAGES/wiithon.mo
es: po/locale/es/LC_MESSAGES/wiithon.mo
pt_PT: po/locale/pt_PT/LC_MESSAGES/wiithon.mo
da_DK: po/locale/en/LC_MESSAGES/wiithon.mo
en: po/locale/nl_NL/LC_MESSAGES/wiithon.mo
nb_NO: po/locale/nb_NO/LC_MESSAGES/wiithon.mo
ja_JP: po/locale/ja_JP/LC_MESSAGES/wiithon.mo
fr: po/locale/fr/LC_MESSAGES/wiithon.mo
de: po/locale/de/LC_MESSAGES/wiithon.mo
pt_BR: po/locale/pt_BR/LC_MESSAGES/wiithon.mo
es_CA: po/locale/es_CA/LC_MESSAGES/wiithon.mo

lang: lang_enable lang_disable
lang_enable: it es en fr de pt_BR es_CA
lang_disable: da_DK fi_FI tr_TR ru_RU ko_KR sv_SE pt_PT da_DK nb_NO ja_JP

compile: lang unrar-nonfree/wiithon_unrar libwbfs_binding/wiithon_wrapper gen_rev_now
	@echo "=================================================================="
	@echo "Compile OK"
	@echo "=================================================================="

making_directories:
	@mkdir -p $(DESTDIR)/usr/share/pixmaps
	@mkdir -p $(DESTDIR)/usr/share/applications
	@mkdir -p $(DESTDIR)/usr/share/doc/wiithon
	@mkdir -p $(DESTDIR)$(PREFIX)/share/wiithon
	@mkdir -p $(DESTDIR)$(PREFIX)/share/wiithon/recursos/glade
	@mkdir -p $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes
	@mkdir -p $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/accesorio
	@mkdir -p $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/caratulas
	@mkdir -p $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/discos
	
recicled_old_wiithon: making_directories
	-@mv -f ~/.wiithon/caratulas/*.png $(PREFIX)/share/wiithon/recursos/imagenes/caratulas
	-@mv -f ~/.wiithon/discos/*.png $(PREFIX)/share/wiithon/recursos/imagenes/discos
	-@mv -f /usr/local/share/wiithon/recursos/imagenes/caratulas/*.png $(PREFIX)/share/wiithon/recursos/imagenes/caratulas
	-@mv -f /usr/local/share/wiithon/recursos/imagenes/discos/*.png $(PREFIX)/share/wiithon/recursos/imagenes/discos
	
copy_archives: making_directories

	cp libwbfs_binding/wiithon_wrapper $(DESTDIR)$(PREFIX)/games/
	cp unrar-nonfree/wiithon_unrar $(DESTDIR)$(PREFIX)/games/
	
	cp *.py $(DESTDIR)$(PREFIX)/share/wiithon

	cp wiithon_autodetectar.sh $(DESTDIR)$(PREFIX)/share/wiithon
	cp wiithon_autodetectar_lector.sh $(DESTDIR)$(PREFIX)/share/wiithon
	cp wiithon_autodetectar_fat32.sh $(DESTDIR)$(PREFIX)/share/wiithon

	cp recursos/icons/wiithon.png $(DESTDIR)/usr/share/pixmaps
	cp recursos/icons/wiithon.svg $(DESTDIR)/usr/share/pixmaps
	cp recursos/icons/wiithon.xpm $(DESTDIR)/usr/share/pixmaps

	cp recursos/glade/*.ui $(DESTDIR)$(PREFIX)/share/wiithon/recursos/glade
	cp recursos/imagenes/*.png $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes
	cp recursos/imagenes/accesorio/*.jpg $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/accesorio
	
	cp recursos/caratulas_fix/*.png $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/caratulas
	cp recursos/discos_fix/*.png $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/discos
	
	cp doc/LICENCIA $(DESTDIR)/usr/share/doc/wiithon
	cp doc/VERSION $(DESTDIR)/usr/share/doc/wiithon
	cp doc/REVISION $(DESTDIR)/usr/share/doc/wiithon
	cp doc/TRANSLATORS $(DESTDIR)/usr/share/doc/wiithon
	
	cp wiithon_usuario.desktop $(DESTDIR)/usr/share/applications/
	cp -R po/locale/ $(DESTDIR)/usr/share/
	cp -R po/man/ $(DESTDIR)/usr/share/
	
	@echo "=================================================================="
	@echo "Copy archives OK"
	@echo "=================================================================="
	
set_permisses:
	chmod 755 $(DESTDIR)$(PREFIX)/share/wiithon/wiithon.py
	chmod 755 $(DESTDIR)$(PREFIX)/games/wiithon_wrapper
	chmod 755 $(DESTDIR)$(PREFIX)/games/wiithon_unrar
	chmod 755 $(DESTDIR)$(PREFIX)/share/wiithon/wiithon_autodetectar*.sh

	chmod 644 $(DESTDIR)$(PREFIX)/share/wiithon/recursos/glade/*.ui
	chmod 644 $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/*.png
	chmod 644 $(DESTDIR)/usr/share/applications/wiithon_usuario.desktop
	 
	chmod 777 $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/caratulas
	chmod 777 $(DESTDIR)$(PREFIX)/share/wiithon/recursos/imagenes/discos
	
	@echo "=================================================================="
	@echo "Permisses OK"
	@echo "=================================================================="

postinst: set_permisses
	-ln -sf $(DESTDIR)$(PREFIX)/share/wiithon/wiithon.py $(DESTDIR)$(PREFIX)/games/wiithon
	-ln -sf $(DESTDIR)$(PREFIX)/games/wiithon_wrapper $(DESTDIR)$(PREFIX)/share/wiithon/wiithon_wrapper
	-ln -sf $(DESTDIR)$(PREFIX)/games/wiithon_unrar $(DESTDIR)$(PREFIX)/share/wiithon/wiithon_unrar
	
	if [ -x /usr/bin/update-menus ] ; then update-menus ; fi
	
	@echo "=================================================================="
	@echo "If you want run witthon as normal user you must add it to 'disk' group."
	@echo "Type: \"sudo gpasswd -a <user> disk\" and restart your GNOME/KDE session."
	@echo "=================================================================="

install: recicled_old_wiithon clean_old_wiithon copy_archives postinst
	@echo "=================================================================="
	@echo "Wiithon Install OK"
	@echo "=================================================================="
	
permisos:
	gpasswd -a ${SUDO_USER} disk
	@echo "=================================================================="
	@echo "Restart GNOME / KDE for it has effect."
	@echo "=================================================================="

install4ppa: copy_archives
	@echo "=================================================================="
	@echo "Wiithon Install for PPA OK"
	@echo "=================================================================="

generate_changelog:
	@ln -sf $(shell pwd)/recursos/bazaar-plugins/gnulog.py ~/.bazaar/plugins/gnulog.py
	bzr log --log-format 'gnu' | sed -e "s/\(<.*@[^.]*\)>/\1\.fake>/g" > debian/changelog
	@$(RM) ~/.bazaar/plugins/gnulog.py

deb: generate_changelog
	debuild -b -uc -us -tc --lintian-opts -Ivi

deb_sign: deb
	gpg --armor --sign --detach-sig ../wiithon_$(VERSION_ACTUAL)_i386.deb

deb_and_install: deb_sign
	sudo dpkg -i ../wiithon_$(VERSION_ACTUAL)_i386.deb

deb_only_install:
	sudo dpkg -i ../wiithon_$(VERSION_ACTUAL)_i386.deb

ppa-inc: generate_changelog
	debuild -S -sd -k0xB8F0176A -I -i --lintian-opts -Ivi
	
ppa-upload: ppa-inc
	dput ppa:wii.sceners.linux/wiithon ../wiithon_$(VERSION_ACTUAL)_source.changes

clean_old_wiithon: 

	@echo "=================================================================="
	@echo "Ignore next errors"
	@echo "=================================================================="

	-@$(RM) -R ~/.wiithon/caratulas/
	-@$(RM) -R ~/.wiithon/discos/
	-@$(RM) ~/.wiithon/bdd/juegos.db
	-@$(RM) ~/.wiithon/bdd/wiithon1.*.db
	-@$(RM) ~/.wiithon/bdd/juegos.db
	-@$(RM) ~/.wiithon_acuerdo
	-@$(RM) /usr/local/share/wiithon/.acuerdo
	
	-@$(RM) /usr/bin/wiithon
	-@$(RM) /usr/bin/wiithon_autodetectar
	-@$(RM) /usr/bin/wiithon_autodetectar_lector
	-@$(RM) /usr/bin/wbfs
	
	-@$(RM) /usr/local/bin/wiithon_autodetectar
	-@$(RM) /usr/local/bin/wiithon_autodetectar_lector
	-@$(RM) /usr/local/bin/wbfs
	-@$(RM) /usr/local/share/wiithon/wbfs
	
	-@$(RM) /usr/local/share/wiithon/glade_wrapper.py

	-@$(RM) /usr/local/share/wiithon/recursos/glade/*.xml
	-@$(RM) /usr/local/share/wiithon/recursos/glade/*.glade
	
	-@$(RM) /usr/local/share/wiithon/wiithon
	-@$(RM) /usr/local/share/wiithon/wiithon_autodetectar
	-@$(RM) /usr/local/share/wiithon/wiithon_autodetectar_lector

	-@gconftool --recursive-unset /apps/nautilus-actions/configurations
	-@$(RM) /usr/share/gconf/schemas/wiithon*.schemas
	
	-@$(RM) /usr/share/applications/wiithon.desktop
	-@$(RM) /usr/share/applications/wiithon_root.desktop
	
	-@$(RM) /usr/local/share/wiithon/HOME.conf

	-@$(RM) /usr/local/lib/libwbfs.so
	-@$(RM) /usr/lib/libwbfs.so
	-@$(RM) /usr/lib32/libwbfs.so
	
	-@$(RM) /usr/local/share/wiithon/*.py
	-@$(RM) /usr/local/share/wiithon/wiithon_wrapper
	-@$(RM) /usr/local/share/wiithon/unrar
	-@$(RM) /usr/local/share/wiithon/*.sh
	-@$(RM) /usr/local/share/wiithon/recursos/glade/*.ui
	-@$(RM) /usr/local/share/wiithon/recursos/imagenes/*.png
	-@$(RM) /usr/local/share/wiithon/recursos/imagenes/accesorio/*.jpg
	-@rmdir /usr/local/share/wiithon/recursos/imagenes/accesorio/

	-@$(RM) /usr/local/share/wiithon/*.pyc
	
	-@$(RM) /usr/local/share/wiithon/recursos/imagenes/caratulas/*.png
	-@$(RM) /usr/local/share/wiithon/recursos/imagenes/discos/*.png
	-@rmdir /usr/local/share/wiithon/recursos/imagenes/caratulas
	-@rmdir /usr/local/share/wiithon/recursos/imagenes/discos
	-@rmdir /usr/local/share/wiithon/recursos/imagenes
	-@rmdir /usr/local/share/wiithon/recursos/glade
	-@rmdir /usr/local/share/wiithon/recursos
	-@rmdir /usr/local/share/wiithon
	
	@echo "=================================================================="
	@echo "Clean old installs"
	@echo "=================================================================="

delete_archives_installation:
	-$(RM) $(PREFIX)/games/wiithon_wrapper
	-$(RM) $(PREFIX)/games/wiithon_unrar
	-$(RM) $(PREFIX)/share/wiithon/*.py
	-$(RM) $(PREFIX)/share/wiithon/*.pyc
	-$(RM) $(PREFIX)/share/wiithon/*.sh
	-$(RM) $(PREFIX)/share/wiithon/recursos/glade/*.ui
	-$(RM) $(PREFIX)/share/wiithon/recursos/imagenes/*.png
	-$(RM) $(PREFIX)/share/wiithon/recursos/imagenes/accesorio/*.jpg
	-rmdir $(PREFIX)/share/wiithon/recursos/imagenes/accesorio/
	-rmdir $(PREFIX)/share/wiithon/recursos/glade/
	
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
	
	-$(RM) /usr/share/man/man1/wiithon.1.gz
	-$(RM) /usr/share/man/es/man1/wiithon.1.gz

	-$(RM) /usr/share/applications/wiithon_usuario.desktop
	
	-$(RM) /usr/share/pixmaps/wiithon.png
	-$(RM) /usr/share/pixmaps/wiithon.svg
	-$(RM) /usr/share/pixmaps/wiithon.xpm
	
postrm:
	-$(RM) /usr/share/doc/wiithon/*
	-rmdir /usr/share/doc/wiithon

	-$(RM) $(PREFIX)/games/wiithon
	-$(RM) $(PREFIX)/share/wiithon/wiithon_wrapper
	-$(RM) $(PREFIX)/share/wiithon/wiithon_unrar
	
uninstall: clean_old_wiithon delete_archives_installation postrm
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
	-rmdir $(PREFIX)/share/wiithon/recursos
	-rmdir $(PREFIX)/share/wiithon
	@echo "=================================================================="
	@echo "Uninstall OK & all clean (purge covers & disc-art ...)"
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

unrar-nonfree/wiithon_unrar: unrar-nonfree/*.cpp unrar-nonfree/*.hpp
	$(MAKE) -C unrar-nonfree

gen_rev_now:
ifeq ($(shell if [ -x .bzr ]; then echo "y"; else echo "n"; fi), y)
	echo $(REV_ACTUAL) > doc/REVISION
endif

gen_rev_next:
ifeq ($(shell if [ -x .bzr ]; then echo "y"; else echo "n"; fi), y)
	echo $(REV_NEXT) > doc/REVISION
endif

commit: clean compile gen_rev_next
	bzr commit --file="COMMIT" && echo "" > COMMIT

log:
	bzr log --forward --short

# TRADUCCION
# http://faq.pygtk.org/index.py?req=show&file=faq22.002.htp
# http://misdocumentos.net/wiki/linux/locales
# Generar plantilla POT
# --no-location
# --omit-header
# --sort-output
po/plantilla.pot: recursos/glade/*.ui.h *.py
	@echo "*** GETTEXT *** Extract strings from code"
	xgettext --language=Python --no-wrap --sort-by-file --keyword=_ --keyword=N_ --from-code=utf-8 --package-name="wiithon" --package-version="$(VERSION_NEXT)" --msgid-bugs-address=$(EMAIL) -o po/plantilla.pot $^ 2> /dev/null
	@cat po/plantilla.pot | grep -v POT-Creation-Date | grep -v PO-Revision-Date > po/plantilla2.pot
	@mv po/plantilla2.pot po/plantilla.pot
	@$(RM) po/plantilla2.pot

# extraer strings del glade
recursos/glade/%.ui.h: recursos/glade/%.ui
	intltool-extract --type="gettext/glade" $<

# generar PO, si ya existe, mezcla o sincroniza
# He desactivado fuzzy con -N
# tambien he quitado los comentarios con --no-location
# --no-location
po/%.po: po/plantilla.pot
	msgmerge -U --no-wrap --sort-by-file $@ $(filter %.pot, $^)
	@touch $@

# generar MO
# FIXME: Crea po/locale/pt_BR/LC_MESSAGES/wiithon
# debería crear: po/locale/pt_BR/LC_MESSAGES/
# lo parcheo con el rmdir
po/locale/%/LC_MESSAGES/wiithon.mo: po/%.po
	@mkdir -p $(basename $@)
	msgfmt $< -o $@
	@rmdir $(basename $@)

first_time:
	@echo ""
#
# Only need first time
#
ppa-new: generate_changelog
	debuild -S -sa -k0xB8F0176A -I -i --lintian-opts -Ivi
	mv ../wiithon_$(VERSION_ACTUAL).tar.gz ../wiithon_$(VERSION_ACTUAL).orig.tar.gz
	debuild -S -sk -k0xB8F0176A -I -i --lintian-opts -Ivi

ppa-upload-new:
	dput ppa:wii.sceners.linux/wiithon ../wiithon_$(VERSION_ACTUAL)_source.changes

#
# Only for new languages
# generar PO VACIO a partir de plantilla POT
#initPO: po/plantilla.pot
#	@echo "*** GETTEXT *** Creando PO"
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
	#msginit -i po/plantilla.pot -o po/pt_PT.po --no-translator
	# danish da_DK
	#msginit -i po/plantilla.pot -o po/da_DK.po --no-translator
	# dutch nl_NL
	#msginit -i po/plantilla.pot -o po/nl_NL.po --no-translator
	# finnish fi_FI
	#msginit -i po/plantilla.pot -o po/fi_FI.po --no-translator
	# japanese ja_JP
	#msginit -i po/plantilla.pot -o po/ja_JP.po --no-translator
	# korean ko_KR
	#msginit -i po/plantilla.pot -o po/ko_KR.po --no-translator
	# norwegian nb_NO
	#msginit -i po/plantilla.pot -o po/nb_NO.po --no-translator
	# russian ru_RU
	#msginit -i po/plantilla.pot -o po/ru_RU.po --no-translator
	# swedish sv_SE
	#msginit -i po/plantilla.pot -o po/sv_SE.po --no-translator
	# turkish tr_TR
	#msginit -i po/plantilla.pot -o po/tr_TR.po --no-translator
