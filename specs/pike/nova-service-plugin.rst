..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===================
Nova service plugin
===================

https://blueprints.launchpad.net/searchlight/+spec/nova-service-plugin

This spec is proposed to support nova service plugin (OS::Nova::Service,
note that OS::Nova::Service doesn't exist in heat resource type same as the
hypervisor plugin, and it is an admin-only resource type), and versioned
notifications are supported for services in nova [0], it would be a nice
additional plugin for Searchlight.

Problem Description
===================

A service[1] takes a manager and enables rpc by listening to queues based on
topic. It also periodically runs tasks on the manager and reports its state
to the database services table. So in cloud with large amount of compute
nodes, there will be a pretty large number of services (typically one service
each compute node, and four services each controller node). The list or search
services (you can use command `nova service-list` to get the whole list or
filter the result by host or binary) may get slow using the native nova API.
And the versioned notifications for hypervisor [2] refers to the service id.
In future implementation for notification in hypervisor plugin [3] we may want
to fetch the service details for hypervisor create or update action by the
service id.

Proposed Change
===============

1. Support index services through nova API.
2. Support versioned notifications.

Alternatives
------------

None

References
==========

[0] https://github.com/openstack/nova/blob/master/nova/objects/service.py#L309-L315
[1] http://docs.openstack.org/developer/nova/services.html#the-nova-service-module
[2] https://review.openstack.org/#/c/315312/11/nova/notifications/objects/compute_node.py
[3] https://github.com/openstack/searchlight/blob/master/searchlight/elasticsearch/plugins/nova/notification_handler.py#L107
