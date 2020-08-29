# Copyright 2018 Cloudbase Solutions

from __future__ import absolute_import

import charms.reactive as reactive
import charmhelpers.core.hookenv as hookenv

import charms_openstack.charm as charm
import charm.openstack.ironic.ironic as ironic  # noqa

from charmhelpers.core.templating import render
import charmhelpers.contrib.network.ip as ch_ip
import charms_openstack.adapters as adapters


# Use the charms.openstack defaults for common states and hooks
charm.use_defaults(
    'charm.installed',
    'amqp.connected',
    'shared-db.connected',
    'identity-service.available',  # enables SSL support
    'config.changed',
    'update-status')


@reactive.when('shared-db.available')
@reactive.when('identity-service.available')
@reactive.when('amqp.available')
def render_stuff(*args):
    hookenv.log("about to call the render_configs with {}".format(args))
    with charm.provide_charm_instance() as ironic_charm:
        ironic_charm.render_with_interfaces(
            charm.optional_interfaces(args))
        ironic_charm.assess_status()
    reactive.set_state('config.complete')


@reactive.when('identity-service.connected')
def setup_endpoint(keystone):
    ironic.setup_endpoint(keystone)
    ironic.assess_status()


@reactive.when('config.complete')
@reactive.when_not('db.synced')
def run_db_migration():
    ironic.db_sync()
    ironic.restart_all()
    reactive.set_state('db.synced')
    ironic.assess_status()


@reactive.when('ha.connected')
def cluster_connected(hacluster):
    ironic.configure_ha_resources(hacluster)


@adapters.config_property
def deployment_interface_ip(self):
    return ch_ip.get_relation_ip("deployment")

@adapters.config_property
def internal_interface_ip(self):
    return ch_ip.get_relation_ip("internal")
