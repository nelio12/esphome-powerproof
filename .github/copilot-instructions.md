<!--
Repo-specific instructions for AI coding agents.
Keep edits small and follow established patterns. This file is intentionally concise.
-->

# Copilot instructions for esphome-megatec-ups

Purpose: provide immediate, actionable info an AI agent needs to modify, extend, or debug this ESPHome external component.

Core overview
- This repository implements an ESPHome external component (`components/powermust/`) that communicates with UPS devices using the Megatec protocol over UART.
- The component is built as a subclass of `uart::UARTDevice` and `PollingComponent`. The main logic is in `powermust.cpp` and the public API and macros are in `powermust.h`.

Key files to reference
- `components/powermust/powermust.h` — entity macro definitions (e.g. `POWERMUST_SENSOR`, `POWERMUST_SWITCH`), public API, and member declarations.
- `components/powermust/powermust.cpp` — state machine: queue/command/poll handling, parsing of Q1/F/I frames, publishing with `publish_state`.
- `components/powermust/switch/powermust_switch.cpp` — how switch write operations enqueue commands.
- Example configs: `esp32-example.yaml`, `esp8266-example.yaml` — show how the component is consumed as `external_components` and how `uart.debug` is configured.
- Tests and traces: `tests/*.yaml` contains manual trace examples that show expected UART frames.

Project-specific patterns and rules (must follow)
- Entity macros: always use provided macros in `powermust.h` when declaring new sensors/switches/text sensors. The macros also register polling commands via `add_polling_command_`.
- Polling & commands: commands are stored in a fixed-size array (`used_polling_commands_`) and polled by `send_next_poll_()`. Do not replace with dynamic containers without ensuring memory safety on embedded targets.
- State machine: preserve the states `STATE_IDLE`, `STATE_POLL`, `STATE_COMMAND`, `STATE_POLL_COMPLETE`, `STATE_COMMAND_COMPLETE`, `STATE_POLL_CHECKED`, `STATE_POLL_DECODED`. Add decoding logic by following existing `switch` branches in `powermust.cpp`.
- Logging: use `ESP_LOGD`, `ESP_LOGI`, `ESP_LOGW`, `ESP_LOGE` consistently. `dump_config()` uses `LOG_SENSOR`, `LOG_BINARY_SENSOR`, `LOG_TEXT_SENSOR` macros — keep those for consistency.
- Language: source comments may include Spanish; do not change log tag names (e.g. `TAG = "powermust"`) or remove contextual comments unless cleaning up.

Build, run, and debug workflow (explicit)
- Install esphome CLI: `pip3 install esphome`.
- To validate, build and run the example device with external components set to this repo (scripts wrap this):
  - `./test-esp32.sh run esp32-example.yaml` — runs esphome using the `external_components` substitutions in the example.
  - `./test-esp8266.sh run esp8266-example.yaml`.
- For parsing / UART debugging, enable higher logger level in YAML and configure `uart.debug` (see examples and README). This prints raw frames into ESPHome logs and is the primary debug approach.

Integration points and constraints
- This component interacts only with ESPHome internals (UART, sensors, switches, logging). Do not add external network libraries; integrations should use `api`, `mqtt`, or `logger` as in examples.
- Keep heap/stack cost in mind: code runs on ESP8266/ESP32. Prefer stack allocation or small fixed-size buffers (existing code uses `POWERMUST_READ_BUFFER_LENGTH = 110`).

Small contract for changes (inputs / outputs)
- Inputs: new polling commands, entity declarations (macros), changes to parsing logic.
- Outputs: `publish_state` calls on sensors/binary sensors/text sensors/switches; log entries using `ESP_LOG*`.
- Success criteria: new entities appear in `dump_config()` and example YAMLs build with `esphome run` and produce expected log output with `uart.debug` enabled.

Examples (where to change and how)
- To add a new Q1 value: add a `POWERMUST_SENSOR(my_new_value, Q1, float)` in `powermust.h`; decode and assign the parsed value inside the `POLLING_Q1` decode block in `powermust.cpp`; then publish it in the `STATE_POLL_DECODED` -> `POLLING_Q1` case.
- To add a new command-switch: add `POWERMUST_SWITCH(my_switch, Q1)` in `powermust.h`, set `on_command` in YAML `switch` config as in `esp32-example.yaml`, and ensure the code that enqueues commands uses `queue_command_` / `switch_command`.

What not to change without attention
- Do not remove the polling registration macros or `add_polling_command_` usage — that breaks automatic polling rotation.
- Do not convert fixed buffers/arrays to dynamic containers without verifying memory usage on both ESP32 and ESP8266.

If you need more context
- Start by reading `powermust.h` (macros and API) then `powermust.cpp` (state handling and parsing). Use `tests/*.yaml` to see real-world UART traces and expected formats.

If anything here is unclear or you'd like the instructions expanded for a specific task (e.g. add a sensor, add a command switch, improve parsing robustness), tell me which task and I'll expand the instructions and provide concrete code edits or tests.
