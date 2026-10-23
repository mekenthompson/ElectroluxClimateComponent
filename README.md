# ElectroluxClimateComponent

Local control for Kelvinator and Electrolux air conditioners that use a Broadlink module of type `0x4f9b`.

This fork aligns the climate entity with Home Assistant 2026.10. It is not an upstream pull request yet.

- HVAC action comes from the compressor, heater, fan, and defrost bits.
- 8°C heat is the Freeze protection preset, not Heat/cool.
- One Kelvinator device per unit. Display and Sleep are switches on that device.
