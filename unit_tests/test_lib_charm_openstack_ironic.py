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

import charms_openstack.test_utils as test_utils

from charm.openstack.ironic import ironic


class TestIronicCharmConfigProperties(test_utils.PatchHelper):

    def setUp(self):
        super().setUp()
        self.patch_release(ironic.IronicAPICharm.release)

    def test_deployment_interface_ip(self):
        cls = mock.MagicMock()
        self.patch_object(ironic, 'ch_ip')
        ironic.deployment_interface_ip(cls)
        self.ch_ip.get_relation_ip.assert_called_with('deployment')

    def test_internal_interface_ip(self):
        cls = mock.MagicMock()
        self.patch_object(ironic, 'ch_ip')
        ironic.internal_interface_ip(cls)
        self.ch_ip.get_relation_ip.assert_called_with('internal')


class TestIronicCharm(test_utils.PatchHelper):

    def setUp(self):
        super().setUp()
        self.patch_release(ironic.IronicAPICharm.release)
        self.target = ironic.IronicAPICharm()

    def test_get_amqp_credentials(self):
        cfg_data = {
            "rabbit-user": "ironic",
            "rabbit-vhost": "openstack",
        }
        self.target.config = cfg_data
        result = self.target.get_amqp_credentials()
        self.assertEqual(result, ('ironic', 'openstack'))

    def test_get_database_setup(self):
        cfg_data = {
            "database-user": "ironic",
            "database": "ironicdb",
        }
        self.target.config = cfg_data
        result = self.target.get_database_setup()
        self.assertEqual(
            result,
            [{
                "database": cfg_data["database"],
                "username": cfg_data["database-user"]}])

    def test_set_ironic_api_info(self):
        self.patch_object(ironic.reactive.flags, 'is_flag_set')
        self.is_flag_set.return_value = True
        baremetal = mock.MagicMock()
        unit = mock.MagicMock()
        unit.relation.relation_id = "fake"
        baremetal.all_joined_units = [unit]
        relation_data = {"ironic-api-ready": True}
        self.target.set_ironic_api_info(baremetal)

        baremetal.set_baremetal_info.assert_called_with(
            "fake", relation_data)

        self.is_flag_set.return_value = False
        relation_data = {"ironic-api-ready": False}
        self.target.set_ironic_api_info(baremetal)

        baremetal.set_baremetal_info.assert_called_with(
            "fake", relation_data)
