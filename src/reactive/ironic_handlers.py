from __future__ import absolute_import

import charms.reactive as reactive
import charmhelpers.core.hookenv as hookenv

import charms_openstack.charm as charm
import charm.openstack.ironic.ironic as ironic  # noqa


# Use the charms.openstack defaults for common states and hooks
charm.use_defaults(
    'charm.installed',
    'amqp.connected',
    'shared-db.connected',
    'identity-service.available',  # enables SSL support
    'config.changed',
    'update-status',
    'upgrade-charm',
    'certificates.available',
    'cluster.available')


@reactive.when('shared-db.available')
@reactive.when('identity-service.available')
@reactive.when('amqp.available')
def render(*args):
    hookenv.log("about to call the render_configs with {}".format(args))
    with charm.provide_charm_instance() as ironic_charm:
        ironic_charm.render_with_interfaces(
            charm.optional_interfaces(args))
        ironic_charm.configure_ssl()
        ironic_charm.assess_status()
    reactive.set_state('config.complete')


@reactive.when('identity-service.connected')
def setup_endpoint(keystone):
    with charm.provide_charm_instance() as ironic_charm:
        keystone.register_endpoints(
            ironic_charm.service_type,
            ironic_charm.region,
            ironic_charm.public_url,
            ironic_charm.internal_url,
            ironic_charm.admin_url)
        ironic_charm.assess_status()


@reactive.when('ironic-api.available')
@reactive.when('config.complete')
def ironic_api_relation_joined(ironic_api):
    with charm.provide_charm_instance() as ironic_charm:
        ironic_charm.set_ironic_api_info(ironic_api)


@reactive.when('config.complete')
@reactive.when_not('db.synced')
def run_db_migration():
    with charm.provide_charm_instance() as ironic_charm:
        ironic_charm.db_sync()
        ironic_charm.restart_all()
        ironic_charm.assess_status()
    reactive.set_state('db.synced')


@reactive.when('ha.connected')
@reactive.when_not('ha.available')
def cluster_connected(hacluster):
    with charm.provide_charm_instance() as ironic_charm:
        ironic_charm.configure_ha_resources(hacluster)
        ironic_charm.assess_status()
