..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

================================================
Example Spec - The title of your Feature Request
================================================

Include the URL of your blueprint:

https://blueprints.launchpad.net/searchlight/...

Introduction paragraph / summary -- why are we doing anything?

Introduction paragraph -- why are we doing this feature? A single paragraph of
prose that **deployers, and developers, and operators** can understand.

Do you even need to file a spec? Many features can be done by filing a blueprint
and moving on with life. In most cases, filing a blueprint and documenting your
design in the devref folder of searchlight docs is sufficient. If the feature
seems very large or contentious, then the drivers team may request a spec, or
you can always file one if desired.

Problem Description
===================

A detailed description of the problem:

* For a new feature this should be a list of use cases. Ensure that you are clear
  about the actors in each use case: End User vs Deployer. Ensure that you identify
  which area of the core is being affected; for something completely new, it
  should be clear why you are considering it being part of the core.

* For a major reworking of something existing it would describe the
  problems in that feature that are being addressed.

Note that the BP filed for this feature will have a description already. This
section is not meant to simply duplicate that; you can simply refer to that
description if it is sufficient, and use this space to capture changes to
the description based on bug comments or feedback on the spec.

Proposed Change
===============

How do you propose to solve this problem?

This section provides an area to discuss your high-level design at the same
time as use cases, if desired.  Note that by high-level, we mean the
"view from orbit" rough cut at how things will happen.

This section should 'scope' the effort from a feature standpoint: how is the
'searchlight end-to-end system' going to look like after this change?
What searchlight areas do you intend to touch and how do you intend to work
on them? The list below is not meant to be a template to fill in, but rather
a jumpstart on the sorts of areas to consider in your proposed change
description.

* Am I going to see new CLI commands?
* How do you intend to support or affect aspects like:
  * API
  * Clients
  * Impact on services or out-of-tree plugins/drivers
  * Security
  * Performance
  * Testing
* What do you intend to not support in the initial release?
* What outside dependencies do you foresee?

You do not need to detail API or data model changes. Details at that level of
granularity belong in the devref docs.

Alternatives
------------

This is an optional section, where it does apply we'd just like a demonstration
that some thought has been put into why the proposed approach is the best one.

References
==========

Please add any useful references here. You are not required to have any
reference. Moreover, this specification should still make sense when your
references are unavailable.

