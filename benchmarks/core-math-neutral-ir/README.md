# Core-Math neutral IR research (#2427)

This directory validates the minimal neutral semantic roles already exercised by
#2433. It is a research gate, not production authority.

Current roles:
- carrier/type;
- constant;
- basis operation signature;
- generated-operation rule;
- expression AST;
- dependency edge;
- explicit partiality;
- projection/provenance envelope;
- canonical serialization.

Out of scope:
- final generated-operation identity (#2435);
- native surface syntax (#2429);
- Core bridges (#2430);
- a second standalone executor (#2428).

The exact-Q corpus is the first positive instance, not the definition of the IR.
