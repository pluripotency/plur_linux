from recipes.desktop import redhat


def install_xrdp(session):
    redhat.dict_desktop['almalinux9']['xrdp'](session)


def install_gui(session):
    redhat.dict_desktop['almalinux9']['desktop'](session)


def install_vbox_additions_libs(session):
    redhat.dict_desktop['almalinux9']['vbox'](session)
