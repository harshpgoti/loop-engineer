# /network-architect

Design the network topology for a deployment: subnets, firewall rules, DNS,
load balancers, VPN/zero-trust, ingress, observability. Read-only design
review. Use when adding a new environment, changing the topology, or auditing
an existing topology.

## How To Interpret

If the user says `/network-architect`, `design the network`, `draw the
topology`, `plan the firewall rules`, or asks for a network design, execute
this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/network-architect/SKILL.md`
3. the current network topology (if any)
4. the deployment requirements (regions, subnets, traffic shape)

## Loop

```text
STATE the requirements -> DRAW the topology (subnets, firewall, DNS, LB, VPN, ingress, observability) -> CITE the principle for each design choice -> SPEC the config
```

## Output

A topology diagram (ASCII or Mermaid) plus a config spec per layer. Each
design decision is cited with the principle behind it.

## Continuation

The chain produces a design; the implementer is the maintainer. The next
`/deployment-plan` run turns the design into an implementation plan.