# MAINFRAME/

## Purpose

This folder is the future home of every artifact needed to actually deploy
and run this project's COBOL and FORTRAN code on a real IBM z/OS mainframe:
JCL job control language, DB2 data definition language and copybooks, and
CICS BMS map definitions.

It exists now, ahead of any content, as an explicit, honest placeholder
rather than as speculative filler. The author is presently learning z/OS,
JCL, DB2, and CICS. As that expertise develops, this folder will be
populated with real, tested artifacts, not aspirational stubs.

## Why this is separate from SRC/

`SRC/` holds portable business logic: functions that take numbers in and
return numbers out, with no dependency on any particular deployment
environment. Everything in `SRC/` is written to remain conformant with a
modern IBM z/OS COBOL and FORTRAN compiler, per `PROJECT-CONVENTIONS.md`
at the project root.

`MAINFRAME/` holds the opposite kind of artifact: content that is
inherently tied to one specific deployment environment and has no meaning
outside it. A JCL job, a DB2 table definition, and a CICS BMS map are not
business logic; they are the scaffolding that lets business logic actually
run inside a mainframe shop's operational environment. Keeping the two
concerns in separate folders means `SRC/` stays genuinely portable, and
`MAINFRAME/` stays honestly scoped to what it actually is.

## Planned structure, once populated

```
MAINFRAME/
    JCL/     Job control language for compiling, linking, and executing
             this project's programs and tests as batch jobs
    DB2/     Table definitions and copybooks for any function whose test
             fixtures or reference data are eventually served from DB2
             rather than from a flat file
    CICS/    BMS map definitions and any CICS-specific program
             considerations, if an interactive, transaction-driven
             demonstration is added later
```

## Status

Placeholder. No content yet. This section will be expanded with real
documentation as each subfolder receives its first artifact.
