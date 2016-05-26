
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

==========================================
Support Nova microversions for Nova plugin
==========================================

https://blueprints.launchpad.net/searchlight/+spec/support-microversion-for-nova

This feature adds the support for Nova APIs with microversions. This would
support Searchlight providing the fields that are added in new microversions
of Nova APIs.

Problem Description
===================

Nova have deprecated v2.0 API and starting to remove the codes from tree.
Nova v2.1 API is designed with the microversion mechanism, that is, when
new data fields are added to one particular resource, the backward
compatibility is ensured by adding new microversions to related APIs [1]_.

For example, in [2]_, a new field ``description`` is added for servers,
it is used for users to make a simple string to describe their servers,
it would be very useful if we can also provide this field.

The changes that were made for each microversions could be found in [3]_.

Proposed Change
===============

Currently, when we initialize nova client, it is hard coded to use
``version=2``, this is bad in two ways:

1. The v2.0 nova API is deprecated and the code will be removed in
Newton [4]_.

2. It can not support microversions if it is hard coded.

In this BP, a new configure option ``compute_api_version`` will be
added in the configuration file. When we initialize nova client,
this config option will be used as the version of the API version.
The default value of this config option will be set to 2.1 in the
design of this BP and can be modified in the future according to
the changes in Nova API.

The supported data fields will be also updated according to the
provided microversion.

Alternatives
------------

Hard code the version to 2.1 as 2.0 will no longer be usable soon.
But the newly added data fields cannot be supported.

References
==========
.. [1] http://docs.openstack.org/developer/nova/api_microversions.html
.. [2] https://blueprints.launchpad.net/nova/+spec/user-settable-server-description
.. [3] http://git.openstack.org/cgit/openstack/nova/tree/nova/api/openstack/rest_api_version_history.rst
.. [4] https://blueprints.launchpad.net/nova/+spec/remove-legacy-v2-api-code

