# Compact buffer decision checkpoint — 2026-11-02

Historical checkpoint: the later [latched-trip and layout review](latched-trip-and-layout-review.md)
supersedes the numerical failure counts and next-action status below. Preserve this
record as the evidence that prompted the latching/event-handling change.

The preceding goal turn was a status restatement, not engineering progress. This
turn adds reproducible alternative-buffer evidence, a functional electrical
definition and preliminary full-function cost allowances. The original eight-item
goal remains active.

## Buffer experiment

`make buffer-study` evaluates six cases for each of six variants. The documented
Eaton HV1860-2R7107-R cell is an alternative, not a replacement of the verified
350 F-cell reference. Manufacturer facts and separate heat-capacity assumptions
are in `data/compact_buffer.yaml`. Nominal, minimum initial capacitance, combined
initial-tolerance/aging and heat-capacity brackets are retained.

The 22s compact bank changes cell-body volume from 1.178 to 0.358 L and cell mass
from 1.32 to 0.44 kg. It also changes nominal bank capacitance from 15.91 to 4.545 F
and ESR from 0.0704 to 0.264 ohm. Body volume excludes terminals, insulation,
balancing, protection, supports and wiring. No complete enclosure fit is claimed.

Twenty integrations complete, with maximum energy residual fraction 1.70e-6;
sixteen fail the bounded solver-work check. Completed heavy-set cases retain low
tracking error. The aged compact bank reaches about 40.37 V in the single heavy
set, close to the proposed 40 V operating threshold. Fast and endurance behavior
is not rescued by the smaller bank. There is no independent convergence study
for this alternative yet.

A diagnostic run isolates the non-latching voltage-trip problem. Immediately
before buffered mains-loss integration fails at about 4.16983 s, the inverter bus
is 40.0003 V while the internal bank is about 44.7556 V. Immediately before the
dump-failure integration fails at about 1.48782 s, the bus is 49.9980 V while the
bank is about 48.0194 V. These bracket the 40 V undervoltage and 50 V overvoltage
thresholds. The current algebraic enable logic can repeatedly switch states as
the bus recovers. These are unresolved hybrid-model events, not qualified
physical shutdowns and not passing product cases.

The first long experiment was deliberately interrupted after a separate
2000-step diagnostic reproduced the problem. The published experiment uses a
2000-internal-step work bound per requested output interval, without relaxing
tolerances or maximum step size. It retains every failure rather than hanging
or reporting a nominal substitute. The published fingerprint matches the study
source and inputs. The verified baseline fingerprint still matches its source.

The recorded cell RMS screen compares the initial open-air datasheet rating;
it is not an aged-cell or enclosed-pack current qualification. With doubled ESR,
the current for the same resistive heat would decrease by sqrt(2), before any
change in cooling. The completed aged heavy-set RMS current is about 3.9 A,
below even that reduced comparison. Real cell imbalance and balancing loss,
leakage, startup/precharge and pack thermal gradients remain unmodeled.

## Electrical and cost definition

`make electrical` generates a functional semantic netlist, SVG and preliminary
harness register from `configs/electrical.yaml`. All 84 ports connect exactly
once. It includes protective earth, isolation-related functions, precharge,
bank monitoring, dump, proposed phase-brake transfer, independent supervision,
sensing, mount state and peer communication. No real pinout or switching circuit
is inferred from semantic bundles. Wire sizing, length, connectors and routes
remain explicitly TBD. The SVG was rendered and visually inspected.

`make preliminary-costs` allocates all 24 electrical functions exactly once,
plus mechanical support, drivetrain, guide, cable, arrestor, harness, interface,
packaging, board and three alternative adapter types. All 36 cost lines are
planning allowances. No supplier quote is included. Totals distinguish module
quantities, paired systems, accessory alternatives, labor, yield, overhead,
warranty, distribution, margin and NRE. Wide corner bounds demonstrate unresolved
economics; they are not market-price predictions or statistically calibrated
estimates. Required functions added by later design work must receive new lines.

## Verification and next work

Input checking passes. The 33 targeted buffer/coupled/engineering tests pass.
The earlier 190-test full-suite result remains baseline evidence; no new claim
of a full 192-test run is made. Diagnostic checks reject missing earth and
invalid connectivity. Existing source/configuration fingerprints remain valid.

Next implement explicit voltage-trip latching, defined reset semantics and
event handling in the coupled reference. Test a persistent trip, a recovering
bus, one-sided pair faults and conservation across a mode change. Rerun the
reference convergence/uncertainty suite and the compact-buffer experiment.
Then integrate actual geometry, protection, harness and cooling into one
candidate, including clearances, rope traverse and mechanical load paths.
Do not mark the goal complete: detailed compact CAD, pin-level preliminary
circuits, harness engineering, structural/fault work and final evidence audit
remain open.
