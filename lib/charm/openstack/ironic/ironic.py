# Copyright 2020 Cloudbase Solutions

from __future__ import absolute_import

import collections
import os

import charms_openstack.charm
import charms_openstack.adapters
import charms_openstack.ip as os_ip

import charm.openstack.ironic.controller_utils as controller_utils

PACKAGES = [
    'ironic-api',
    'ironic-conductor',
    'python-mysqldb',
    'python3-dracclient',
    'python3-sushy',
    'python3-ironicclient',
    'python3-scciclient',
    'shellinabox',
    'openssl',
    'socat',
    'open-iscsi',
    'qemu-utils',
    'ipmitool']

IRONIC_DIR = "/etc/ironic/"
IRONIC_CONF = os.path.join(IRONIC_DIR, "ironic.conf")
ROOTWRAP_CONF = os.path.join(IRONIC_DIR, "rootwrap.conf")
FILTERS_DIR = os.path.join(IRONIC_DIR, "rootwrap.d")
IRONIC_LIB_FILTERS = os.path.join(
    FILTERS_DIR, "ironic-lib.filters")
IRONIC_UTILS_FILTERS = os.path.join(
    FILTERS_DIR, "ironic-utils.filters")
TFTP_CONF = "/etc/default/tftpd-hpa"

OPENSTACK_RELEASE_KEY = 'ironic-charm.openstack-release-version'


# select the default release function
charms_openstack.charm.use_defaults('charm.default-select-release')


def db_sync_done():
    return IronicAPICharm.singleton.db_sync_done()


def restart_all():
    IronicAPICharm.singleton.restart_all()


def db_sync():
    IronicAPICharm.singleton.db_sync()


def configure_ha_resources(hacluster):
    IronicAPICharm.singleton.configure_ha_resources(hacluster)


def assess_status():
    IronicAPICharm.singleton.assess_status()


def setup_endpoint(keystone):
    charm = IronicAPICharm.singleton
    public_ep = '{}'.format(charm.public_url)
    internal_ep = '{}'.format(charm.internal_url)
    admin_ep = '{}'.format(charm.admin_url)
    keystone.register_endpoints(charm.service_type,
                                charm.region,
                                public_ep,
                                internal_ep,
                                admin_ep)


class IronicAPICharm(charms_openstack.charm.HAOpenStackCharm):

    abstract_class = False
    release = 'train'
    name = 'ironic'
    packages = PACKAGES
    api_ports = {
        'ironic-api': {
            os_ip.PUBLIC: 6385,
            os_ip.ADMIN: 6385,
            os_ip.INTERNAL: 6385,
        }
    }
    service_type = 'ironic'
    default_service = 'ironic-api'
    services = ['ironic-api', 'ironic-conductor', 'tftpd-hpa']
    sync_cmd = ['ironic-dbsync', 'upgrade']

    required_relations = [
        'shared-db', 'amqp', 'identity-service']

    restart_map = {
        IRONIC_CONF: services,
        IRONIC_UTILS_FILTERS: services,
        IRONIC_LIB_FILTERS: services,
        ROOTWRAP_CONF: services,
    }

    ha_resources = ['vips', 'haproxy']

    # Package for release version detection
    release_pkg = 'ironic-common'

    # Package codename map for ironic-common
    package_codenames = {
        'ironic-common': collections.OrderedDict([
            ('14', 'train'),
            ('15', 'ussuri'),
        ]),
    }

    group = "ironic"

    def __init__(self, **kw):
        super().__init__(**kw)
        self.pxe_config = controller_utils.get_pxe_config_class(
            self.config)
        if self.config.get('use_ipxe', False):
            self.services.append('nginx')
        else:
            self.purge_packages.append("nginx")

    def get_amqp_credentials(self):
        """Provide the default amqp username and vhost as a tuple.

        :returns (username, host): two strings to send to the amqp provider.
        """
        return (self.config['rabbit-user'], self.config['rabbit-vhost'])

    def get_database_setup(self):
        return [
            dict(
                database=self.config['database'],
                username=self.config['database-user'], )
        ]

    def install(self):
        super().install()
        self.pxe_config.configure_resources()
    
    # def configue_tls(self, certificates_instance=None):
    #     # TODO(gsamfira): add tls support
    #     pass
