from yoshimi import test
from yoshimi.content import Content, Location
from yoshimi.browse import Policy


class TestPolicy(test.TestCase):
    def setUp(self):
        self.policy = Policy()

        c = Content()
        c.main_location.id = 2
        self.policy._target = c.main_location

    def test_can_select_when_location_is_not_self(self):
        c1 = Content()
        c1.main_location.id = 5
        self.assertTrue(self.policy.can_select(c1.main_location))

    def test_can_not_select_location_when_location_is_self(self):
        c1 = Content()
        c1.main_location.id = 2
        self.assertFalse(self.policy.can_select(c1.main_location))

    def test_can_select_when_not_child_of_self(self):
        c1 = Content()
        c1.main_location.id = 1
        c2 = Content(parent=c1.main_location)
        c2.main_location.id = 4
        self.assertTrue(self.policy.can_select(c2.main_location))

    def test_can_not_select_when_child_of_self(self):
        c1 = Content()
        c1.main_location.id = 2
        c2 = Content(parent=c1.main_location)
        c2.main_location.id = 5
        self.assertFalse(self.policy.can_select(c2.main_location))

    def test_can_not_select_when_destination_is_same_content_object(self):
        # Test structure:
        # c1.l1 (1)
        #   c2.l2 (3, target)
        # c1.main_location (2, loc)
        #   c2.main_location (4)
        c1 = Content()
        c1.main_location.id = 2
        l1 = Location()
        l1.id = 1
        c1.locations.append(l1)

        c2 = Content(parent=c1.main_location)
        c2.main_location.id = 4
        l2 = Location(parent=l1)
        l2.id = 3
        c2.locations.append(l2)

        self.policy._target = l2

        self.assertFalse(self.policy.can_select(c2.main_location))

    def test_selection_input_type_when_single(self):
        self.policy.selection = 'single'
        self.assertEqual('radio', self.policy.selection_input_type)

    def test_selection_input_type_when_multiple(self):
        self.policy.selection = 'multiple'
        self.assertEqual('checkbox', self.policy.selection_input_type)
