from plur_linux.recipes.pxe import pxe


def setup_pxe_uefi(session):
    pxe.setup_a8_pxe_uefi(session)


def setup_pxe(session):
    pxe.setup_a8_pxe(session)
