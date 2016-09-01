
..
    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

==============
Ironic plugin
==============

https://blueprints.launchpad.net/searchlight/+spec/ironic-plugin

This spec is proposed to add ironic plugin for Searchlight. Ironic is OpenStack
baremetal service. Plugin should support these baremetal resourses: nodes
(OS::Ironic::Node), ports (OS::Ironic::Port) and chassis (OS::Ironic::Chassis).

Problem Description
===================

Notifications about baremetal node state changes (power, provisioning) and
create, update and delete of resources are proposed to ironic ([1]_, [2]_).
Because information about node in the database can be changed quickly during
deployment specification [2]_ provides ways to limits flow of notifications.
Using of Searchlight API with ironic plugin can reduce load on ironic API
from periodical polling tasks.

Proposed Change
===============

1. Searchlight listener should be changed because ironic can use any
notifications message priority, not only INFO ([1]_). For possibility of use
this feature and backward compatibility new configuration option (list type)
``additional_priorities`` will be added to ``listener`` group. Allowed
values are "audit", "debug", "warn", "error", "critical" and "sample". Default
value is not set (no additional priorities).

2. Plugin with indexers and notification handlers for ironic nodes, ports and
chassis shoud be implemented.

3. Custom Searchlight config should be used with ironic because ironic uses
own hardcoded ``ironic_versioned_notifications`` topic ([3]_).

Alternatives
------------

None

References
==========
.. [1] http://specs.openstack.org/openstack/ironic-specs/specs/approved/notifications.html
.. [2] https://review.openstack.org/#/c/347242
.. [3] http://docs.openstack.org/developer/ironic/dev/notifications.html
