..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

=============================
Tacker Plugin for Searchlight
=============================

https://storyboard.openstack.org/#!/story/2004968

This spec is proposed to support indexing Tacker resource information into
ElasticSearch.

Problem Description
===================

Tacker is a software that facilitates the OpenStack components to provide NFV
Orchestration. While leveraging the OpenStack infrastructure to realize its
elements (e.g., virtual machines as VNFs, etc.), Tacker keeps its own copy of
the resource definitions in a separate database. That database can only be
accessed by using the Tacker APIs. So, it would be beneficial to index Tacker
resource information and events into Searchlight to provide a universal search
interface for users.


Proposed Change
===============

The Tacker plugin will support indexing Tacker resources via Tacker API. The
plugin will use the python-tackerclient to communicate with Tacker server to
query its resource information. The plugin will then index that information
into ElasticSearch database. Tacker plugin also offers Searchlight listener
the ability to acknowledge any change on those resources and update the
corresponding data in ElasticSearch.

The following figure describes the overall architecture of the proposed
plugin:

::

 +------------------------------------------------+
 |                                                |
 |                      Tacker                    |
 |                                                |
 +---------^--------------+-----------------------+
           |              |
           |  +-----------v------------+
           |  |     Oslo Messeging     |
           |  +-----------^------------+
           |              |
 +---------|--------------|-----------------------+
 | +-------|--------------v---------------------+ |
 | |  +----v---------------------------------+  | |
 | |  |            Tacker Client             |  | |
 | |  +--------------------------------------+  | |
 | |               Tacker Plugin                | |
 | +----------------------+---------------------+ |
 |                        |                       |
 | +----------------------v---------------------+ |
 | |               ElasticSearch                | |
 | +--------------------------------------------+ |
 |                  Searchlight                   |
 +------------------------------------------------+


The following Tacker resource information will be indexed:

* Network Services (NS)

* Virtual Infrastructure Managers (VIM)

* Virtual Network Functions (VNF)

* Virtual Network Function Forwarding Graphs (VNFFG)


Alternatives
------------

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Trinh Nguyen <dangtrinhnt@gmail.com>

Work Items
----------

1. Create a Tacker plugin for Searchlight to index resource information.
2. Add unit & functional tests.
3. Add user guides.


References
==========

* https://docs.openstack.org/tacker/latest/

* https://docs.openstack.org/python-tackerclient/latest/

* https://docs.openstack.org/oslo.messaging/latest/

* https://www.elastic.co
