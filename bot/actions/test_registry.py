from bot.actions.registry import ActionRegistry
from bot.localizer import Localizer
from bot.types import ActionType


class TestActionRegistryStampsActionType:
    def test_get_returns_action_tagged_with_its_registry_key(self):
        registry = ActionRegistry(localizer=Localizer())

        action = registry.get(ActionType.TRANSLATE)

        assert action.action_type == ActionType.TRANSLATE

    def test_different_keys_yield_differently_tagged_actions(self):
        registry = ActionRegistry(localizer=Localizer())

        assert registry.get(ActionType.ANALYZE).action_type == ActionType.ANALYZE
        assert registry.get(ActionType.CORRECT).action_type == ActionType.CORRECT
