from yoshimi import test
from yoshimi.content import Content
from yoshimi.browse import Policy


class TestPolicy(test.TestCase):
    def setUp(self):
        self.policy = Policy()

        c = Content()
        c.id = 2
        self.policy._target = c

    def test_can_select_when_location_is_not_self(self):
        c1 = Content()
        c1.id = 5
        self.assertTrue(self.policy.can_select(c1))

    def test_can_not_select_location_when_location_is_self(self):
        c1 = Content()
        c1.id = 2
        self.assertFalse(self.policy.can_select(c1))

    def test_can_select_when_not_child_of_self(self):
        c1 = Content()
        c1.id = 1
        c2 = Content(parent=c1)
        c2.id = 4
        self.assertTrue(self.policy.can_select(c2))

    def test_can_not_select_when_child_of_self(self):
        c1 = Content()
        c1.id = 2
        c2 = Content(parent=c1)
        c2.id = 5
        self.assertFalse(self.policy.can_select(c2))

    def test_selection_input_type_when_single(self):
        self.policy.selection = 'single'
        self.assertEqual('radio', self.policy.selection_input_type)

    def test_selection_input_type_when_multiple(self):
        self.policy.selection = 'multiple'
        self.assertEqual('checkbox', self.policy.selection_input_type)
