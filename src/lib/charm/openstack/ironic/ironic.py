from __future__ import absolute_import

import collections
import os

import charms_openstack.charm
import charms_openstack.adapters
import charms_openstack.ip as os_ip
import charmhelpers.contrib.network.ip as ch_ip
import charms_openstack.adapters as adapters

from charms import reactive


PACKAGES = [
    'ironic-api',
    'python3-mysqldb',
    'python3-ironicclient']

IRONIC_DIR = "/etc/ironic/"
IRONIC_CONF = os.path.join(IRONIC_DIR, "ironic.conf")

OPENSTACK_RELEASE_KEY = 'ironic-charm.openstack-release-version'


# select the default release function
charms_openstack.charm.use_defaults('charm.default-select-release')


@adapters.config_property
def deployment_interface_ip(cls):
    return ch_ip.get_relation_ip("deployment")


@adapters.config_property
def internal_interface_ip(cls):
    return ch_ip.get_relation_ip("internal")


class IronicAPICharm(charms_openstack.charm.HAOpenStackCharm):

    abstract_class = False
    release = 'train'
    name = 'ironic'
    python_version = 3
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
    services = ['ironic-api', ]
    sync_cmd = ['ironic-dbsync', 'upgrade']

    required_relations = [
        'shared-db', 'amqp', 'identity-service']

    restart_map = {
        IRONIC_CONF: services,
    }

    ha_resources = ['vips', 'haproxy']

    # Package for release version detection
    release_pkg = 'ironic-common'

    # Package codename map for ironic-common
    package_codenames = {
        'ironic-common': collections.OrderedDict([
            ('13', 'train'),
            ('15', 'ussuri'),
        ]),
    }

    group = "ironic"

    def __init__(self, **kw):
        super().__init__(**kw)

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

    def set_ironic_api_info(self, baremetal):
        is_ready = reactive.flags.is_flag_set('config.complete')
        relation_data = {"ironic-api-ready": is_ready}
        for unit in baremetal.all_joined_units:
            baremetal.set_baremetal_info(
                unit.relation.relation_id,
                relation_data)
