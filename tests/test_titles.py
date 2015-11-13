# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import glob
import re

import docutils.core
import testtools


class TestTitles(testtools.TestCase):
    def _get_title(self, section_tree):
        section = {
            'subtitles': [],
        }
        for node in section_tree:
            if node.tagname == 'title':
                section['name'] = node.rawsource
            elif node.tagname == 'section':
                subsection = self._get_title(node)
                section['subtitles'].append(subsection['name'])
        return section

    def _get_titles(self, spec):
        titles = {}
        for node in spec:
            if node.tagname == 'section':
                # Note subsection subtitles are thrown away
                section = self._get_title(node)
                titles[section['name']] = section['subtitles']
        return titles

    def _check_titles(self, filename, expect, actual):
        # TODO(dougwig): old style specs get a pass
        old = [
            'Dependencies',
            'Documentation Impact',
            'Implementation',
            'Testing',
        ]
        old += expect

        missing_sections = [x for x in expect if x not in actual]
        extra_sections = [x for x in actual if x not in old]

        msgs = []
        if missing_sections:
            msgs.append("Missing sections: %s" % missing_sections)
        if extra_sections:
            msgs.append("Extra sections: %s" % extra_sections)

        for section in expect.keys():
            missing_subsections = [x for x in expect[section]
                                   if x not in actual[section]]
            # extra subsections are allowed
            if len(missing_subsections) > 0:
                msgs.append("Section '%s' is missing subsections: %s"
                            % (section, missing_subsections))

        if len(msgs) > 0:
            self.fail("While checking '%s':\n  %s"
                      % (filename, "\n  ".join(msgs)))

    def _check_lines_wrapping(self, tpl, raw):
        for i, line in enumerate(raw.split("\n")):
            if "http://" in line or "https://" in line:
                continue
            self.assertTrue(
                len(line) < 80,
                msg="%s:%d: Line limited to a maximum of 79 characters." %
                (tpl, i+1))

    def _check_no_cr(self, tpl, raw):
        matches = re.findall('\r', raw)
        self.assertEqual(
            len(matches), 0,
            "Found %s literal carriage returns in file %s" %
            (len(matches), tpl))

    def _check_trailing_spaces(self, tpl, raw):
        for i, line in enumerate(raw.split("\n")):
            trailing_spaces = re.findall(" +$", line)
            self.assertEqual(len(trailing_spaces), 0,
                    "Found trailing spaces on line %s of %s" % (i + 1, tpl))

    def test_template(self):
        releases = [x.split('/')[1] for x in glob.glob('specs/*/')]
        for release in releases:
            if release[0] < 'k':
                # Don't bother enforcement for specs before Kilo,
                # or that belong to 'archive' and 'backlog'
                continue
            try:
                # Support release-specific template.
                with open("specs/%s-template.rst" % release) as f:
                    template = f.read()
            except IOError:
                # Base template if release template not found.
                with open("specs/template.rst") as f:
                    template = f.read()
            spec = docutils.core.publish_doctree(template)
            template_titles = self._get_titles(spec)

            files = glob.glob("specs/%s/*" % release)
            for filename in files:
                self.assertTrue(filename.endswith(".rst"),
                                "spec's file must uses 'rst' extension.")
                with open(filename) as f:
                    data = f.read()

                spec = docutils.core.publish_doctree(data)
                titles = self._get_titles(spec)
                self._check_titles(filename, template_titles, titles)
                # TODO(russellb) Enable this eventually, but it will probably
                # require fixes to existing specs.  Alternatively, it could be
                # turned on for a new release (like L) before any L specs are
                # merged to avoid unnecessary churn.
                #self._check_lines_wrapping(filename, data)
                self._check_no_cr(filename, data)
                self._check_trailing_spaces(filename, data)
