
..
    c) Copyright 2015 Intel Corp.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

================================================
Notification Forwarding (to systems like Zaqar)
================================================

https://blueprints.launchpad.net/searchlight/+spec/notification-forwarding

This feature adds the ability to forward the Searchlight consumed indexing
notifications to external providers such as Zaqar[1] via a simple driver
interface. This would include the data enrichment that Searchlight provides on
top of the simple OpenStack notifications.

Problem Description
===================

There are a number of use cases by projects within OpenStack and outside of
OpenStack that need to know when OpenStack resources have been changed.
OpenStack provides a notification bus for receiving notifications published by
services, however there are a few limitations:

 * The OpenStack message bus is not typically directly exposed external
   consumers for security concerns.
 * The notifications often only contain a subset of the data about a particular
   resource, that is incomplete, not rich enough
 * The notification data does not look the same as the API results
 * The notification bus does not support all the message subscription semantics
   or mechanisms needed, like per-subscriber filtering or web sockets/hooks

Searchlight handles a number of the above problems and will continue to evolve
with OpenStack so that as notifications change / are enriched, it will evolve
with them. It does this by indexing the data from the OpenStack Services from
a variety of locations, including listening to notifications. It enriches the
data provided by the base notifications in a number of ways, which allows the
index to be used directly instead of the APIs [2]. The latter has the
additional advantage of reducing API call pressure on the various services.

Searchlight's enhanced searching capabilities [3] and performance [4] over
typical API responses are compelling; consequently it has been integrated
into horizon[5][6][7] and elsewhere.

Current Searchlight users will still need to use polling mechanisms to get
updated information from Searchlight. Many Searchlight consumers will need an
asynchronous way to stay informed of OpenStack Resource changes, such as
Availability and Status, instantly. They will also need a way that ensures
that the status updates they receive are coherent with the status of the
resources indexed into Searchlight.

1. A Horizon painpoint today, despite the availability of Searchlight and
its many benefits stemming from richer notifications and elastic search,
is that Horizon still needs to periodically poll Searchlight for updates.
(Where a notification is not handled by Searchlight, direct calls to
OpenStack service APIs are necessary. However, more and more OpenStack
projects are being integrated with Searchlight.) A notification
service that instead provides updates as they occur would be attractive.
Consider for instance a VM launch request. In the ideal scenario the
Horizon UI updates automatically to display the various stages in a
virtual machine launch as the transitions occur. Today
this is achieved in Horizon behind the scenes by frequently polling
Searchlight and/or other OpenStack API services.

2. Telco vendors, with their demanding service up time requirements and low
tolerance for service delays, also seek resource change notifications.
Typically they will have a management layer/application that seeks visibility
into resource updates. For example, CRUD of a user, VM, glance image,
flavor or other. For instance, the arrival of a new user may need to trigger
a workflow such as welcome messages, proferring services, and more.
Searchlight today detects such events and indexes them  but is unable to
push them to Telco management layer instantly, near real time.

3. For third party applications, often there is interest in  monitoring tools
that want insight into resources and their availability. These might span
flavors, instances, storage, images, and more and their status. Typically these
third party monitor systems will not have access to the OpenStack message bus
for security reasons. Consider for example, a content provider, who would like
to advertise to their customer base when a new movie is uploaded into Swift.
Yet another example may be triggering a upgrade action when a security patch
gets uploaded into Glance.


Proposed Change
===============

We propose that Searchlight add the ability to forward notifications.
Further, a forwarding infrastructure that supports a pipeline of forwarding
entities would provide maximum flexibility. For example, consider paste
pipeline,  within the order and entities as specified in the paste.ini file.
Note, in a sense Searchlight is the first element in notification pipeline,
the entity that takes as input the primary notifications from the OpenStack
message bus and enriches them in addition to indexing them.

A notification consumer might be Zaqar, the OpenStack messaging as a service
project or even simpler message forwarding mechanisms such as WebSockets,
or even a simple logger.

The notification consumer would need to be fast so as not to bog down
Searchlight's notification push subsystem. Further, rules of engagement
need to be agreed upon. For instance, if Searchlight is unable to contact
a registered notification consumer, what should it do? See bug [8].
Log the error and forget it? Should it re-try some pre-configured number
of times after some pre-configured wait interval between tries? Should
it hold the notifications till it can successfully send them? This latter
solution may be overly demanding on Searchlight especially when there are
multiple registered consumers.

Our solution strategy is to define a consumer-plugin for Searchlight for
each consumer. If Zaqar is the consumer, than a Zaqar plugin in Searchlight.
The intricacies of error handling on connection fail can be left to the Zaqar
plugin, any filtering of notifications to be actually transmitted from
Searchlight to Zaqar can further be handled there. Leaving the error handling
to the plugin makes sense because some consumers may care about lost
notifications while others may not. For example, a mail program displays
messages as they arrive, but occassionally the VPN goes down, or there is no
wireless connectity or other problem. The mail reader then may on reconnect
just issue a mail-synch. It is in this vein that we leave notification
handling to the plugin and its associated consumer and its end-user  API.
Essentially re-try behavior, re-synch behavior are all left to the
plugin-consumer pair.

The main notification/message flow would look like the below:
OS Internal Service —> Searchlight —>  Zaqar-plugin —> Zaqar —> External app

For each Searchlight plugin, it may have a notification forwarder configured.
After Searchlight has received a notification, performed any data enrichment,
and indexed into ElasticSearch, it would send the enriched data to the
configured notification forwarder via its plugin.

The notification forwarder would support filtering out forwarded fields:

 * Unsearchable fields (already configurable by Searchlight)
 * Admin only fields
 * By regex (similar to Glance property protections)

Searchlight may ease plugin development by refactoring the above functionality
into a common utility. The respective plugins may want to leave filtering as
configurable parameters or hard code them. This is entirely up to the
plugin-consumer pair.

This way, when a resource gets updated by notification, the updated resource
will be sent out to a messaging system like Zaqar. The Zaqar message body will
include the complete resource data from Searchlight.

Alternatives
------------

An alternative is introducing a brand new service, split out from ceilometer,
to listen to notifications, but that would have the following shortcomings.

Would either not have or would have to rebuild Searchlight's ability to enrich
data and to know about sensitive data.

Generically solving the issue of cache coherency from listening to
notifications and from periodic re-synchs would still be an issue.
Ideally no consumer should be obliged to deal with a flood of notifications
resulting from another consumer initiating some action.
Consider for instance the Horizon table view, such as the instance table
which lists all instances. If Horizon was just consuming the
notification data to display new instances as they become available,
it could call the Nova API to supplement any currently displayed list
of instances. However, the results the user sees from searching/
Searchlight (see Horizon blueprints referenced) are different. Likewise the
results will vary should the search criteria be changed. By keeping
Searchlight as the first hop in a notification pipeline, we ensure the user
has a consistent view of all notifications, barring any re-synchs the user
initiates.

References
==========

[1] https://launchpad.net/zaqar

[2] https://www.youtube.com/watch?v=0jYXsK4j26s&feature=youtu.be&t=2053

[3] https://www.youtube.com/watch?v=0jYXsK4j26s&feature=youtu.be&t=167

[4] https://blueprints.launchpad.net/horizon/+spec/searchlight-search-panel

[5] https://blueprints.launchpad.net/horizon/+spec/searchlight-images-integration

[6] https://blueprints.launchpad.net/horizon/+spec/searchlight-instances-integration

[7] https://www.youtube.com/watch?v=0jYXsK4j26s&feature=youtu.be&t=1771

[8] https://bugs.launchpad.net/searchlight/+bug/1524998
