
..
    c) Copyright 2016, Huawei Technology.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

==============================
Add nova server groups plugin
==============================

https://blueprints.launchpad.net/searchlight/+spec/nova-server-groups-plugin

This Blueprint adds a plugin for Nova server groups (OS::Nova::Server_groups).

Problem Description
===================

Currently, in nova, there are no filter support fo os-server-groups API,
that means, when list server groups, all the existing server groups will
be listed. As server groups are very widely used feature in commercial
deployment, this will be problematic, especially for large scale Public
Cloud deployments. For example, in Deutsche Telekom OTC Public Cloud,
each tenant will have 10 server groups by default, when the number of
tenant grows, it will be a bottleneck to list and search for particular
server groups. And it will also be very user-friendly to let user
search for server groups with ``name``, ``policy`` or ``members`` which
is not yet provided by Nova.

Proposed Change
===============
Phase I:

Add a Nova server groups plugin to collect server groups data and
provide the ability to search server groups using ``name``, ``policy``,
``members``, ``id`` and ``metadata``.

Phase II:
Add new notification handler for server groups notifications once the
notification for server groups in nova has been added.

Alternatives
------------

Not add this plugin and we will lack the support for a widely used nova
feature.

References
==========
