
..
    c) Copyright 2016 Intel Corp.

    Licensed under the Apache License, Version 2.0 (the License); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an AS IS BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

================================================
Pipeline Architecture
================================================

https://blueprints.launchpad.net/searchlight/+spec/pipeline-architecture

This feature enables flexible pipeline architecture to allow Searchlight to
configure multiple publishers to consume enhanced data.

Problem Description
===================

Currently when a notification comes to Searchlight, it gets processed in
a notification handler. The handler enriches notifications in a number of ways
and indexes enriched data into Elasticsearch. This is a simple and
straightforward approach because Elasticsearch is the only storage backend in
Searchlight now. As we are going to introduce notification forwarder [1], this
process becomes inflexible. A pipeline architecture is needed to
provide extra flexibility for users to define where enriched data is published
to. It also allows Searchlight to support other non-elasticsearch backends
in the future.

Proposed Change
===============
We propose that Searchlight change to a pipeline architecture to provide
flexibility for forwarding notifications.

The current main message flow in Searchlight is looking like the below:
Source(Notifications) -> Enrichment&Index to Elasticsearch.

Currently notification handlers wait for notifications, transform them and
index data into Elasticsearch. It's tight coupled and not modular. A
consistent workflow is needed.

With pipeline in place, the main message flow would look like:
Source(Notifications) -> Data Transformer(Enrichment) -> Publishers(Elasticsearch, Zaqar).

To achieve this, some refactors to Searchlight are needed. Notification
handlers focus solely on capturing supported notification events.
After that, notifications are forwarded to data transformers.
There are mainly two kinds of data transformation. One is to normalize
a notification into an OpenStack resource payload. The payload is api
compatible format without publisher additional metadata. The
normalization is always done by either calling OpenStack API services
or updating existing Elasticsearch data. These resource transformers
are plugin-dependent. For example, a nova create instance notification
could be normalized into a server info document. Besides resource data
enrichment, there might be some publisher metadata to be attached,
like user role field, parent child relationship, version in
Elasticsearch. These transformations should be separated from resource
data enrichment.

Publishers should implement a method to accept enriched data, notification
information, as well as an action indicated resources CURD. For example, if a
nova server has been updated, publishers in the pipeline will receive server
full info, server update notification and an 'update' action. It is entirely
up to the publisher to decide how to deal with those information.

We see Elasticsearch indexing as a case of publisher. It could be the default
publisher because for some plugins resource update needs to fetch old documents
from Elasticsearch, partial update doesn't work without Elasticsearch, though in
the future we may solve this issue. The order of publishers in the pipeline
doesn't matter. Publisher can choose how to deal with errors, either request a
requeue or just ignore the exception. The requeue operation is especially
useful for Elasticsearch publisher, because data integrity is important for
search functions of Searchlight. Requeue should not affect other configured
publishers, thus a filter is needed to make sure publishers won't deliver
same message twice.

Currently Searchlight gets its data in two ways, one is incremental updates via
notifications, the other is full indexing to ElasticSearch via API calls.
Incremental updates are notified to all the publishers configured in the
pipeline. For reindexing, it is up to publishers to decide if they want
reindexing or not.

There are two alternatives of pipeline design. One is the pipeline only
consists of publishers. Notifications are normalized by resource transformer,
then passed to configured publishers. Publishers could attach specific metadata
inside themselves. Users can only control what publishers Searchlight data is
heading for. Another alternative is make both transformers and publishers
configurable. By combining different transformers and publishers, one can
produce different pipeline on same notification.


Alternatives
------------


References
==========

[1] https://blueprints.launchpad.net/searchlight/+spec/notification-forwarding

