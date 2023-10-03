=======
Escriba
=======

Easy preservation of web content you care about.

License
-------

The project license is specified in COPYING.

escriba is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.

escriba is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>

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

Black is a highly opinionated code formatter. Black focuses on
reformatting your code files in place for you. When you're comfortable
with black taking over the minutiae of hand formatting you will see
that you can focus more on the content of your code than formatting it
properly.

Install pre-commit
~~~~~~~~~~~~~~~~~~

Install the pre-commit hook running the script below inside the project
root directory:

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

We group imports in 3 sections, in the following order. Within each
section, imports should be lexically sorted:

1. Standard library
2. 3rd party library
3. Our own code

Technical Notes
---------------

For the dashboard, a proven WSGI framework and web server like Flask was
chosen. Adopting ASGI would be nice, but we do not require HTTP/2 nor
Websockets. For now the user interface is expected to be so simple and
boring that anything should suffice. Nothing radical here, just a quick
way to show some progress and present our app to less technical users.

The biggest challenge will be the task dispatcher and supervisor.
We do NOT want to simply push tasks into a queue and hope for the best,
but to be able to inspect them and monitor their state. This means that
tasks queues like Celery or Huey are not enough. Message brokers like
RabbitMQ are out of question as well.

Archivematica uses Gearman to distribute jobs, which may or may not suit us.
Nonetheless, ZeroMQ is a solid library on which we can build a distributed
software system.

As for the object storage, we may use just a plain filesystem. It's a
simple and dependency-free path, but the sheer number of objects may
slow us down unless we take some precautions. When I tested Archivebox,
it became unusable around 10k pages. Escriba must handle that easily and
reach even 1 million pages before breaking a sweat.

The industry standard nowadays uses an S3-compatible API for object
storage. MinIO comes to mind as a solution suited for both enterprise
and single node deployment. GarageHQ and SeaweedFS appear as less
glamorous but more selfhost tailored.

Despite these options, we may not escape implementing a basic object
storage within the file system. Some people may not hold enough data to
justify a full-blow object storage and/or may want to live dependency
free for whatever reason. Our "easy to use" core value should guide our
choice here.

Considering that each page saved is stored in their UUID-named
directory, we can create a nested layout, similar to how git stores the
blobs internally. Take the first byte in a UUID hex string and turn it
into a parent folder. This gives us 256 first level folders to subdivide
our entire collection into balanced directories. To reach 1 million
pages saved without slowing us down, we may even create a middle layer
using the UUID 2nd byte. This should suffice for anyone who does not
need a proper object storage.
