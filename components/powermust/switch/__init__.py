import esphome.codegen as cg
from esphome.components import switch
import esphome.config_validation as cv
from esphome.const import (
    CONF_BEEPER,
    CONF_NAME,
    ICON_POWER,
    ICON_TIMER,
)

from .. import CONF_POWERMUST_ID, POWERMUST_COMPONENT_SCHEMA, powermust_ns

DEPENDENCIES = ["uart"]

# === Comandos existentes ===
CONF_QUICK_TEST = "quick_test"
CONF_DEEP_TEST = "deep_test"
CONF_TEN_MINUTES_TEST = "ten_minutes_test"

# === NUEVOS: Shutdown ===
CONF_SHUTDOWN = "shutdown"              # S<n>
CONF_SHUTDOWN_RESTORE = "shutdown_restore"  # S<n>R<m>
CONF_CANCEL_SHUTDOWN = "cancel_shutdown"   # C

# === Mapeo: (comando ON, comando OFF) ===
TYPES = {
    CONF_BEEPER: ("Q", "Q"),                    # Toggle beeper
    CONF_QUICK_TEST: ("T", "CT"),
    CONF_DEEP_TEST: ("TL", "CT"),
    CONF_TEN_MINUTES_TEST: ("T10", "CT"),
    # --- NUEVOS ---
    CONF_SHUTDOWN: ("S05", None),               # Apagar en 5 min (personalizable)
    CONF_SHUTDOWN_RESTORE: ("S05R0030", None),  # Apagar 5 min, restaurar en 30 min
    CONF_CANCEL_SHUTDOWN: ("C", None),          # Cancelar
}

# Iconos personalizados
ICONS = {
    CONF_BEEPER: ICON_POWER,
    CONF_QUICK_TEST: ICON_TIMER,
    CONF_DEEP_TEST: ICON_TIMER,
    CONF_TEN_MINUTES_TEST: ICON_TIMER,
    CONF_SHUTDOWN: "mdi:power-plug-off",
    CONF_SHUTDOWN_RESTORE: "mdi:restart",
    CONF_CANCEL_SHUTDOWN: "mdi:cancel",
}

PowermustSwitch = powermust_ns.class_("PowermustSwitch", switch.Switch, cg.Component)

PIPSWITCH_SCHEMA = switch.switch_schema(
    PowermustSwitch,
    block_inverted=True,
).extend(cv.COMPONENT_SCHEMA)


def validate_shutdown_command(config):
    """Valida que S<n> y S<n>R<m> tengan formato correcto"""
    type_ = config["type"]
    if type_ == CONF_SHUTDOWN:
        cmd = config.get("on_command", "S05")
        if not (cmd.startswith("S") and len(cmd) == 3 and cmd[1:].isdigit()):
            raise cv.Invalid(f"shutdown: comando debe ser S + 2 dígitos (ej: S05), recibido: {cmd}")
    elif type_ == CONF_SHUTDOWN_RESTORE:
        cmd = config.get("on_command", "S05R0030")
        if not (cmd.startswith("S") and "R" in cmd and len(cmd) >= 6):
            raise cv.Invalid(f"shutdown_restore: debe ser S<n>R<m> (ej: S05R0030), recibido: {cmd}")
    return config


CONFIG_SCHEMA = POWERMUST_COMPONENT_SCHEMA.extend(
    {cv.Optional(type): PIPSWITCH_SCHEMA for type in TYPES}
).extend({
    cv.Optional(CONF_SHUTDOWN): PIPSWITCH_SCHEMA.extend({
        cv.Optional("on_command", "S05"): cv.string,
    }),
    cv.Optional(CONF_SHUTDOWN_RESTORE): PIPSWITCH_SCHEMA.extend({
        cv.Optional("on_command", "S05R0030"): cv.string,
    }),
}).add_extra(validate_shutdown_command)


async def to_code(config):
    paren = await cg.get_variable(config[CONF_POWERMUST_ID])

    for type_, (default_on, default_off) in TYPES.items():
        if type_ in config:
            conf = config[type_]
            var = await switch.new_switch(conf)

            # Usar comando personalizado si existe
            on_cmd = conf.get("on_command", default_on) if "on_command" in conf else default_on
            cg.add(var.set_on_command(on_cmd))

            if default_off is not None:
                cg.add(var.set_off_command(default_off))

            await cg.register_component(var, conf)
            cg.add(getattr(paren, f"set_{type_}_switch")(var))
            cg.add(var.set_parent(paren))
