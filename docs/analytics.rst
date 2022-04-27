#########
Analytics
#########

Overview

Currently breaking, but outdated, mermaid diagrams:


.. image:: assets/data_io.png

.. mermaid::

    flowchart TD
        s1[import current state into postgres]
        s2[process in postgres with dbt]
        s3[update spellcheck queue table in postgres]
        s4[trigger spellcheck processing]
        s5[iteratively send items from spellcheck queue to languagetool container]
        s6[process spellcheck errors in postgres with dbt]
        style s4 stroke-width:2px, stroke-dasharray: 5 5
        s1 --&gt; s2
        s2 --&gt; s3
        s3 -. poll finished .-&gt; s4
        s4 --&gt; s5
        s5 --&gt; s6

Data import and processing

.. image:: assets/analytics_overview.png

.. mermaid::

    sequenceDiagram
        participant F as fastapi
        participant P as postgres
        participant R as rpc-dbt
        participant E as elastic
        autonumber
        note left of F: POST /run-analytics
        rect var(--md-footer-bg-color--dark)
        note over F: import into postgres
        F-&gt;&gt;E: load collections
        E--&gt;&gt;F: collections
        F-&gt;&gt;E: load materials
        E--&gt;&gt;F: materials
        F-&gt;&gt;P: store in postgres
        end
        rect var(--md-footer-bg-color--dark)
        note over F: run analytics
        F--)R: rpc: send run analytics
        R-&gt;&gt;P: runs analytics models
        note right of F: poll finished ...
        end
        rect var(--md-footer-bg-color--dark)
        note over F: store historical changes
        F--)R: rpc: send run snapshots
        R-&gt;&gt;P: runs snapshots
        note right of F: poll finished ...
        end
        note left of F: call spellcheck()

Spellcheck processing

.. image:: assets/spellcheck.png

.. mermaid::

    sequenceDiagram
        participant F as fastapi
        participant P as postgres
        participant R as rpc-dbt
        participant L as languagetool
        autonumber
        note left of F: call spellcheck()
        rect var(--md-footer-bg-color--dark)
        note over F: read from spellcheck queue
        F-&gt;&gt;P: load spellcheck items
        P--&gt;&gt;F: spellcheck items
        end
        rect var(--md-footer-bg-color--dark)
        note over F: read from spellcheck queue
        loop spellcheck items
            F-&gt;&gt;L: do spellcheck
            L--&gt;&gt;F: spellcheck error ?
            F-&gt;&gt;P: store error
        end
        end
        rect var(--md-footer-bg-color--dark)
        note over F: run spellcheck
        F--)R: rpc: send run spellcheck
        R-&gt;&gt;P: runs spellcheck models
        note right of F: poll finished ...
        end