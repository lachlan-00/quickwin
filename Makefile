INSTALLPATH="/usr/share/quickwin"
INSTALLTEXT="quickwin is now installed"
UNINSTALLTEXT="quickwin has been removed"

install-req:
	@mkdir -p $(INSTALLPATH)
	@cp quickwin/* $(INSTALLPATH) -f
	@cp README $(INSTALLPATH) -f
	@cp AUTHORS $(INSTALLPATH) -f
	@cp LICENSE $(INSTALLPATH) -f
	@cp bin/quickwin /usr/bin/ -f
	@cp bin/quickwin3 /usr/bin/ -f
	@cp share/quickwin.png /usr/share/pixmaps -f
	@cp share/quickwin.desktop /usr/share/applications/ -f
	@chmod +x /usr/bin/quickwin
	@chmod +x /usr/bin/quickwin3
	@chmod +x /usr/share/quickwin/quickwin.py

install: install-req
	@echo $(INSTALLTEXT)

uninstall-req:
	@rm -rf $(INSTALLPATH)
	@rm /usr/share/pixmaps/quickwin.png
	@rm /usr/share/applications/quickwin.desktop
	@rm /usr/bin/quickwin

uninstall: uninstall-req
	@echo $(UNINSTALLTEXT)
