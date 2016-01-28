..
    c) Copyright 2016 Hewlett-Packard Development Company, L.P.

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
ElasticSearch Deletion Journaling
================================================

https://blueprints.launchpad.net/searchlight/+spec/es-deletion-journaling

This feature enables tracking of object deletion in ElasticSearch to allow
for better coherency and asynchronous operations.

Problem Description
===================

As a service providing a snapshot of the OpenStack eco-system, we expect the
following trait:

* The snapshot is up to date and coherent, independent of the order of the
  updates received from the other various OpenStack services.

Anything less and we will have failed our users with a deluge of undependable
data.

Background
----------

When created, an ElasticSearch document is stored in an index. When deleted,
we barbarically engage in Damnatio Memoriae and the ElasticSearch document is
permanently removed from the index. In most cases this is not an issue and the
document is not missed. But computer science is fraught with corner cases. One
such corner case is introduced with the new Zero Downtime Re-indexing
functionality [1]. Now Searchlight is required to remember the existence of
deleted documents.

With the addition of the Zero Downtime Re-indexing, Searchlight will be
performing CRUD operations on documents simultaneously from both re-syncing
(which uses API queries) and notifications sent from the services. All within
a distributed environment. These notifications will result in an asynchronous
sequence of ElasticSearch operations. Searchlight needs to make sure that the
state of the eco-system is always correctly reflected in ElasticSearch,
independent of the non-determinate order of notifications that are being
thrown by the services. If a delete notification is received before
the corresponding create notification, this sequence of events still need to
result in the correct ElasticSearch state.

In light of this harsh reality, we need to make the Searchlight document CRUD
commands order independent. This implies a way to track the state of deleted
documents. See below for more concrete examples of the issues we are resolving
with this blueprint.

As a side note, keeping track of deleted documents will allow Searchlight to
easily provide a "delta" functionality if so desired in the future.

ElasticSearch provides functionality to allow Searchlight to track deleted
documents. Instead of rashly removing a document, we can avail ourselves of the
TTL (Time To Live) field for that document. This will allow the document to
exist until all ordering issues are resolved. Once ElasticSearch is
asynchronously satisfied, the document will fade away into the distant recesses
of Searchlight's collective memory.

The concept and use of the TTL field is described in the ElasticSearch
guides [2].

Examples
--------
Some more concrete example may help here. We will use Nova as the resource type,
As a reminder here is how the plug-in commands map to ES operations.

* A "Create document" command in the Nova plug-in turns into an ES "index"
  operation with a new payload from Nova.
* An "update document" command in the Nova plug-in turns into an ES "index"
  operation with a new payload from Nova that already contains the
  modifications. Once thing to note here is that we do neither an ES "update"
  operation nor a read/modify/write using multiple ES operations. From
  ElasticSearch's frame of reference an update command is the same as a create
  command.
* A "delete document" command turns into an ES "delete" operation.

Example #1 (Fusillade)
----------------------
Consider the following Nova notifications "Create Obj1", "Modify Obj1", "Modify Obj1",
"Modify Obj1" and "Delete Obj1". Due to the distributed and asynchronous nature of
the eco-system.  the order the notifications are sent by the listener may not be the
same order the operations are received by ElasticSearch. In some cases, the last
ElasticSearch modify operation will arrive after the ElasticSearch delete operation.
ElasticSearch will see the following operations (in this order): ::

    PUT /searchlight/obj1        # Create Obj1
    PUT /searchlight/obj1        # Modify Obj1
    PUT /searchlight/obj1        # Modify Obj1
    DELETE /searchlight/obj1     # Delete Obj1
    PUT /searchlight/obj1        # Modify Obj1

After all of the operations are executed by ElasticSearch, the net result will
be an index of the Nova object "Obj1". When queried by an inquisitive user,
Searchlight will embarrassingly return the phantom document as if it corporeally
exists. Folie a deux! Not good for anyone involved.

Example #2 (Nostradamus)
------------------------
We will also need to handle the simplistic case of Nova creating a document
followed by Nova deleting the document. This case could be rather common
in the Zero Downtime Re-indexing work [1]. This sequence results in the
Nova notifications "Create Obj2" and "Delete Obj2". If the ElasticSearch
create operation arrives after the ElasticSearch delete operation,
ElasticSearch will see the following operations (in this order) ::

    DELETE /searchlight/obj2     # Delete Obj2
    PUT /searchlight/obj2        # Create Obj2

After both operations are executed by ElasticSearch, the net result will be
an index of the Nova object "Obj2". This naughty behavior is incorrect
and also needs to be avoided.

This example also illuminates a subtlety with out of order deletion notifications.
There may be times when ElasticSearch is being asked to delete a (currently)
non-existent document. This omen of a future event needs to be interpreted and
thus handled correctly.

Proposed Change
===============

Ecce proponente! With this blueprint, the basic idea is to keep the state of
a deleted document around until no longer needed. At a high level, we will
need to make three major modifications to Searchlight.

* We will need to modify the ElasticSearch index mappings.
* We will need to modify the delete functionality to take advantage of the
  new mapping fields.
* We will need to modify the query functionality to be aware of the new
  mapping fields.

ElasticSearch Index Mapping Modification
----------------------------------------

Two modifications are needed for the mapping defined for each index.

The first modification is to enable the TTL field. We need to define the
mapping for a particular index like this: ::

  {
      "mappings": {
          "resource_index": {
              "_ttl": { "enabled": true }
          }
      }
  }

By not specifying a default TTL value, a document will not expire until the
TTL is explicitly set. Exactly what we need.

The second modification is to add a new metadata field to the mapping.
The metadata field would be named "deleted" and would always be defined.
When the document is created/modified the field would be set to "False".
When the document is deleted the field would be set to "True". There is
some concern that we need more than a boolean for this field. A version
or timestamp may be more appropriate. This is a detail for the design and
can be fleshed out at that time if needed.

Searchlight Delete Functionality Modification
---------------------------------------------

When a document is deleted, we will need to set both the TTL field and the
metadata field. This is considered a modification to the original document.

If the document does not already exist, we will need to create the document
and set the "deleted" and "TTL" fields. This will prevent an out-of-order
create/update operation from succeeding.

Searchlight Query Functionality Modification
--------------------------------------------

When a document is queried, we will need to modify the query to exclude
any documents whose metadata indicates the document has been deleted. We will
also need to filter out the metadata field.

Searchlight Create/Modify Functionality Modification
----------------------------------------------------

When a document is created, the mapping will need to add the new "deleted"
field and enable TTL functionality. The "deleted" field will need to be set
appropriately. If the "deleted" field is set to true we will not modify
the document. These modifications depend on the version functionality being
in place [3].

Configuration Changes
----------------------

We need to define the TTL value to determine how long a deleted document
endures. This default value can be overridden by a configuration value.

Setting a TTL value is not enough to delete a document. In tandem we need
ElasticSearch to run its purge process. This purge process will poll all
documents and delete those with expired TTL values. The default is to run the
purge process every 60 seconds. This default value can be overridden by a
configuration value.

Deleted Field Options
---------------------

For historical completeness, here are the different options that were considered
for the "deleted" metadata field.

(1) The metadata field would be named "deleted" and would be defined only when a
    document has been deleted. When a document is created/modified this field is
    not defined. To detect if a document is deleted we will search for the
    existence of this field. This simplifies the create/modify code, but
    complicates the query code.
(2) The metadata field would be named "deleted" and would always be defined.
    When the document is created/modified the field would be set to "False".
    When the document is deleted the field would be set to "True". This adds a
    little bit of work to the create/modify but simplifies the query command.
(3) The metadata field would be named "state" and would always be defined. The
    value of "state" would be the current state of the document: "Created",
    "Modified" or "Deleted". More work is needed in this option to distinguish
    between "Modified" and "Create", since they are treated the same say in
    the plug-ins. This will allow for "delta" functionality to be added to
    Searchlight in the future. This work is the same as option (2).

Alternatives
------------

ElasticSearch has garbage collection functionality. Further research can
determine if garbage collection is a better alternative to using TTLs. In
particular, modifying the garbage collection interval [4].

References
==========

[1] The Zero Downtime Re-indexing work is described here:
    https://blueprints.launchpad.net/searchlight/+spec/zero-downtime-reindexing

[2] The concept of a TTL field is described here:
    https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-ttl-field.html/searchlight/obj1

[3] External versions added to ElasticSearch documents is described here:
    https://review.openstack.org/#/c/255751/

[4] ElasticSearch garbage collection is disucssed here:
    https://www.elastic.co/guide/en/elasticsearch/guide/current/_monitoring_individual_nodes.html#garbage_collector_primer
