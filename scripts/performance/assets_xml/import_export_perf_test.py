
import os
import os.path
from tempfile import mkdtemp
from generate_asset_xml import make_asset_xml

from code_block_timer import CodeBlockTimer
from xmodule.assetstore import AssetMetadata
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore.xml_exporter import export_to_xml
from xmodule.modulestore.tests.test_cross_modulestore_import_export import (
    MIXED_MODULESTORE_BOTH_SETUP,
    MODULESTORE_SETUPS,
    SHORT_NAME_MAP,
    TEST_DATA_DIR,
    MongoContentstoreBuilder,
    XmlModulestoreBuilder,
    MixedModulestoreBuilder
)

# Number of assets saved in the modulestore per test run.
ASSET_AMOUNT_PER_TEST = (1, 10, 100, 1000, 10000)

# Use only this course in asset metadata performance testing.
COURSE_NAME = 'manual-testing-complete'

# Path where generated asset file is saved.
ASSET_FILE_LOCATION = os.path.join(
    os.environ['HOME'],
    "edx-platform",
    TEST_DATA_DIR,
    COURSE_NAME,
    AssetMetadata.EXPORTED_ASSET_DIR,
    AssetMetadata.EXPORTED_ASSET_FILENAME
)


class CrossStoreXMLRoundtrip(object):
    """
    This class exists to time XML import and export between different modulestore
    classes with different amount of asset metadata.
    """

    def __init__(self, source_ms, dest_ms, course, num_assets):
        #super(CrossStoreXMLRoundtrip, self).setUp()
        self.export_dir = mkdtemp()
        self.source_ms = source_ms
        self.dest_ms = dest_ms
        self.course = course
        self.num_assets = num_assets
        #self.addCleanup(rmtree, self.export_dir, ignore_errors=True)

    def runTest(self):
        self.generate_asset_xml()
        self.generate_timing()

    def generate_asset_xml(self):
        """
        Generate the test asset XML and put it in the test course to be imported.
        """
        make_asset_xml(self.num_assets, ASSET_FILE_LOCATION)

    def generate_timing(self):
        desc = "XMLRoundTrip:{}->{}:{}".format(
            SHORT_NAME_MAP[self.source_ms],
            SHORT_NAME_MAP[self.dest_ms],
            self.num_assets
        )
        with CodeBlockTimer(desc) as timer:
            # Construct the contentstore for storing the first import
            with MongoContentstoreBuilder().build() as source_content:
                # Construct the modulestore for storing the first import (using the previously created contentstore)
                with self.source_ms.build(source_content) as source_store:
                    # Construct the contentstore for storing the second import
                    with MongoContentstoreBuilder().build() as dest_content:
                        # Construct the modulestore for storing the second import (using the second contentstore)
                        with self.dest_ms.build(dest_content) as dest_store:
                            source_course_key = source_store.make_course_key('a', 'course', 'course')
                            dest_course_key = dest_store.make_course_key('a', 'course', 'course')

                            with CodeBlockTimer("initial_import"):
                                import_from_xml(
                                    source_store,
                                    'test_user',
                                    os.path.join(os.environ['HOME'], "edx-platform", TEST_DATA_DIR),
                                    course_dirs=[self.course],
                                    static_content_store=source_content,
                                    target_course_id=source_course_key,
                                    create_course_if_not_present=True,
                                    raise_on_failure=True,
                                )

                            with CodeBlockTimer("export"):
                                export_to_xml(
                                    source_store,
                                    source_content,
                                    source_course_key,
                                    self.export_dir,
                                    'exported_source_course',
                                )

                            with CodeBlockTimer("second_import"):
                                import_from_xml(
                                    dest_store,
                                    'test_user',
                                    self.export_dir,
                                    course_dirs=['exported_source_course'],
                                    static_content_store=dest_content,
                                    target_course_id=dest_course_key,
                                    create_course_if_not_present=True,
                                    raise_on_failure=True,
                                )


# Run the tests.
for source_ms in MODULESTORE_SETUPS:
    for dest_ms in MODULESTORE_SETUPS:
        for amount in ASSET_AMOUNT_PER_TEST:
            print "=========================="
            print "Testing with {}->{} with {} asset metadata items...".format(
                SHORT_NAME_MAP[source_ms],
                SHORT_NAME_MAP[dest_ms],
                amount
            )
            print "=========================="
            tester = CrossStoreXMLRoundtrip(MODULESTORE_SETUPS[0], MODULESTORE_SETUPS[0], COURSE_NAME, amount)
            tester.runTest()

# Query the test data and generate reports.

