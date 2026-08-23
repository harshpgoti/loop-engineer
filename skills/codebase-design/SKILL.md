---
name: codebase-design
description: Shared vocabulary for designing deep modules - module, interface, depth, seam, adapter, leverage, locality. Use when placing a seam, shaping an interface, deciding what to test, judging whether a module earns its keep, or when another skill needs this vocabulary.
---

# Codebase Design

Design **deep** modules: a lot of behaviour behind a small interface, at a clean seam,
testable through that interface. Use these words exactly. Consistent language is the point -
substituting "component", "service", "API", or "boundary" costs the shared meaning.

## Glossary

**Module** - anything with an interface and an implementation. Scale-agnostic on purpose: a
function, a class, a package, a tier-spanning slice. Not: unit, component, service.

**Interface** - everything a caller must know to use the module correctly. The type
signature, but also invariants, ordering constraints, error modes, required configuration,
performance characteristics. Not: API, signature - those name only the type-level surface.

**Implementation** - what is inside. Distinct from adapter: a module can be a small adapter
with a large implementation (a Postgres repository) or a large adapter with a small one (an
in-memory fake).

**Depth** - leverage at the interface: how much behaviour a caller or a test can exercise per
unit of interface it has to learn. **Deep** = large behaviour, small interface. **Shallow** =
interface nearly as complex as the implementation.

**Seam** - a place where you can alter behaviour without editing in that place. Where a
module's interface lives. Where to put the seam is its own decision, separate from what goes
behind it. Not: boundary.

**Adapter** - a concrete thing satisfying an interface at a seam. Names a role, not a
substance.

**Leverage** - what callers get from depth: more capability per unit of interface learned.

**Locality** - what maintainers get from depth: change, bugs, and verification concentrate in
one place instead of spreading across callers.

## Deep and shallow

```text
deep                              shallow
+-------------------+             +-----------------------------------+
|  small interface  |             |         large interface           |
+-------------------+             +-----------------------------------+
|                   |             |      thin implementation          |
|   lots of         |             +-----------------------------------+
|   implementation  |
+-------------------+
```

Designing an interface, ask: can I cut a method? Can I simplify a parameter? Can I hide more
behind it?

## Principles

- **Depth is a property of the interface, not the implementation.** A deep module can be
  built internally from small swappable parts; they just are not part of the interface. It
  can have internal seams its own tests use, as well as the external seam at its interface.
- **The deletion test.** Imagine deleting the module. If complexity vanishes, it was a
  pass-through. If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.** Callers and tests cross the same seam. Wanting to
  test past the interface means the module is the wrong shape.
- **One adapter is a hypothetical seam. Two adapters is a real one.** Do not introduce a
  seam until something actually varies across it - typically production plus test.
- **Fewer seams is better.** Each one is a contract somebody has to hold in their head.

## Designing for testability

Accept dependencies, do not construct them:

```python
def process_order(order, payment_gateway): ...        # testable
def process_order(order): gateway = StripeGateway()   # not
```

Return results rather than mutating in place. Keep the surface small: fewer methods means
fewer tests, fewer parameters means simpler setup.

## Dependency categories

Classify a module's dependencies - the category decides how it gets tested across its seam.

| Category | What it is | How it is tested |
|----------|------------|------------------|
| **In-process** | Pure computation, in-memory state, no I/O | Directly through the new interface. No adapter |
| **Local-substitutable** | Has a real local stand-in (PGLite for Postgres, in-memory FS) | Stand-in runs in the suite. Seam stays internal |
| **Remote but owned** | Your own service across a network | Port at the seam; HTTP adapter in production, in-memory adapter in tests |
| **True external** | A third party you do not control (Stripe, a clearinghouse) | Injected port; mock adapter in tests |

## Deepening a cluster

Replace, do not layer. Old unit tests written against the shallow modules become waste once
tests exist at the deepened interface - delete them. New tests assert observable outcomes
through the interface, so they survive internal refactors. A test that has to change when the
implementation changes is testing past the interface.

When the right interface is genuinely unclear, design it twice: sketch two or three
deliberately different shapes - one minimising the interface, one maximising flexibility, one
optimising the common caller - and compare them on depth, locality, and seam placement before
choosing. First ideas are rarely the best ones.

## Where this shows up

- `skills/implementation-planner/SKILL.md` - before code edits
- `skills/tdd/SKILL.md` - agreeing the seams a task is tested at
- `skills/code-reviewer/SKILL.md` - the standards axis
- `CONTEXT.md` `## Language` - domain names for the seams this vocabulary places
