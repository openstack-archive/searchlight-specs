..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===================
Cross-Region Search
===================

SearchLight currently is targeted at being deployed alongside nova, glance,
cinder etc. as part of an Openstack control plane. There has been a lot of
interest in allowing SearchLight to index and search resources across
Openstack regions.

Problem Description
===================

A typical production Openstack deployment can provide scaling_ and resilience
in several ways, some of which apply to all services and some specific to
services that support a feature.

**Availability zones** provide some ability to distribute resources (VMs,
networks) across multiple machines that might, for instance be in separate
racks with separate power supplies. AZs are represented in resource data
and are already part of the indexing that SearchLight does.

**Regions** can provide separation across geographical locations (different
data centers, for instance). The only requirement to run multiple regions
within a single Openstack deployment is that Keystone is configured to share
data across the regions (with master-master database replication, for
instance). All other services are isolated from one another, but Keystone is
able to provide the URLs for, say, the ``nova-api`` deployments in each
region. A keystone token typically is not scoped to a particular region;
Horizon currently treats a region change as a heavy weight option because it
means refreshing the dashboards and panels that should be visible in the
selected region.

**Multiple clouds** provide total isolation such that each cloud is totally
separate with no knowledge of the other. Horizon also supports this model
(confusingly also referring to each cloud as a 'Region') though changing
'region' requires logging into the new region.

**Nova cells** are a feature specific to Nova that allows horizontal scaling
within a single region. Cells_ spread the compute API over several databases
and message queues in a way that's mostly transparent to users. Cells will
be considered beyond the scope of this document since they address performance
rather than resilience, and thus aren't directly related to this feature
(though may be the basis of another).

For deployments using multiple regions, the ability to search aggregated data
can provide value. A Nova deployment in a fictional Region-A is
unaware of resources in a fictional Region-B, so a user must make requests to
each region to get information. This makes Horizon somewhat cumbersome
(changing region triggers reloading pages to change the context,
although authentication status is preserved).

.. _scaling: http://docs.openstack.org/openstack-ops/content/scaling.html
.. _Cells: http://docs.openstack.org/liberty/config-reference/content/section_compute-cells.html

These are the potential deployment options for multi-region clouds. The options
that follow are presented in order of effort and complexity. Relative
performance is noted.

1. Deploy Searchlight in the same fashion as Keystone. API endpoints can exist
   in both regions. Data will be duplicated between regions (by some external
   process - Elasticsearch explicitly does not support or recommend splitting
   clusters across geographical locations); Searchlight indexing will write to
   its local cluster and queries will be run against a local cluster. All
   region-aware resources will have a region id attached to them.
   **Best performance**, **most difficult maintenance**,
   **zero client complexity**.

2. Searchlight will run in each location, but data will not be duplicated
   across locations (similar to how nova and glance work). To allow searching
   across regions, Elasticsearch is configured with a tribe_ node that acts as
   a federated search node; indexing operations are always performed locally.
   A search against an alias on the tribe node will act as a search against
   that alias in all clusters to which the tribe node is joined.
   **Worst performance** (as bad as the slowest node, though single region
   searches can be optimized), **easier maintenance**,
   **zero client complexity**.

3. Run Searchlight in both regions separately; either have clients make
   queries against both regions explicitly or have Searchlight's API echo
   requests to other regions. Likely this would enforce segregating results by
   region (which might be a good outcome).
   **Variable performance** (can receive results as they are available),
   **easiest maintenance**, **complexity pushed to client**.

.. _tribe: https://www.elastic.co/guide/en/elasticsearch/reference/current/modules-tribe.html

It should be noted that options 1 and 2 provide a similar
functional experience; searches will appear to run against a single API
endpoint returning data in multiple regions (sorting and paging
appropriately). Option 3 treats each region separately; paging and sorting
would apply to each region's results. There is a decision to be made even at
that level what is actually desirable; should the UI segregate results by
region or is a merged view more desirable?

Proposed Change
===============

After discussion at the Newton summit in Austin (where the alternative below
was presented) it was agreed that a unified view is potentially very useful,
but requires significant awareness of the security implications and a lot more
testing. The general feeling given the workload for Newton was that this
functionality can be adequately supported from the client.

As such, we will document the method by which Searchlight can be run using
tribe nodes, and the networking implications it brings. We will also add
``region_name`` to all mappings.

This may be expanded upon in subsequent releases.

Alternatives
------------

To enable use of tribe nodes to support searches in multiple regions:

#. Set up a stock devstack with Searchlight
#. Deploy a second devstack configured for `multi-region`_ (I set it up on
   a second local VM)
#. Ensure that ``searchlight.conf`` included the correct ``region-name`` in
   the auth credential sections
#. Ensure that the Elasticsearch cluster names were different
   (``cluster.name: region-one``)
#. Check that ``searchlight-manage`` indexes correctly in each region
#. Set up a tribe_ node (again with a different cluster name) on a different
   port on the first devstack VM. I used manual host discovery
#. Configure a separate searchlight-api running off the tribe node. Searches
   against the alias return results across both clusters

This technique will suffer from the same problem that resulted in us disabling
`multi-index support`_; if the index mappings are different errors will
result. The solution (as I suspect there) is to ensure identical mappings
across indices even if no data is indexed into a given index.

The work required here in addition to setting up Elasticsearch would be to
make ``searchlight-api`` use the tribe node (potentially one in every region)
rather than the cluster the listener uses (or perhaps both depending on
search context). This change is relatively minor. We would also need to make
all resources region aware (which is a sensible change) and make sure
Searchlight itself is aware of its own region (also a sensible change).

.. _`multi-index support`: (https://blueprints.launchpad.net/searchlight/+spec/reenable-multiple-indices)
.. _`multi-region`: http://docs.openstack.org/developer/devstack/configuration.html#multi-region-setup
.. _tribe: https://www.elastic.co/guide/en/elasticsearch/reference/current/modules-tribe.html

References
==========

* Openstack scaling http://docs.openstack.org/openstack-ops/content/scaling.html
* Elasticsearch 'tribe' nodes: https://www.elastic.co/guide/en/elasticsearch/reference/current/modules-tribe.html
