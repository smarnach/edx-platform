"""
Test the partitions and partitions service

"""

from unittest import TestCase
from mock import Mock

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from stevedore.extension import Extension, ExtensionManager
from xmodule.partitions.partitions import Group, UserPartition, UserPartitionError, USER_PARTITION_SCHEME_NAMESPACE
from xmodule.partitions.partitions_service import PartitionService


class TestGroup(TestCase):
    """Test constructing groups"""
    def test_construct(self):
        test_id = 10
        name = "Grendel"
        group = Group(test_id, name)
        self.assertEqual(group.id, test_id)    # pylint: disable=no-member
        self.assertEqual(group.name, name)

    def test_string_id(self):
        test_id = "10"
        name = "Grendel"
        group = Group(test_id, name)
        self.assertEqual(group.id, 10)    # pylint: disable=no-member

    def test_to_json(self):
        test_id = 10
        name = "Grendel"
        group = Group(test_id, name)
        jsonified = group.to_json()
        act_jsonified = {
            "id": test_id,
            "name": name,
            "version": group.VERSION
        }
        self.assertEqual(jsonified, act_jsonified)

    def test_from_json(self):
        test_id = 5
        name = "Grendel"
        jsonified = {
            "id": test_id,
            "name": name,
            "version": Group.VERSION
        }
        group = Group.from_json(jsonified)
        self.assertEqual(group.id, test_id)    # pylint: disable=no-member
        self.assertEqual(group.name, name)

    def test_from_json_broken(self):
        test_id = 5
        name = "Grendel"
        # Bad version
        jsonified = {
            "id": test_id,
            "name": name,
            "version": 9001
        }
        with self.assertRaisesRegexp(TypeError, "has unexpected version"):
            Group.from_json(jsonified)

        # Missing key "id"
        jsonified = {
            "name": name,
            "version": Group.VERSION
        }
        with self.assertRaisesRegexp(TypeError, "missing value key 'id'"):
            Group.from_json(jsonified)

        # Has extra key - should not be a problem
        jsonified = {
            "id": test_id,
            "name": name,
            "version": Group.VERSION,
            "programmer": "Cale"
        }
        group = Group.from_json(jsonified)
        self.assertNotIn("programmer", group.to_json())


class MockUserPartitionScheme(object):
    """
    Mock user partition scheme
    """
    def __init__(self, name="mock", current_group=None, **kwargs):
        super(MockUserPartitionScheme, self).__init__(**kwargs)
        self.name = name
        self.current_group = current_group

    def get_group_for_user(self, course_id, user, user_partition, track_function=None):  # pylint: disable=unused-argument
        """
        Returns the current group if set, else the first group from the specified user partition.
        """
        if self.current_group:
            return self.current_group
        groups = user_partition.groups
        if not groups or len(groups) == 0:
            return None
        return groups[0]


class PartitionTestCase(TestCase):
    """Base class for test cases that require partitions"""
    TEST_ID = 0
    TEST_NAME = "Mock Partition"
    TEST_DESCRIPTION = "for testing purposes"
    TEST_GROUPS = [Group(0, 'Group 1'), Group(1, 'Group 2')]
    TEST_SCHEME_NAME = "mock"

    def setUp(self):
        # Set up two user partition schemes: mock and random
        extensions = [
            Extension(
                self.TEST_SCHEME_NAME, USER_PARTITION_SCHEME_NAMESPACE,
                MockUserPartitionScheme(self.TEST_SCHEME_NAME), None
            ),
            Extension(
                "random", USER_PARTITION_SCHEME_NAMESPACE, MockUserPartitionScheme("random"), None
            ),
        ]
        UserPartition.scheme_extensions = ExtensionManager.make_test_instance(
            extensions, namespace=USER_PARTITION_SCHEME_NAMESPACE
        )

        # Create a test partition
        self.user_partition = UserPartition(
            self.TEST_ID,
            self.TEST_NAME,
            self.TEST_DESCRIPTION,
            self.TEST_GROUPS,
            extensions[0].plugin
        )


class TestUserPartition(PartitionTestCase):
    """Test constructing UserPartitions"""

    def test_construct(self):
        user_partition = UserPartition(
            self.TEST_ID, self.TEST_NAME, self.TEST_DESCRIPTION, self.TEST_GROUPS, MockUserPartitionScheme()
        )
        self.assertEqual(user_partition.id, self.TEST_ID)    # pylint: disable=no-member
        self.assertEqual(user_partition.name, self.TEST_NAME)
        self.assertEqual(user_partition.description, self.TEST_DESCRIPTION)    # pylint: disable=no-member
        self.assertEqual(user_partition.groups, self.TEST_GROUPS)    # pylint: disable=no-member
        self.assertEquals(user_partition.scheme.name, self.TEST_SCHEME_NAME)    # pylint: disable=no-member

    def test_string_id(self):
        user_partition = UserPartition(
            "70", self.TEST_NAME, self.TEST_DESCRIPTION, self.TEST_GROUPS
        )
        self.assertEqual(user_partition.id, 70)    # pylint: disable=no-member

    def test_to_json(self):
        jsonified = self.user_partition.to_json()
        act_jsonified = {
            "id": self.TEST_ID,
            "name": self.TEST_NAME,
            "description": self.TEST_DESCRIPTION,
            "groups": [group.to_json() for group in self.TEST_GROUPS],
            "version": self.user_partition.VERSION,
            "scheme": self.TEST_SCHEME_NAME
        }
        self.assertEqual(jsonified, act_jsonified)

    def test_from_json(self):
        jsonified = {
            "id": self.TEST_ID,
            "name": self.TEST_NAME,
            "description": self.TEST_DESCRIPTION,
            "groups": [group.to_json() for group in self.TEST_GROUPS],
            "version": UserPartition.VERSION,
            "scheme": "mock",
        }
        user_partition = UserPartition.from_json(jsonified)
        self.assertEqual(user_partition.id, self.TEST_ID)    # pylint: disable=no-member
        self.assertEqual(user_partition.name, self.TEST_NAME)    # pylint: disable=no-member
        self.assertEqual(user_partition.description, self.TEST_DESCRIPTION)    # pylint: disable=no-member
        for act_group in user_partition.groups:    # pylint: disable=no-member
            self.assertIn(act_group.id, [0, 1])
            exp_group = self.TEST_GROUPS[act_group.id]
            self.assertEqual(exp_group.id, act_group.id)
            self.assertEqual(exp_group.name, act_group.name)

    def test_version_upgrade(self):
        # Version 1 partitions did not have a scheme specified
        jsonified = {
            "id": self.TEST_ID,
            "name": self.TEST_NAME,
            "description": self.TEST_DESCRIPTION,
            "groups": [group.to_json() for group in self.TEST_GROUPS],
            "version": 1,
        }
        user_partition = UserPartition.from_json(jsonified)
        self.assertEqual(user_partition.scheme.name, "random")    # pylint: disable=no-member

    def test_from_json_broken(self):
        # Missing field
        jsonified = {
            "name": self.TEST_NAME,
            "description": self.TEST_DESCRIPTION,
            "groups": [group.to_json() for group in self.TEST_GROUPS],
            "version": UserPartition.VERSION,
            "scheme": self.TEST_SCHEME_NAME,
        }
        with self.assertRaisesRegexp(TypeError, "missing value key 'id'"):
            UserPartition.from_json(jsonified)

        # Missing scheme
        jsonified = {
            'id': self.TEST_ID,
            "name": self.TEST_NAME,
            "description": self.TEST_DESCRIPTION,
            "groups": [group.to_json() for group in self.TEST_GROUPS],
            "version": UserPartition.VERSION,
        }
        with self.assertRaisesRegexp(TypeError, "missing value key 'scheme'"):
            UserPartition.from_json(jsonified)

        # Invalid scheme
        jsonified = {
            'id': self.TEST_ID,
            "name": self.TEST_NAME,
            "description": self.TEST_DESCRIPTION,
            "groups": [group.to_json() for group in self.TEST_GROUPS],
            "version": UserPartition.VERSION,
            "scheme": "no_such_scheme",
        }
        with self.assertRaisesRegexp(UserPartitionError, "Unrecognized scheme"):
            UserPartition.from_json(jsonified)

        # Wrong version (it's over 9000!)
        # Wrong version (it's over 9000!)
        jsonified = {
            'id': self.TEST_ID,
            "name": self.TEST_NAME,
            "description": self.TEST_DESCRIPTION,
            "groups": [group.to_json() for group in self.TEST_GROUPS],
            "version": 9001,
            "scheme": self.TEST_SCHEME_NAME,
        }
        with self.assertRaisesRegexp(TypeError, "has unexpected version"):
            UserPartition.from_json(jsonified)

        # Has extra key - should not be a problem
        jsonified = {
            'id': self.TEST_ID,
            "name": self.TEST_NAME,
            "description": self.TEST_DESCRIPTION,
            "groups": [group.to_json() for group in self.TEST_GROUPS],
            "version": UserPartition.VERSION,
            "scheme": "mock",
            "programmer": "Cale",
        }
        user_partition = UserPartition.from_json(jsonified)
        self.assertNotIn("programmer", user_partition.to_json())


class StaticPartitionService(PartitionService):
    """
    Mock PartitionService for testing.
    """
    def __init__(self, partitions, **kwargs):
        super(StaticPartitionService, self).__init__(**kwargs)
        self._partitions = partitions

    @property
    def course_partitions(self):
        return self._partitions


class TestPartitionService(PartitionTestCase):
    """
    Test getting a user's group out of a partition
    """

    def setUp(self):
        super(TestPartitionService, self).setUp()
        course = Mock(id=SlashSeparatedCourseKey('org_0', 'course_0', 'run_0'))
        self.partition_service = StaticPartitionService(
            [self.user_partition],
            user=Mock(username='ma', email='ma@edx.org', is_staff=False, is_active=True),
            course_id=course.id,
            track_function=Mock()
        )

    def test_get_user_group_id_for_partition(self):
        # assign the first group to be returned
        user_partition_id = self.user_partition.id    # pylint: disable=no-member
        groups = self.user_partition.groups    # pylint: disable=no-member
        self.user_partition.scheme.current_group = groups[0]    # pylint: disable=no-member

        # get a group assigned to the user
        group1_id = self.partition_service.get_user_group_id_for_partition(user_partition_id)
        self.assertEqual(group1_id, groups[0].id)    # pylint: disable=no-member

        # switch to the second group and verify that it is returned for the user
        self.user_partition.scheme.current_group = groups[1]    # pylint: disable=no-member
        group2_id = self.partition_service.get_user_group_id_for_partition(user_partition_id)
        self.assertEqual(group2_id, groups[1].id)    # pylint: disable=no-member

    def test_get_group(self):
        """
        Test that a partition group is assigned to a user.
        """
        groups = self.user_partition.groups    # pylint: disable=no-member

        # assign first group and verify that it is returned for the user
        self.user_partition.scheme.current_group = groups[0]    # pylint: disable=no-member
        group1 = self.partition_service.get_group(self.user_partition)
        self.assertEqual(group1, groups[0])    # pylint: disable=no-member

        # switch to the second group and verify that it is returned for the user
        self.user_partition.scheme.current_group = groups[1]    # pylint: disable=no-member
        group2 = self.partition_service.get_group(self.user_partition)
        self.assertEqual(group2, groups[1])    # pylint: disable=no-member
