# Open resistance-control foundation

Owner steering, 2026-11-02: an open system people can develop on top of; “the linux kernel of resistance training”.

The objective is a reusable engineering/control foundation, with the compact trainer as its reference implementation. The full engineering goal in goal.md remains active: an extensible API does not replace physical feasibility, coupled verification, electrical/mechanical definition, costing or review evidence.

Core contracts:

- SI quantities and documented force, payout, torque and power signs.
- Independent mechanical, electrical and thermal component parameters with sources, units, rated conditions and uncertainty. No silent default for missing vendor ratings.
- Reproducible one/two-unit scenarios, fault injection and replayable state/energy traces.
- Local protection semantics independent of optional peer coordination. Simulation protection is not certified hardware safety.
- Independent conservation, analytical and convergence checks that extension authors can run against a new component/model.
- Public configuration schemas and versioned source files. Keep the vendor-specific reference data separate from solver/model logic.
- Hardware adapters and future human-interface applications must sit above these contracts; no physical output or high-force experiment is authorized by this project.

First implementation boundary: the coupled reference plant consumes sourced component data plus explicit, labeled modeling assumptions, and returns named states, forces, power flows, temperatures, fault outcomes and energy residuals. Contributors should be able to swap a motor/drive/supply/cable model and see which acceptance criteria or data gaps change.
