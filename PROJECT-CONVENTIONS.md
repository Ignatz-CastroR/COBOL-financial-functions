# Project Conventions

## Mainframe conformance [binding on every source file in SRC/]

Every COBOL and FORTRAN file in `SRC/` must remain conformant with what a
modern IBM z/OS compiler [Enterprise COBOL for the COBOL modules, IBM's
supported FORTRAN toolchain for the modules under `SRC/FORTRAN-MODULES/`]
could accept, in principle, without modification. This project is built
and tested locally under GnuCOBOL, since that is the compiler available
during development, but GnuCOBOL is a development convenience, not the
target platform. The target platform is z/OS.

This is not a vague aspiration; it constrains specific choices every time
new code is written:

1. **No GnuCOBOL-only dialect extensions or compiler directives.** If a
   language feature only exists because of a GnuCOBOL-specific `$SET`
   directive or a GnuCOBOL dialect extension, it does not belong in
   `SRC/`. When in doubt, prefer the feature described in the COBOL
   standard over a convenience specific to one compiler.

2. **No shelling out to the operating system.** `CALL "SYSTEM"` and
   similar mechanisms assume a POSIX-style process model that a z/OS
   batch job does not provide in the same way. Nothing in `SRC/` may
   depend on spawning an external OS process.

3. **No Unix-filesystem-specific assumptions.** Any function that reads
   or writes a file must be written with awareness that its eventual
   target storage model is QSAM or VSAM datasets, not a POSIX filesystem
   path. Where local development requires a flat file for convenience
   [test fixtures, for instance], that dependency stays inside `TESTS/`
   and `VALIDATION/`, never inside `SRC/` itself.

4. **Every deliberate deviation gets documented, not silently allowed.**
   If a specific function genuinely cannot avoid a GnuCOBOL-specific
   convenience during this development phase, that exception is recorded
   in that function's own domain README, with the reason stated plainly,
   rather than left for a future reader to discover by surprise.

## Why this exists

This project's audience is banking, insurance, and government
recruiters, the three industries where COBOL demand actually
concentrates, and where mainframe deployment is the norm rather than the
exception. A repository that only proves it compiles under a hobbyist
compiler on a laptop is a materially weaker claim than one that was
written, from its first line, to also survive a real mainframe compiler.
This convention exists to make that second, stronger claim true, not just
stated.

## Relationship to MAINFRAME/

This convention is what eventually makes `MAINFRAME/` meaningful. The JCL,
DB2, and CICS artifacts planned for that folder only make sense as a
deployment wrapper around code that was already written to be deployable
in the first place. See `MAINFRAME/README.md` for that folder's own
scope.
