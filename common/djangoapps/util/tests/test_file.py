# -*- coding: utf-8 -*-
"""
Tests for file.py
"""
from cStringIO import StringIO
import ddt

from django.test import TestCase
from datetime import datetime
from django.utils.timezone import UTC
from mock import patch, Mock
from django.http import HttpRequest
from django.core.files.uploadedfile import SimpleUploadedFile
import util.file
from util.file import course_and_time_based_filename_generator, store_uploaded_file, FileValidationException, UniversalNewlineIterator
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from django.core import exceptions
import os


class FilenameGeneratorTestCase(TestCase):
    """
    Tests for course_and_time_based_filename_generator
    """
    NOW = datetime.strptime('1974-06-22T01:02:03', '%Y-%m-%dT%H:%M:%S').replace(tzinfo=UTC())

    def setUp(self):
        datetime_patcher = patch.object(
            util.file, 'datetime',
            Mock(wraps=datetime)
        )
        mocked_datetime = datetime_patcher.start()
        mocked_datetime.now.return_value = self.NOW
        self.addCleanup(datetime_patcher.stop)

    def test_filename_generator(self):
        """
        Tests that the generator creates names based on course_id, base name, and date.
        """
        self.assertEqual(
            "course_id_file_1974-06-22-010203",
            course_and_time_based_filename_generator("course/id", "file")
        )
        self.assertEqual(
            "__1974-06-22-010203",
            course_and_time_based_filename_generator("", "")
        )
        self.assertEqual(
            u"course_base_name_ø_1974-06-22-010203",
            course_and_time_based_filename_generator(u"course", u" base` name ø ")
        )
        course_key = SlashSeparatedCourseKey.from_string("foo/bar/123")
        self.assertEqual(
            "foo_bar_123_cohorted_1974-06-22-010203",
            course_and_time_based_filename_generator(course_key, "cohorted")
        )


class StoreUploadedFileTestCase(TestCase):
    """
    Tests for store_uploaded_file.
    """

    def setUp(self):
        self.request = Mock(spec=HttpRequest)
        self.file_content = "test file content"
        self.request.FILES = {"uploaded_file": SimpleUploadedFile("tempfile.csv", self.file_content)}
        self.stored_file_name = None
        self.file_storage = None

    def tearDown(self):
        if self.file_storage and self.stored_file_name:
            self.file_storage.delete(self.stored_file_name)

    def verify_exception(self, expected_message, error):
        """
        Helper method to verify exception text.
        """
        self.assertEqual(expected_message, error.exception.message)

    def test_error_conditions(self):
        """
        Verifies that exceptions are thrown in the expected cases.
        """
        with self.assertRaises(ValueError) as error:
            store_uploaded_file(self.request, "wrong_key", [".txt", ".csv"], "stored_file")
        self.verify_exception("No file uploaded with key 'wrong_key'.", error)

        with self.assertRaises(exceptions.PermissionDenied) as error:
            store_uploaded_file(self.request, "uploaded_file", [], "stored_file")
        self.verify_exception("The file must end with one of the following extensions: ''.", error)

        with self.assertRaises(exceptions.PermissionDenied) as error:
            store_uploaded_file(self.request, "uploaded_file", [".bar"], "stored_file")
        self.verify_exception("The file must end with the extension '.bar'.", error)

        with self.assertRaises(exceptions.PermissionDenied) as error:
            store_uploaded_file(self.request, "uploaded_file", [".xxx", ".bar"], "stored_file")
        self.verify_exception("The file must end with one of the following extensions: '.xxx', '.bar'.", error)

        with self.assertRaises(exceptions.PermissionDenied) as error:
            store_uploaded_file(self.request, "uploaded_file", [".csv"], "stored_file", max_file_size=2)
        self.verify_exception("Maximum upload file size is 2 bytes.", error)

    def test_validator(self):
        """
        Verify that a validator function can throw an exception.
        """
        validator_data = {}

        def verify_file_presence(should_exist):
            """ Verify whether or not the stored file, passed to the validator, exists. """
            self.assertEqual(should_exist, validator_data["storage"].exists(validator_data["filename"]))

        def store_file_data(storage, filename):
            """ Stores file validator data for testing after validation is complete. """
            validator_data["storage"] = storage
            validator_data["filename"] = filename
            verify_file_presence(True)

        def exception_validator(storage, filename):
            """ Validation test function that throws an exception """
            self.assertEqual("error_file.csv", os.path.basename(filename))
            with storage.open(filename, 'rU') as f:
                self.assertEqual(self.file_content, f.read())
            store_file_data(storage, filename)
            raise FileValidationException("validation failed")

        def success_validator(storage, filename):
            """ Validation test function that is a no-op """
            self.assertEqual("success_file.csv", os.path.basename(filename))
            store_file_data(storage, filename)

        with self.assertRaises(FileValidationException) as error:
            store_uploaded_file(self.request, "uploaded_file", [".csv"], "error_file", validator=exception_validator)
        self.verify_exception("validation failed", error)
        # Verify the file was deleted.
        verify_file_presence(False)

        store_uploaded_file(self.request, "uploaded_file", [".csv"], "success_file", validator=success_validator)
        # Verify the file still exists
        verify_file_presence(True)

    def test_file_upload_lower_case_extension(self):
        """
        Tests uploading a file with lower case extension. Verifies that the stored file contents are correct.
        """
        self.file_storage, self.stored_file_name = store_uploaded_file(
            self.request, "uploaded_file", [".csv"], "stored_file"
        )
        self._verify_successful_upload()

    def test_file_upload_upper_case_extension(self):
        """
        Tests uploading a file with upper case extension. Verifies that the stored file contents are correct.
        """
        self.request.FILES = {"uploaded_file": SimpleUploadedFile("tempfile.CSV", self.file_content)}
        self.file_storage, self.stored_file_name = store_uploaded_file(
            self.request, "uploaded_file", [".gif", ".csv"], "second_stored_file"
        )
        self._verify_successful_upload()

    def _verify_successful_upload(self):
        """ Helper method that checks that the stored version of the uploaded file has the correct content """
        self.assertTrue(self.file_storage.exists(self.stored_file_name))
        with self.file_storage.open(self.stored_file_name, 'r') as f:
            self.assertEqual(self.file_content, f.read())


@ddt.ddt
class TestUniversalNewlineIterator(TestCase):
    """
    Tests for the UniversalNewlineIterator class.
    """
    @ddt.data(1, 2, 999)
    def test_line_feeds(self, buffer_size):
        self.assertEqual(
            [thing for thing in UniversalNewlineIterator(StringIO('foo\nbar\n'), buffer_size=buffer_size)],
            ['foo\n', 'bar\n']
        )

    @ddt.data(1, 2, 999)
    def test_carriage_returns(self, buffer_size):
        self.assertEqual(
            [thing for thing in UniversalNewlineIterator(StringIO('foo\rbar\r'), buffer_size=buffer_size)],
            ['foo\n', 'bar\n']
        )

    @ddt.data(1, 2, 999)
    def test_carriage_returns_and_line_feeds(self, buffer_size):
        self.assertEqual(
            [thing for thing in UniversalNewlineIterator(StringIO('foo\r\nbar\r\n'), buffer_size=buffer_size)],
            ['foo\n', 'bar\n']
        )

    @ddt.data(1, 2, 999)
    def test_no_trailing_newline(self, buffer_size):
        self.assertEqual(
            [thing for thing in UniversalNewlineIterator(StringIO('foo\nbar'), buffer_size=buffer_size)],
            ['foo\n', 'bar']
        )

    @ddt.data(1, 2, 999)
    def test_only_one_line(self, buffer_size):
        self.assertEqual(
            [thing for thing in UniversalNewlineIterator(StringIO('foo\n'), buffer_size=buffer_size)],
            ['foo\n']
        )

    @ddt.data(1, 2, 999)
    def test_only_one_line_no_trailing_newline(self, buffer_size):
        self.assertEqual(
            [thing for thing in UniversalNewlineIterator(StringIO('foo'), buffer_size=buffer_size)],
            ['foo']
        )

    @ddt.data(1, 2, 999)
    def test_empty_file(self, buffer_size):
        self.assertEqual(
            [thing for thing in UniversalNewlineIterator(StringIO(), buffer_size=buffer_size)],
            []
        )
