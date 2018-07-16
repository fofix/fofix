Contributing to FoFiX
=====================

As an open source project, FoFiX welcomes contributions of many forms.


Bug reporting
-------------

Please use the [issue tracker on GitHub](https://github.com/fofix/fofix/issues).

Be sure to include all relevant information (traceback, version, reproducing
steps, …).


Patches submission
------------------

Patches are welcome either as [pull requests on GitHub](https://github.com/fofix/fofix/pulls).
Please avoid duplicated patches, and make small PR.

To avoid duplicated work:
- if there is no issue about your bug, create one
- tell people that you're working on a patch.

Here are some guidelines:
- fork the repo
- create a topic branch based on `master`:

        git checkout -b my-topic-branch master


- hack
- write [logical unit commits following basic guidelines](#git-commit-guidelines)
- push your branch:

        git push origin my-topic-branch

- submit a [pull request](https://help.github.com/articles/creating-a-pull-request/) to `master`.


Then, your pull request (PR) will be reviewed. This could take several days,
which is also good for maturity.

After your pull request is merged, do not forget to:
- remove your topic branch
- update your `master` branch with upstream version
- celebrate :).


Git Commit Guidelines
---------------------

In order to make commit messages readable, they should follow some rules, based
on *community standards*:
- separate subject from body with a blank line
- limit the subject line to 50 characters
- capitalize the subject line
- do not end the subject line with a period
- use the imperative mood in the subject line
- wrap the body at 72 characters
- use the body to explain what and why vs. how.


This will look like this:

    Capitalized, short (50 chars or less) summary

    More detailed explanatory text, if necessary.  Wrap it to about 72
    characters or so.  In some contexts, the first line is treated as the
    subject of an email and the rest of the text as the body.  The blank
    line separating the summary from the body is critical (unless you omit
    the body entirely); tools like rebase can get confused if you run the
    two together.

    Write your commit message in the imperative: "Fix bug" and not "Fixed bug"
    or "Fixes bug."  This convention matches up with commit messages generated
    by commands like git merge and git revert.

    Further paragraphs come after blank lines.

    - Bullet points are okay, too

    - Typically a hyphen or asterisk is used for the bullet, preceded by a
      single space, with blank lines in between, but conventions vary here

    - Use a hanging indent

    Fix #1234
    Ref #2345


You can test your commit with [gitlint](http://jorisroovers.github.io/gitlint/)
before pushing your code.


For more information about those community standards, take a look at:
- Tim Pope's [A Note About Git Commit Messages](https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html)
- Chris Beams's summary: [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/)
- Pro Git book: [Contributing to a Project](https://www.git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project#_commit_guidelines)
- Wikipedia: [Atomic commit](https://en.wikipedia.org/wiki/Atomic_commit#Atomic_commit_convention)
- Thoughtbot's [5 Useful Tips For A Better Commit Message](https://robots.thoughtbot.com/5-useful-tips-for-a-better-commit-message).


Coding style
------------

Since most of the code is written in Python, please, follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/).


Get in touch
------------

You can also drop by the #fofix channel on oftc.net ([web interface](https://webchat.oftc.net/)).
