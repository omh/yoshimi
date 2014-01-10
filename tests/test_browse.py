from yoshimi import test
from yoshimi.content import Content
from yoshimi.browse import Policy


class TestPolicy:
    def setup(self):
        self.policy = Policy()

        c = Content()
        c.id = 2
        self.policy._target = c

    def test_can_select_when_location_is_not_self(self):
        c1 = Content()
        c1.id = 5
        assert self.policy.can_select(c1) == True

    def test_can_not_select_location_when_location_is_self(self):
        c1 = Content()
        c1.id = 2
        assert self.policy.can_select(c1) == False

    def test_can_select_when_not_child_of_self(self):
        c1 = Content()
        c1.id = 1
        c2 = Content(parent=c1)
        c2.id = 4
        assert self.policy.can_select(c2) == True

    def test_can_not_select_when_child_of_self(self):
        c1 = Content()
        c1.id = 2
        c2 = Content(parent=c1)
        c2.id = 5
        assert self.policy.can_select(c2) == False

    def test_selection_input_type_when_single(self):
        self.policy.selection = 'single'
        assert 'radio' == self.policy.selection_input_type

    def test_selection_input_type_when_multiple(self):
        self.policy.selection = 'multiple'
        assert 'checkbox' == self.policy.selection_input_type
