VERSION=${shell cat VERSION.txt}
REVISION=${shell bzr revno}

all: build_wbfs
	@echo ==================================================================
	@echo Escribe "sudo make install" para instalar
	@echo Escribe "sudo make uninstall" para desinstalar
	@echo ==================================================================

install: uninstall
	
	@echo "=================================================================="	
	@echo "Se ha desinstalado, antes de instalar"
	@echo "=================================================================="

	cp wiithon /usr/local/bin
	cp wiithon_autodetectar /usr/local/bin
	cp wiithon_autodetectar_lector /usr/local/bin
	cp wbfs /usr/local/bin

	cp ./schemas/wiithon1.schemas /usr/share/gconf/schemas/
	cp ./schemas/wiithon2.schemas /usr/share/gconf/schemas/
	cp ./schemas/wiithon3.schemas /usr/share/gconf/schemas/
	cp ./schemas/wiithon4.schemas /usr/share/gconf/schemas/
	cp ./schemas/wiithon5.schemas /usr/share/gconf/schemas/
	cp ./schemas/wiithon6.schemas /usr/share/gconf/schemas/
	cp ./schemas/wiithon7.schemas /usr/share/gconf/schemas/
	cp ./schemas/wiithon8.schemas /usr/share/gconf/schemas/

	chmod 644 /usr/share/gconf/schemas/wiithon1.schemas
	chmod 644 /usr/share/gconf/schemas/wiithon2.schemas
	chmod 644 /usr/share/gconf/schemas/wiithon3.schemas
	chmod 644 /usr/share/gconf/schemas/wiithon4.schemas
	chmod 644 /usr/share/gconf/schemas/wiithon5.schemas
	chmod 644 /usr/share/gconf/schemas/wiithon6.schemas
	chmod 644 /usr/share/gconf/schemas/wiithon7.schemas
	chmod 644 /usr/share/gconf/schemas/wiithon8.schemas

	chmod 755 /usr/local/bin/wiithon
	chmod 755 /usr/local/bin/wiithon_autodetectar
	chmod 755 /usr/local/bin/wiithon_autodetectar_lector
	chmod 755 /usr/local/bin/wbfs

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
	
	-rm /usr/share/gconf/schemas/wiithon1.schemas
	-rm /usr/share/gconf/schemas/wiithon2.schemas
	-rm /usr/share/gconf/schemas/wiithon3.schemas
	-rm /usr/share/gconf/schemas/wiithon4.schemas
	-rm /usr/share/gconf/schemas/wiithon5.schemas
	-rm /usr/share/gconf/schemas/wiithon6.schemas
	-rm /usr/share/gconf/schemas/wiithon7.schemas
	-rm /usr/share/gconf/schemas/wiithon8.schemas
	
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

commit:
	bzr commit --file=COMMIT.txt && echo "" > COMMIT.txt

status:
	bzr status
