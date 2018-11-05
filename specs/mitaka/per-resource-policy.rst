..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===========================
Per resource policy control
===========================

https://blueprints.launchpad.net/searchlight/+spec/per-resource-type-policy-control

Problem Description
===================
Current policy control allows us to restrict who can query, list plugins or
retrieve facets using the oslo policy engine [1]. Openstack is moving towards
supporting more fine-grained controls, and for Searchlight a step in that
direction is allowing control over individual resource types. For instance,
it might be the case in a given cloud that non-administrative users should
not be permitted to search a particular resource type. Longer term this allows
us to move towards a model where RBAC is defined by policy control; rather than
the hard-coded project-based RBAC we use for each plugin, we might replace or
augment it with the typical `is_admin_or_owner` policy rule employed by
projects.

Proposed Change
===============
The proposed change will allow `policy.json` to include rules for individual
plugins. A rule `resource:<resource type>:allow` will control overall access to
a plugin. In addition, `allow` can be replaced with other actions to allow more
precise control. For instance, rules might be::

    "default": "",
    "resource:OS::Glance::Image:allow": "@",
    "resource:OS::Glance::Image:facets": "is_admin:True"
    "resource:OS::Nova::Server:query": "!"

A future extension may extend this to support RBAC rule specification through
policy. For instance, the following rules might translate into the existing
RBAC query we have today::

    "admin_or_owner": "is_admin:True or project_id:%(project_id)s",
    "resource:OS::Nova::Server:allow": "admin_or_owner",

If a resource is *not* allowed via policy, it will be removed from the list
of types to be searched; if this results in no allowed types, the search will
return an empty result set.

Alternatives
------------
Disabling plugins entirely in setup.cfg is one possibility that can be done
with the current codebase.

Disabling indexing for non-administrators would require a few changes.

The ideal long-term solution (which is one that this proposal drives towards)
is to consume the service ``policy.json`` files as does horizon. Ultimately
the hard-coded RBAC rules might be expressed as policy rules in many cases,
allowing greater configuration flexibility (for instance, restricting access
to a resource to the user that created it and not the project/tenant). This
will make it easier to keep searchlight deployments in sync with the rules
deployed with each service.

References
==========
[1] Oslo policy documentation:
    http://docs.openstack.org/developer/oslo.policy/api.html
