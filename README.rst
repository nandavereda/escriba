=======
Escriba
=======

Easy preservation of web content you care about.

License
-------

The project license is specified in COPYING.

escriba is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

escriba is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>

Contributing
------------

We adopt git hooks via pre-commit in order to run formatting before the
commit process. This approach has some really nice advantages:

- IDE agnostic
- Runs automatically (i.e. unforgivable) on the code that is changing
- Enforces style consistency in the codebase
- Prevent style bikeshedding
- Helps create smaller diffs

Why Black?
~~~~~~~~~~

Black is a highly opinionated code formatter. Black focuses on reformatting
your code files in place for you. When you're comfortable with black taking
over the minutiae of hand formatting you will see that you can focus more on
the content of your code than formatting it properly.

Install pre-commit
~~~~~~~~~~~~~~~~~~

Install the pre-commit hook running the script below inside the project root
directory:

.. code:: sh

    cat <<EOF > .git/hooks/pre-commit
    #!/bin/sh
    black --check .
    EOF
    chmod +x .git/hooks/pre-commit

Coding standards
----------------

Naming stuff
~~~~~~~~~~~~

Whenever in doubt, prefer nouns in singular:

- DO write view.py
- do NOT write views.py
- DO create table user
- do NOT create table users

Importing stuff
~~~~~~~~~~~~~~~

We always import the modules and avoid rebinding the symbol names:

- DO import datetime
- do NOT from datetime import timedelta
- DO import collections.abc as abc
- do NOT from collections import abc

We group imports in 3 sections, in the following order. Within each section,
imports should be lexically sorted:

1. Standard library
2. 3rd party library
3. Our own code