..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===============
Default filters
===============

https://blueprints.launchpad.net/searchlight/+spec/overridable-default-filters

This spec is proposed to support cases in plugins where a filter should be
applied for most searches, but should be overidable by a user.

Problem Description
===================
The two cases identified thus far for supporting default (but overridable)
filters are glance's community images, and nova deleted server instances. In
both cases there are query clauses that should be applied to searches by
default, but which a user should be able to explicitly disable.

Proposed Change
===============
In addition to RBAC filters which are applied to all queries on a per-plugin
basis, this change will allow plugins to specify additional filters that will
be applied by default alongside the RBAC filters. For these defaults, however,
the query builder will examine the incoming query for any instances of the
fields that would be filtered on, excluding any filters that the user has
explicitly specified.

This solution will have some flaws. query_string clauses are by their nature
difficult to analyze; potentially we can look for instances of ``key:`` after
splitting on ``&``. For structured queries, looking for instances of the
filter key in the structured query should be good enough.

In addition, it will be difficult/impossible to know whether a filter should
be overridden only for specific types (e.g. if ``deleted`` is a default filter
for the Nova servers plugin, it will be removed for any query including
``deleted`` as a term even if it wasn't intended to apply to Nova servers).

These limitations are somewhat unavoidable given the flexibility of the
Elasticsearch DSL. The cases for removing these filters are specific enough
that edge cases aren't important.

Alternatives
------------
None, but this restricts the use of Searchlight for Nova's cells, and the
ability to match Glance's API with respect to community images.

An alternative implementation option would be a specific option for 'disable
default filters' at the query top level. This would be safer, more performant,
more predictable but would require knowledge of these defaults (e.g. that a
search for ``_type:OS::Nova::Server AND deleted`` won't return anything
unless the additional override parameter is given).

References
==========
