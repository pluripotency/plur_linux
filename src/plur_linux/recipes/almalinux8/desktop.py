from plur_linux.recipes.desktop import redhat


def install_xrdp(session):
    redhat.dict_desktop['almalinux8']['xrdp'](session)


def install_gui(session):
    redhat.dict_desktop['almalinux8']['desktop'](session)


def install_vbox_additions_libs(session):
    redhat.dict_desktop['almalinux8']['vbox'](session)
