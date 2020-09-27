# Copyright 2020 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock

from charm.openstack.ironic import ironic
import reactive.ironic_handlers as handlers

import charms_openstack.test_utils as test_utils


class TestRegisteredHooks(test_utils.TestRegisteredHooks):

    def test_hooks(self):
        defaults = [
            'charm.installed',
            'amqp.connected',
            'shared-db.connected',
            'identity-service.available',
            'config.changed',
            'update-status',
            'upgrade-charm',
            'certificates.available',
        ]
        hook_set = {
            'when': {
                'render': ('shared-db.available',
                           'identity-service.available',
                           'amqp.available',),
                'run_db_migration': ('config.complete',),
                'cluster_connected': ('ha.connected',),
                'setup_endpoint': ('identity-service.connected',),
                'ironic_api_relation_joined': (
                    'ironic-api.available',
                    'config.complete',
                ),
            },
            'when_not': {
                'run_db_migration': (
                    'db.synced',),
                'cluster_connected': ('ha.available',),
            },
            'hook': {
                'upgrade_charm': ('upgrade-charm',),
            },
        }
        # test that the hooks were registered via the
        # reactive.ironic_handlers
        self.registered_hooks_test_helper(handlers, hook_set, defaults)


class TestIronicHandlers(test_utils.PatchHelper):

    def setUp(self):
        super().setUp()
        self.patch_release(ironic.IronicAPICharm.release)
        self.ironic_charm = mock.MagicMock()
        self.patch_object(handlers.charm, 'provide_charm_instance',
                          new=mock.MagicMock())
        self.provide_charm_instance().__enter__.return_value = \
            self.ironic_charm
        self.provide_charm_instance().__exit__.return_value = None

    def test_setup_endpoint_connection(self):
        keystone = mock.MagicMock()
        handlers.setup_endpoint(keystone)
        keystone.register_endpoints.assert_called_once_with(
            self.ironic_charm.service_type,
            self.ironic_charm.region,
            self.ironic_charm.public_url,
            self.ironic_charm.internal_url,
            self.ironic_charm.admin_url)
        self.ironic_charm.assess_status.assert_called_once_with()

    def test_ironic_api_relation_joined(self):
        ironic_api = mock.MagicMock()
        handlers.ironic_api_relation_joined(ironic_api)
        self.ironic_charm.set_ironic_api_info.assert_called_once_with(
            ironic_api)

    def test_render(self):
        self.patch('charms.reactive.set_state', 'set_state')
        self.patch_object(handlers.charm, 'optional_interfaces')
        self.optional_interfaces.return_value = ('fake', 'interface', 'list')
        handlers.render('arg1', 'arg2')
        self.ironic_charm.render_with_interfaces.assert_called_once_with(
            ('fake', 'interface', 'list'))
        self.optional_interfaces.assert_called_once_with(
            ('arg1', 'arg2'))
        self.ironic_charm.configure_ssl.assert_called_once_with()
        self.ironic_charm.assess_status.assert_called_once_with()
        self.set_state.assert_called_once_with('config.complete')

    def test_run_db_migration(self):
        self.patch('charms.reactive.set_state', 'set_state')
        handlers.run_db_migration()
        self.ironic_charm.db_sync.assert_called_once_with()
        self.ironic_charm.restart_all.assert_called_once_with()
        self.set_state.assert_called_once_with('db.synced')
        self.ironic_charm.assess_status.assert_called_once_with()

    def test_cluster_connected(self):
        hacluster = mock.MagicMock()
        handlers.cluster_connected(hacluster)
        self.ironic_charm.configure_ha_resources.assert_called_once_with(
            hacluster)
        self.ironic_charm.assess_status.assert_called_once_with()
