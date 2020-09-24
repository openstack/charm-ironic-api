# Overview

This charm provides the Ironic baremetal API service for an OpenStack cloud, starting with Train. To get a fully functional Ironic deployment, you will also need to deploy the ```ironic-conductor``` and the ```neutron-api-plugin-ironic``` charms.
 
# Usage

## Configuration

This charm requires no special configuration, outside of what is already required/recommended for any other OpenStack API service charm.

## Deployment

To deploy (partial deployment only):

```bash
juju deploy ironic-api

juju add-relation ironic-api keystone
juju add-relation ironic-api rabbitmq-server
juju add-relation ironic-api mysql
```

The following interface is provided by this charm:

  * ironic-api - Used to signal readiness of the Ironic API to OpenStack services.

