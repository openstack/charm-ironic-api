import os
import shutil

from charmhelpers.core.templating import render
from charmhelpers.core.host import get_distrib_codename
import charmhelpers.fetch as fetch

_IRONIC_USER = "ironic"
_IRONIC_GROUP = "ironic"


class PXEBootBase(object):
    
    TFTP_ROOT = "/tftpboot"
    HTTP_ROOT = "/httpboot"
    IPXE_BOOT = os.path.join(HTTP_ROOT, "boot.ipxe")
    GRUB_DIR = os.path.join(TFTP_ROOT, "grub")
    MAP_FILE = os.path.join(TFTP_ROOT, "map-file")
    TFTP_CONFIG = "/etc/default/tftpd-hpa"

    # This is a file map of source to destination. The destination is
    # relative to self.TFTP_ROOT
    FILE_MAP = {
        "/usr/lib/PXELINUX/pxelinux.0": "pxelinux.0",
        "/usr/lib/syslinux/modules/bios/chain.c32": "chain.c32",
        "/usr/lib/syslinux/modules/bios/ldlinux.c32": "ldlinux.c32",
        "/usr/lib/grub/x86_64-efi-signed/grubnetx64.efi.signed": "grubx64.efi",
        "/usr/lib/shim/shim.efi.signed": "bootx64.efi",
        "/usr/lib/ipxe/undionly.kpxe": "undionly.kpxe",
        "/usr/lib/ipxe/ipxe.efi": "ipxe.efi",
    }

    TFTP_PACKAGES = ["tftpd-hpa"]
    PACKAGES = [
        'syslinux-common',
        'pxelinux',
        'grub-efi-amd64-signed',
        'shim-signed',
        'ipxe',
    ]

    def __init__(self, charm_config):
        self._config = charm_config

    def _copy_resources(self):
        self._ensure_folders()
        for f in self.FILE_MAP:
            if os.path.isfile(f) is False:
                raise ValueError(
                    "Missing required file %s. Package not installes?" % f)
            shutil.copy(
                f, os.path.join(self.TFTP_ROOT, self.FILE_MAP[f]),
                follow_symlinks=True)
        self._recursive_chown(
            self.TFTP_ROOT, user=_IRONIC_USER, group=_IRONIC_GROUP)

    def _recursive_chown(self, path, user=None, group=None):
        for root, _, files in os.walk(path):
            shutil.chown(root, user=user, group=group)
            for f in files:
                shutil.chown(
                    os.path.join(root, f), user=user, group=group)

    def _ensure_folders(self):
        if os.path.isdir(self.TFTP_ROOT) is False:
            os.makedirs(self.TFTP_ROOT)
        
        if os.path.isdir(self.HTTP_ROOT) is False:
            os.makedirs(self.HTTP_ROOT)

        if os.path.isdir(self.IPXE_BOOT) is False:
            os.makedirs(self.IPXE_BOOT)

        if os.path.isdir(self.GRUB_DIR) is False:
            os.makedirs(self.GRUB_DIR)
        
        self._recursive_chown(
            self.TFTP_ROOT, user=_IRONIC_USER, group=_IRONIC_GROUP)
        self._recursive_chown(
            self.HTTP_ROOT, user=_IRONIC_USER, group=_IRONIC_GROUP)

    def _create_file_map(self):
        self._ensure_folders()
        render(source='tftp-file-map',
           target=self.MAP_FILE,
           owner=_IRONIC_USER,
           perms=0o664,
           context={})
    
    def _create_grub_cfg(self):
        self._ensure_folders()
        render(source='grub-efi',
           target=os.path.join(self.GRUB_DIR, "grub.cfg"),
           owner="root",
           perms=0o644,
           context={
               "tftpboot": self.TFTP_ROOT,
           })

    def _create_tftp_config(self):
        cfg_dir = os.path.dirname(self.TFTP_CONFIG)
        if os.path.isdir(cfg_dir) is False:
            raise Exception("Could not find %s" % cfg_dir)
        render(source='tftpd-hpa',
           target=self.TFTP_CONFIG,
           owner="root",
           perms=0o644,
           context={
               "tftpboot": self.TFTP_ROOT,
               "max_tftp_block_size": self._config.get(
                   "max_tftp_block_size", 0)
           })
    
    def configure_resources(self):
        # On Ubuntu 20.04, if IPv6 is not available on the system,
        # the tftp-hpa package fails to install properly. We create the
        # config beforehand, forcing IPv4.
        self._create_tftp_config()
        fetch.apt_install(self.TFTP_PACKAGES, fatal=True)
        fetch.apt_install(self.PACKAGES, fatal=True)
        self._copy_resources()
        self._create_file_map()
        self._create_grub_cfg()


class PXEBootBionic(PXEBootBase):

    # This is a file map of source to destination. The destination is
    # relative to self.TFTP_ROOT
    FILE_MAP = {
        "/usr/lib/PXELINUX/pxelinux.0": "pxelinux.0",
        "/usr/lib/syslinux/modules/bios/chain.c32": "chain.c32",
        "/usr/lib/syslinux/modules/bios/ldlinux.c32": "ldlinux.c32",
        "/usr/lib/grub/x86_64-efi-signed/grubnetx64.efi.signed": "grubx64.efi",
        "/usr/lib/shim/shimx64.efi.signed": "bootx64.efi",
        "/usr/lib/ipxe/undionly.kpxe": "undionly.kpxe",
        "/usr/lib/ipxe/ipxe.efi": "ipxe.efi",
    }


def get_pxe_config_class(charm_config):
    # In the future, we may need to make slight adjustments to package
    # names and/or configuration files, based on the version of Ubuntu
    # we are installing on. This function serves as a factory which will
    # return an instance of the proper class to the charm. For now we only
    # have one class.
    series = get_distrib_codename()
    if series == "bionic":
        return PXEBootBionic(charm_config)
    return PXEBootBase(charm_config)
