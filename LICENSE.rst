xtas license and legal information
==================================

xtas license
------------

xtas is Copyright 2013-2016 Netherlands eScience Center and
University of Amsterdam

With the exception of the NERServer helper program and the modified
Sentiwords data set, xtas is licensed under the Apache License,
Version 2.0 (the "License"); you may not use xtas except in compliance
with the License. You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

or see LICENSE-al2.txt.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

NERServer license
-----------------

NERServer is Copyright 2014 Netherlands eScience Center and University of
Amsterdam

The NERServer helper program, comprising NERServer.java and NERServer.class,
is free software: you can redistribute it and/or modify it under the terms
of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

NERServer is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
NERServer.  If not, see <http://www.gnu.org/licenses/>.

SentiWords license
------------------

xtas incorporates a (mechanically) modified version of SentiWords v1.0, in
sentiwords.txt.

Copyright © 2014 Trento RISE and FBK
All rights reserved.

Modified for xtas to save space:

- took the (unweighted) mean over POS tags per word
- removed all words with zero (mean) score.

SentiWords is distributed under the Attribution-ShareAlike 3.0 Unported
(CC BY-SA 3.0) license.
http://creativecommons.org/licenses/by-sa/3.0/

Additional software for use with xtas
-------------------------------------

xtas acts as a package manager and shell for several tools and data sets. It
will download and run these programs and data sets for you when you use the
corresponding xtas functions. For your information, as of writing, these were
distributed under the following licenses:

- Heideltime: GNU General Public License version 3 or higher
- ILK Frog: GNU General Public License version 3 or higher
- RUG Alpino: GNU Lesser General Public License version 2.1 or higher
- SEMAFOR: GNU General Public License version 3 or higher
- Stanford CoreNLP 3.4.1: GNU General Public License version 3 or higher
- Stanford NER: GNU General Public License version 2 or higher

Heideltime requires Treetagger, which as of writing is licensed under a
restrictive license which only allows research and teaching use. xtas will
not download or install Treetagger. If you meet the license requirements,
you can install Treetagger yourself, and point xtas at it; xtas will then
install Heideltime for you and configure it to use your Treetagger
installation.

External data sets for use with xtas
------------------------------------

xtas will download and use several data sets as required to implement some
of its functionality. These are

- `polarity dataset v2.0
  <http://www.cs.cornell.edu/people/pabo/movie-review-data/>`_ (no explicit
  license)
- `emotion classification dataset of Buitinck et al.
  <https://github.com/NLeSC/spudisc-emotion-classification>`_ (You may use
  this data for academic/research purposes.)
- `University of Antwerp CoNLL'02 data
  <http://www.cnts.ua.ac.be/conll2002/ner/>`_ (Files in these directories
  may only be used for research applications in the context of the
  CoNLL-2002 shared task. No permission is given for usage other applications
  especially not for commercial applications.)

xtas will require you to explicitly acknowledge these restrictions when using
the corresponding functionality.

External services for use with xtas
-----------------------------------

xtas can call the University of Amsterdam Semanticizer Web API. Its authors
`request citation of their publication(s) <http://semanticize.uva.nl/doc/>`_
if you use this webservice for your own research.

Python dependencies
-------------------

xtas uses (links to) a number of Python libraries. These are not distributed
with xtas, but installed by pip when you install xtas. As of writing, these
dependencies are distributed under the MIT, New BSD, and Apache License v2.0
permissive open source licenses, and in some cases under the GNU Lesser
General Public License v2.1. See requirements.txt and requirements3.txt for
the package names.

