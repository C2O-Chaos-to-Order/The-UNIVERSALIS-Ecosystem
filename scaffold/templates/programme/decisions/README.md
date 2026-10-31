# Decision records

This file is not a decision. It does not review, accept, or authorize anything.

`verified`, `independently_reproduced`, `validated` and `authorized` evidence states require a JSON decision file in this directory that cites an owner or reviewer. `authorization_status` is a separate column from `evidence_status`. The default is `NOT_AUTHORIZED`. Tooling must not copy `evidence_status` into `authorization_status`, and an evidence_state of `authorized` does not set or imply `authorization_status` `AUTHORIZED`.

An authorization record sets `authorization_status` to `AUTHORIZED` and cites the target ids. An evidence decision does not authorize unless that authorization column is set on the decision itself.
