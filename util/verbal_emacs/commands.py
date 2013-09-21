from dragonfly import MappingRule, Alternative, RuleRef
from proxy_nicknames import Text, Key

from verbal_emacs.common import NumericDelegateRule, ruleDigitalInteger
from verbal_emacs.operators import ruleOperatorApplication

class PrimitiveCommand(MappingRule):
  mapping = {
    "vim scratch":Key("X"),
    "vim chuck":Key("x"),
    "vim undo":Key("u"),
    "plap":Key("P"),
    "plop":Key("p"),
    "megaditto":Text("."),
  }
rulePrimitiveCommand = RuleRef(PrimitiveCommand(), name="PrimitiveCommand")

class Command(NumericDelegateRule):
  spec = "[<count>] <command>"
  extras = [Alternative([ruleOperatorApplication,
                         rulePrimitiveCommand,
                        ], name="command"),
            ruleDigitalInteger[4]]

  def value(self, node):
    rval = "c", NumericDelegateRule.value(self, node)
    return rval
ruleCommand = RuleRef(Command(), name="Command")
