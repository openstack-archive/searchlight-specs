..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===========================
Searching admin-only fields
===========================

https://blueprints.launchpad.net/searchlight/+spec/index-level-role-separation

Our aim is to allow all fields to be searchable and available in facets but
only for users where that is appropriate; as such, we introduced the idea of
filtering search results based on whether or not a user has the admin role.

The flaw that we discovered towards the end of Liberty is described in
https://bugs.launchpad.net/searchlight/+bug/1504399, but very briefly, merely
removing fields from the result is not sufficient. It is possible to 'fish'
for values for known fields by running searches against them and examining
whether results come back; an attacker might use range or wildcard queries
to reduce the time it takes to locate values that return results.

Problem Description
===================

We wish to allow plugins to define fields (whether in code or in configuration)
that cannot be seen by non-administrative users, be that in search results,
visible in facets or by searching for values for a field. Administrators should
be subject to none of these restrictions.

Prior to the fix in bug #1504399 Searchlight fulfilled the first two of these
criteria. Unfortunately the fix (which was under a very tight time restriction)
prevented even administrators from searching fields. The problem, therefore,
is to ensure these conditions.

Proposed Change
===============

Role-based filtering
--------------------
This solution involves indexing twice and adding a field to all resources that
can be used to filter a search based on a user's role. For instance, taking a
heavily cut-down Nova server definition::

  {
    "_id": "aaaaabbbb-1111-4444-2222-eeee",
    "_type": "OS::Nova::Server",
    "_source": {
       "status", "ACTIVE",
       "OS-EXT-ATTR-SOMETHING": "admin only data"
    }
  }

This is turned into two documents, identical except that:
* the admin-only document has an additional field `'user-role': 'admin'`
* the user document has an additional field `'user-role': 'user'`
* the user document does not contain the `OS-EXT-ATTR-SOMETHING` field
* the ids for each document have a role added (`111111-4444-2222-eeee:ADMIN`)

Indexing
~~~~~~~~
Indexing operations are unchanged except that two operations (or one bulk
operation) are needed. Admin-only fields would be stripped from the serialized
source document for the non-admin copy::

  {
    "_id": "aaaaabbbb-1111-4444-2222-eeee_ADMIN",
    "_type": "OS::Nova::Server",
    "_source": {
      "status", "ACTIVE",
      "OS-EXT-ATTR-SOMETHING": "admin only data",
      "_searchlight_user_role": "admin"
    }
  },
  {
    "_id": "aaaaabbbb-1111-4444-2222-eeee_USER",
    "_type": "OS::Nova::Server",
    "_source": {
      "status", "ACTIVE",
      "_searchlight-user-role": "user"
    }
  }


This solution allows resources that don't need an admin/user separation to
index a single document with both roles::

  {
    "_id": "abcdefa-1222",
    "_type": "OS::Designate::Zone",
    "_source": {
      "_searchlight-user-role": ["admin", "user"]
    }
  }

Searches
~~~~~~~~
The server can apply a non-analyzed (term) filter on `_searchlight-user-role`
based on the request context::

  {
    "query": {... },
    "filter": {"term": {"_searchlight-user-role": "admin"}}
  }

Filters are cached and very fast. An alternative, once we switch to using
aliases (see the `zero downtime spec <https://review.openstack.org/#/c/245222/>`_
proposal), is applying the filter on the alias::

  {
    "index": "searchlight-<timestamp>",
    "alias": "searchlight-admin",
    "filter": {"term": {"_searchlight-user-role": "admin"}}
  }

The search API would query against `searchlight-admin` or `searchlight-user`
as appropriate. There is some precedent for this; it's a common way to make
data appear to be segmented based on a field ('index per user' - Reference_)
without the overhead of multiple lucene indices.

.. _Reference: https://www.elastic.co/guide/en/elasticsearch/guide/current/faking-it.html

Second choice - Separate indexes
--------------------------------

.. note:: This began as my frontrunner, but the added maintenance headache
   has pushed me towards filter-based separation.

Another solution is to maintain separate indices for admin and
non-admin users. While this seems offensive from a duplication point of view,
it's very common in non-relational-databases to store information based on
the kinds of queries you want to run. There will be an impact on indexing
speed and data storage, though I believe the volume and throughput of data
we store makes this impact insignificant. The major downside is the increased
maintenance overhead (at a minimum, two indices would be required at least
for those plugins requiring it).

Technically, introducing a pair of indices isn't terribly complicated; all
write operations become two, and searches determine which index they're using
before running. As far as a user sees, there will be no impact (except that
admins will once again be able to run searches against admin-only fields).

Indexing
~~~~~~~~

Information in the -users index can be restricted with dynamic_mapping
template (that can tell Elasticsearch not to store or index matching fields
with `index:no` and `include_in_all:no`). Along with result filtering (or
`_source` filtering or removing these fields from the indexed document)
this achieves all three requirements.

Some plugins do not have admin-only fields, and those plugins could run
against the same index. I believe, though, that it would be necessary to
use a separate shared index in that case, because otherwise a query could
potentially run against (say) `OS::Nova::Server` in both indices. For example,
the structure below assumes `OS::Something::Else` doesn't need two indices,
and all data is in the user index::

  searchlight-admin:
     OS::Nova::Server
  searchlight-user:
     OS::Nova::Server
     OS::Something::Else

An admin query against both types would have to run against both indices,
running the risk of duplicate results for `OS::Nova::Server` resources.
This might need more discussion, but safer would be to either mandate storing
information twice for all types, or::

  searchlight-admin:
     OS::Nova::Server
  searchlight-user:
     OS::Nova::Server
  searchlight-all:
     OS::Something::Else

Searches
~~~~~~~~

Little would change as far as a user is concerned. The search code would
have some extra conditionals in it to determine which index to use. This
would be complicated if an index contains both admin- and non-admin- data.

Alternatives
------------

There are two other alternatives I'm aware of.

1. `Elasticsearch Shield <https://www.elastic.co/products/shield>`_. Shield
   adds a number of features to Elasticsearch, all aimed at security and
   authentication. One of those features (supported only by Elasticsearch 2.0)
   is `field level access control <https://www.elastic.co/guide/en/shield/current/setting-up-field-and-document-level-security.html>`_.
   This requires an inclusive list of fields to be given in configuration on
   a per-index basis, and also requires Shield's authentication to be enabled
   (there are various plugins available). It disables the `_all` field for
   users who are subject to field level restrictions.

   Most importantly, Shield is a commercial, closed-source product that runs
   on the server, and so is able to do things we are not (since it has
   access to the parsed query).

2. Modify or reject incoming queries. We already strip certain fields from
   search results for non-admin users, and in theory we could restrict
   searches in the same way (or raise Not Authorized exceptions). While
   naively this seems straightforward, in reality it becomes complex quite
   quickly. Imagine the following queries against Nova for a protected field
   called `hypervisor_id`::

      {"query": {"term": {"hypervisor_id": "abcd1"}}}
      {"query": {"query_string": {"query": "hypervisor_id:abcd1"}}}
      {"query": {"multi_match": {"query": "abcd1", "fields": ["hypervisor_id"]}}}
      {"query": {"query_string": {"query": "abcd1"}}}

   Constructing filters to catch those queries isn't impossible, but becomes
   increasingly complex; we would essentially need to parse the query, and
   we'd need to do so for each plugin type.

References
==========

* https://bugs.launchpad.net/searchlight/+bug/1504399
* https://review.openstack.org/#/c/233225/ (patch for above)
* `Shield <https://www.elastic.co/guide/en/shield/current/index.html>`_
* https://www.elastic.co/guide/en/elasticsearch/guide/current/faking-it.html
