import venusian


class Policy:
    selection = 'single'
    can_select_self = False

    _target = None

    def can_select(self, possible_destination):
        if self.can_select_self:
            return True

        if self._target.id == possible_destination.id:
            return self.can_select_self

        if possible_destination.parent:
            if self._target.id == possible_destination.parent.id:
                return self.can_select_self

        target_location_ids = [l.id for l in self._target.content.locations]
        if possible_destination.id in target_location_ids:
            return False

        return True

    @property
    def selection_input_type(self):
        return 'checkbox' if self.selection == 'multiple' else 'radio' 


class BrowsePolicy:
    _policies = {}

    def __init__(self, policy):
        self.policy = policy

    @classmethod
    def register(cls, policy_name, policy_callable):
        cls._policies[policy_name] = policy_callable

    @classmethod
    def get(cls, policy_name, target):
        policy_getter_func = cls._policies.get(policy_name, Policy)
        p = policy_getter_func()
        p._target = target

        return p


class browse_policy(object):
    def __init__(self, policy_name):
        self.policy_name = policy_name

    def register(self, scanner, name, wrapped):
        BrowsePolicy.register(self.policy_name, wrapped)

    def __call__(self, wrapped):
        venusian.attach(wrapped, self.register, category='yoshimi')
        return wrapped


@browse_policy('move')
def policy():
    return Policy()
