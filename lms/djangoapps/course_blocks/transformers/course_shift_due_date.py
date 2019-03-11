"""
Load Override Data Transformer
"""
from openedx.core.djangoapps.content.block_structure.transformer import BlockStructureTransformer


# The list of fields are in support of Individual due dates and could be expanded for other use cases.
REQUESTED_FIELDS = [
    'due'
]


class CourseShiftDueDateTransformer(BlockStructureTransformer):
    """
    A transformer that load override data in xblock.
    """
    WRITE_VERSION = 1
    READ_VERSION = 1

    @classmethod
    def name(cls):
        """
        Unique identifier for the transformer's class;
        same identifier used in setup.py.
        """
        return "course_shift_due_date"

    @classmethod
    def collect(cls, block_structure):
        """
        Collects any information that's necessary to execute this transformer's transform method.
        """
        # collect basic xblock fields
        block_structure.request_xblock_fields(*REQUESTED_FIELDS)

    def transform(self, usage_info, block_structure):
        """
        loads override data into blocks
        """
        location_list = block_structure.topological_traversal()
        for location_id in location_list:
            due_date = block_structure.get_xblock_field(location_id, 'due')
            if due_date:
                new_due_date = usage_info.course_shift_date(due_date)
                if new_due_date:
                    block_structure.override_xblock_field(
                        location_id,
                        'due',
                        new_due_date
                    )
