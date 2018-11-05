
..
    c) Copyright 2016 Hewlett-Packard Enterprise Development Company, L.P.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

=============================
Index Performance Enhancement
=============================

https://blueprints.launchpad.net/searchlight/+spec/index-performance-enhancement.

This feature will improve the performance of indexing resource types within Searchlight.

Problem Description
===================

If the above link is too troublesome to follow, please indulge us while we
plagiarize from the blueprint.

When indexing (first time or re-indexing) we will index all resource group types
sequentially. We loop through all plugins, indexing each one in turn. The result
is that the time it takes to re-index is equal to the sum of the time for all
plugins. This may take longer than it should. In some cases a lot longer.

The time it takes to complete the full index is::

        n
    O( ∑ T(p) )
        p=0

When n is the number of plugins and T(p) is the time it takes for plugin p to
index.

We should change the algorithm to index in parallel, rather than in serial. As we
are looping through each plugin to re-index, we should spin each indexing task
into it's own thread.  This way the time it takes to index is the time it takes
the longest plugin to re-index.

With this enhancement, the time it takes to complete the index is::

             n
    O( MAX( T(p) ) )
            p=0

To provide context for the design, we will review the current design for
re-indexing. A re-indexing starts when the admin runs the command:

``searchlight-manage index sync``

Under the cover, ``searchlight-manage`` is doing the following:

 * Determine which resource groups need to be re-indexed.
 * Determine which resource types within each resource group needs to be
   re-indexed.
 * For each resource type that *does* need to be re-indexed,
   ``searchlight-manage`` will call the plugin associated with that resource type.
   The plugin will make API calls to that service and re-index the information.
 * For each resource type that *does not* need to be re-indexed,
   ``searchlight-manage`` will call ElasticSearch directly and re-index from the
   old index into the new index.
 * Once all re-indexing is complete, the ES aliases are adjusted and
   ``searchlight-manage`` returns to the user.

This implies the following:
 * The admin must wait for all of the re-indexing to complete before
   ``searchlight-manage`` finishes.
 * When ``searchlight-manage`` finishes, the admin knows the exact state of the
   re-index. Whether it completed successfully or if there was an error.

Proposed Change
===============

As described in the blueprint, we would like to reduce the time to complete the
re-index. Based on discussions with the blueprint and this spec, we will be
implementing only the first enhancement in the blueprint. We will be using python
threads to accomplish this task. We need to understand the design issues
associated with implementing a multi-thread approach.

1. **Are the indexing plugins thread-safe?**

If there are a lot of inter-dependencies within the plugins, it may not pay off
to try to multi-thread the plugins. Reviewing the code and functionality of the
plugins, they appear to be separate enough that they are good candidates to be
moved into their own threads. The plugins are isolated from each other and do not
depend on any internal structures to handle the actual indexing.

**Design Proposal:** The individual plugins can be successfully threaded.

2. **At what level should we create the indexing threads?**

The obvious candidates are the resource type (e.g. OS::Nova::Server) or the
resource type group (e.g. the index "searchlight"). The main reason that we are
considering this enhancement is due to the large amount of time for a particular
resource type, but not for a particular resource type group.

Internal to ``searchlight-manage``, this distinction fades rather quickly. We use
the resource type groups to only determine which resource types need to be
re-indexed. We also have an existing enhancement within ``searchlight-manage``
where we re-index through the plugin API only the resource types that were
explicitly demanded by the user. All other resource types are re-indexed directly
within ElasticSearch.  We need to keep this enhancement.

Keeping the current design intact means we will want to thread on the fine
resource type level and not at the gross resource type group level. Based on the
parent/child relationship that exists between some of the resource types, this is
the "fine" level we will be considering.

Since we are already using bulk commands for Elasticsearch re-indexing, we will
place all of the Elasticsearch re-indexing into a single thread. Considering
that this will be I/O bound on Elasticsearch's side, There does not appear
to be any advantage of doing an Elasticsearch re-indexing for each resource type
in a separate thread.

**Design Proposal:** Whenever the indexing code currently calls the plugin API,
it will create a worker in the thread pool.

**Design Proposal:** All of the calls to ElasticSearch to re-index an existing
index, will be placed in a single worker in the thread pool.

3. **Mapping of plugins to threads**

There may be a large number of plugins used with Searchlight. If each plugin
has its own thread, we may be using a lot of threads. Instead of having a single
thread map to a single plugin, we will use a thread pool. This will keep the
number of threads to a manageable level while still allowing for an appropriate
level of asynchronous re-indexing. The size of the thread pool can be changed
through a configuration option.

**Design Proposal:** Use a thread pool.

4. **When will we know to switch the ElasticSearch aliases?**

In the serial model of re-indexing, it is trivial to know when to switch the
ElasticSearch alias to the use the new index. It's when the last index finishes!
Switching over to a model of asynchronous threads running in parallel potentially
complicates the alias update.

The indexing code will wait for all the threads to complete. When all threads
have completed, the indexing code can continue with updating the aliases.

**Design Proposal:** The alias switching code will be run after all of the
threads have completed.

5. **How do we clean up from a failed thread?**

The indexing code will need to have the threads communicate if a catastrophic
failure occurred. After all workers have been placed into the Thread pool, the
main program will wait for all of the threads to finish. If any thread fails,
it will raise an exception. The exception will be caught and the normal
clean-up call will commence. All threads that are still waiting to run will be
cancelled.

**Design Proposal:** Catch exceptions thrown by a failing thread.

For those following along with the code (searchlight/cmd/manage.py::sync), here
is a rough guide to the changes. We will reference the sections as mentioned in
the large comment blocks:

* First pass: No changes.
* Second pass: No changes.
* Step #1: No changes.
* Step #2: No changes.
* Step #3: No changes.
* Step #4: Use threads. Track thread usage.
* Step #5: No changes.
* Step #6: No changes.

Alternatives
------------

We can always choose to not perform any enhancements. Or we can go back to the
first draft of this spec.

References
==========

