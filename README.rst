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

===============
Technical Notes
===============

User interface
--------------

The main user interface will be a web dashboard, so we can easily
interact with Escriba from personal laptops and smartphones.

For the dashboard, a proven WSGI framework and web server like Flask was
chosen. Adopting ASGI would be nice, but we do not require HTTP/2 nor
Websockets. For now the user interface is expected to be so simple and
boring that anything should suffice. Nothing radical here, just a quick
way to show some progress and present our app to less technical users.

Distributed computation platform
--------------------------------

At its core, Escriba is a limited but tireless archivist working
fulltime to preserve web content. This behaviour requires a component
outside of web server request-reply loop which, working independently
of user interaction, is designated a daemon.

The biggest challenge will be the task dispatcher and supervisor.
We do NOT want to simply push tasks into a queue and hope for the best,
but to be able to inspect them and monitor their state. This means that
tasks queues like Celery or Huey are not enough. Message brokers like
RabbitMQ are out of question as well.

The daemon performs `remote procedure calls`_ inside a grid of
heteregeneous and not-always-online nodes. Interesting as it sounds, we
prefer trusting the hard-but-common problems to proven libraries. In
the hope of finding a nice fit for our problem domain, the following
software solutions were evaluated:

.. _remote procedure calls: https://en.wikipedia.org/wiki/Remote_procedure_call

- `dispy <https://dispy.org/index.html>`_
- `gearman <http://gearman.org>`_
- `ray <https://github.com/ray-project/ray>`_
- `rpyc <http://rpyc.sourceforge.net/>`_
- `scoop <http://scoop.readthedocs.org/>`_
- `spread <http://www.spread.org/>`_
- `zeromq <https://zeromq.org>`_

We are interested in frameworks which are able to:

- Support synchronous and asynchronous invocation
- Dispatch tasks based on remote node capabilities (ie `service discovery`_)
- Take care of nodes joining or leaving the network
- Handle workload balancing and node failures
- Collect results from workers
- Extend RPC with distributed futures (mostly for handling files on
  remote nodes)
- Handle large results (e.g. video files)
- Leaning towards `grid computing`_ instead of cluster computing

.. _service discovery: https://en.wikipedia.org/wiki/Service_discovery
.. _grid computing: https://en.wikipedia.org/wiki/Grid_computing

After careful consideration of each of these options we realized that
job distribution and control is our core functionality and as such we
cannot afford to outsource it to some out-of-shelve framework. This
decision aligns with what `Joel was telling us`_ back in 2001.

.. _Joel was telling us: https://www.joelonsoftware.com/2001/10/14/in-defense-of-not-invented-here-syndrome/

The roadmap then is to use zeromq, a comprehensive messaging library, as
foundation and develop the job handling and cluster management logic
ourselves.

Problem domain
~~~~~~~~~~~~~~

Using Erlang's Architecture Model as a reference, we can adapt it to
notice the following properties about Escriba:

1. The system must be able to handle a high number of concurrent
   activities
2. Actions must be performed at a certain point in time or within a
   certain time
3. Systems may be distributed over several computers
4. The system is used to interact with network resources
5. The software system is small
6. The system is a facade for a composite of complex tools
7. The system may be in intermitent operation with months apart each
   execution
8. Stopping the system for software maintainance is not a problem
9. There are moderate quality, and reliability requirements
10. Fault tolerance both to hardware failures, software failures and
    network failures, must be provided

Concurrent - Escriba perform a reasonable number of mostly independent
tasks. As most of these independent tasks are bounded by the remote web
servers capacity, which have an unpredictable latency, a concurrent
system is required.

Soft real-time - many operations have to be performed within a specific
time. As web content becomes increasingly ephemeral over time, acting
quickly on web content we care about may make the difference between a
preserved copy and a 404 Not Found, or the difference between having an
offline copy available before a trip and depending on slow and expensive
mobile connection. Some of these timed operations may be strictly
enforced, in the sense that if a given operation does not succeed within
a given time interval then the entire operation will be aborted. Other
operations are merely monitored with some form of timer, the operation
being reported if the timer event triggers before the operation has
completed. Programming such system requires manipulating many tens of
thousands of timers in an efficient manner.

Distributed - the web content is becoming more dynamic over time. As
most web content is made for humans to access, synchronously, in a
personal computing device, its adequate reprodution may raise computing
power requirements prohibitly for a single-node. Nevertheless,
geo-restrictions are incredible common, and content is adapted for user
screen size and device type. Farming computing resources of distributed
devices, heterogeneus hardware and remote nodes located far away should
be made trivial.

Network interaction - compared to local computing, the web is slow,
faulty and unsafe. Some errors are temporary and may be fixed by the
built-in mechanisms of networking tools. Other errors, may be produced
by uncooperactive agents, working actively to disrupt the collection of
web content and any autonomous non-human activity. These errors may
disappear when throling is applied, may require cookies and other
techniques to certificate our daemon is playing fairly, or need creative
adversarial interoperability tactics. Blindly trusting each other is
rarely a sane idea, even more in a web environment. The web is infested
of malware, misconfigured systems and badly intentioned agents. For
being a nice netizen (net citizen) we must validate the safety and
correctness of what is consumed, and show ourselves in a respectful
manner, with transparency and fair usage of public and shared resources.

Small size - Escriba size is trivial

Complex functionaly - web browsing have complex endeavor. The good side
is that we do not need to reinvent the wheel and can use a vast number
of free and open source tools to assist us. The bad side is that these
tools abstract, but do not eliminate, the web complexity and, when
things go badly, as they inevitably do, some of that complexity may
surface to us through leaky abstractions. Escriba take the burden of
handling all the edge cases and specificities of each tool to present
a clean and uniform interface for our users.

Intermitent operation - archivist systems are not mission critical, and
may often operate in burst mode: a lot of work is received
concomitantly, pushing the system to its limits, and then nothing else
happens for a long time.

Maintainance - Downtime is not an issue

Quality requirements - errors build distrust and may prevent the users
of adhering to the archivist software-assisted routine. Escriba should
run with an acceptable level of service even in the presence of errors
to justify its adoption.

Fault tolerance - From the outset we know that faults will occur, and
that we must design a software and network infrastructure that can deal
with these faults, and provide an acceptable level of service even in
the presence of faults.

Concurrency model
~~~~~~~~~~~~~~~~~

At the present, `PEP 703`_ is `expected to be accepted`_ by the Python
Steering Council. Which, as good as it sounds, means that we still have
to work with the GIL for some few years more. Until then, that means
that Python offers us 3 models of concurrency:

- proccess: concurrent and parallel-capable execution, preemptive scheduling
- thread: concurrent execution, preemptive scheduling
- coroutine: concurrent execution, cooperative scheduling

.. _PEP 703: https://peps.python.org/pep-0703/
.. _expected to be accepted: https://discuss.python.org/t/a-steering-council-notice-about-pep-703-making-the-global-interpreter-lock-optional-in-cpython/30474

Each concurrency model has its benefits and drawbacks and we intend to
choose when to use each one counsciously.

We partition the software into a number of independent processes that
reflect all the truly concurrent tasks in our real world activity. A
system which is designed to be implemented as a number of independent
concurrent processes can be implemented on a multi-processor or run on a
distributed network of processors. Each independent activity should be
performed in a completely isolated process. Such processes should share
no data, and only communicate by message passing.

When we partition a problem into a number of concurrent processes we can
arrange that all the processes respond to the same messages (ie they are
polymorphic,) and that they follow the same message passing interface.

Since nothing is shared, everything necessary to perform a distributed
computation must be copied.

As the operating system processes and threads are not lightweight,
within each parallel process we adopt cooperative multitasking as much
as viable for a high degree of concurrency and efficiency.

Storage layer
-------------

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

Content-addressable Storage
~~~~~~~~~~~~~~~~~~~~~~~~~~~

I feel that Escriba will develop towards a `Content-addresable storage`_
instead of a Location-based storage. The first reason is because that
approach will bring us some resilience against the evolving layout of
the underneath filesystem. The second reason is because CAS systems
ensure that the files within them are unique, and because changing the
file will result in a new key, CAS systems provide assurance that the
file is unchanged. That means that a CAS would bring us the desired
properties of data deduplication and integrity.

.. _Content-addresable storage: https://en.wikipedia.org/wiki/Content-addressable_storage
